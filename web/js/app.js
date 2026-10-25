import { readInt8, readJSON } from "./data.js";
import { embedQuery, loadModel } from "./embed.js";
import { bestPerPolygon, countBy, hexCounts, scores, topK } from "./search.js";

const RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"];
const HEX_MAX_ZOOM = 11; // closer in, hexes would hide the imagery the text is compared with
const IGN = (layer, format) =>
  "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&STYLE=normal" +
  `&TILEMATRIXSET=PM&LAYER=${layer}&FORMAT=${format}&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}`;
const ATTRIBUTION =
  '© <a href="https://www.ign.fr">IGN</a> · © <a href="https://www.openstreetmap.org/copyright">OSM</a>';

const $ = (id) => document.getElementById(id);
const el = (tag, props = {}, children = []) => {
  const node = Object.assign(document.createElement(tag), props);
  node.append(...children);
  return node;
};
const status = (text) => ($("status").textContent = text);

// Map ------------------------------------------------------------------------
const map = L.map("map", { preferCanvas: true }).setView([45.55, 5.6], 8);
const photo = L.tileLayer(IGN("ORTHOIMAGERY.ORTHOPHOTOS", "image/jpeg"), {
  maxZoom: 19,
  attribution: ATTRIBUTION,
}).addTo(map);
const plan = L.tileLayer(IGN("GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2", "image/png"), {
  maxZoom: 19,
  attribution: ATTRIBUTION,
});
L.control.layers({ "Orthophoto IGN": photo, "Plan IGN": plan }).addTo(map);

let maxCount = 1;
const hexLayer = L.geoJSON(null, { style: hexStyle, onEachFeature: bindHex }).addTo(map);
const markerLayer = L.layerGroup().addTo(map);
const outlineLayer = L.layerGroup().addTo(map);
map.on("zoomend", () => {
  const show = map.getZoom() <= HEX_MAX_ZOOM;
  if (show !== map.hasLayer(hexLayer)) show ? hexLayer.addTo(map) : hexLayer.remove();
});

const legend = L.control({ position: "bottomleft" });
legend.onAdd = () =>
  el("div", { className: "legend", hidden: true, id: "legend" }, [
    "Lieux trouvés par hexagone",
    el(
      "div",
      { className: "ramp" },
      RAMP.map((c) => el("i", { style: `background:${c}` })),
    ),
    el("div", { className: "ends" }, [
      el("span", { textContent: "1" }),
      el("span", { id: "legend-max" }),
    ]),
  ]);
legend.addTo(map);

function hexStyle(feature) {
  const t = Math.log1p(feature.properties.count) / Math.log1p(maxCount);
  const color = RAMP[Math.round(t * (RAMP.length - 1))];
  return { fillColor: color, fillOpacity: 0.7, color: "#fff", weight: 0.6 };
}

function bindHex(feature, layer) {
  const { count, score } = feature.properties;
  layer.bindTooltip(`${count} lieu${count > 1 ? "x" : ""} · meilleur score ${score.toFixed(2)}`, {
    sticky: true,
  });
  layer.on("click", () => map.fitBounds(layer.getBounds(), { maxZoom: 13 }));
}

// Data -----------------------------------------------------------------------
const fetchOk = async (url) => {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url} : ${response.status}`);
  return response;
};
const file = (name) => `data/${meta.files[name]}`;
const loadJSON = async (name) => readJSON(await fetchOk(file(name)));

const meta = await readJSON(await fetchOk("data/meta.json"));
const [sentences, polygons, cells, examples] = await Promise.all(
  ["sentences", "polygons", "cells", "examples"].map(loadJSON),
);
let geometries; // outlines load on the first click
let vectors; // vectors and model load only for typed queries; examples come pre-ranked
const loadVectors = () => (vectors ??= fetchOk(file("vectors")).then(readInt8));
const cache = new Map();

async function rank(query) {
  const example = examples.queries.indexOf(query);
  if (example >= 0) return { rows: examples.rows[example], scores: examples.scores[example] };
  status("Chargement du modèle et des vecteurs (une seule fois, environ 150 Mo)…");
  const [vector, all] = await Promise.all([embedQuery(meta.model, query), loadVectors()]);
  return topK(scores(all, meta.dims, vector), meta.mapSentences);
}

function hit({ row, score }) {
  const p = sentences.polygon[row];
  return {
    polygon: polygons.id[p],
    name: polygons.name[p],
    tag: polygons.tag[p],
    lat: polygons.lat[p],
    lon: polygons.lon[p],
    cell: polygons.cell[p],
    index: p,
    score,
    text: sentences.text[row],
    source: sentences.source[row],
    url: sentences.url[row],
  };
}

function hexFeatures(hits) {
  const features = [...hexCounts(hits)].map(([cell, properties]) => ({
    type: "Feature",
    properties,
    geometry: { type: "Polygon", coordinates: [cells[cell]] },
  }));
  return { type: "FeatureCollection", features };
}

async function run(query) {
  const { rows, scores: rowScores } = await rank(query);
  const hits = bestPerPolygon(rows, rowScores, sentences.polygon).map(hit);
  return {
    hits,
    hexes: hexFeatures(hits),
    tags: countBy(
      hits.map((h) => h.tag),
      meta.topTags,
    ),
  };
}

async function search(query) {
  query = query.trim();
  if (!query) return;
  $("q").value = query;
  status("Recherche…");
  try {
    if (!cache.has(query)) cache.set(query, await run(query));
    render(cache.get(query));
  } catch (error) {
    status(`Erreur : ${error.message}`);
  }
}

// Rendering ------------------------------------------------------------------
function render({ hits, hexes, tags }) {
  maxCount = Math.max(1, ...hexes.features.map((f) => f.properties.count));
  hexLayer.clearLayers().addData(hexes);
  outlineLayer.clearLayers();
  $("legend").hidden = false;
  $("legend-max").textContent = maxCount;
  status(`${hits.length} lieux décrits par les ${meta.mapSentences} phrases les plus proches.`);
  renderTags(tags);
  renderResults(hits.slice(0, meta.listSize));
}

function renderTags(tags) {
  const top = Math.max(1, ...tags.map(([, n]) => n));
  $("tags").replaceChildren(
    ...tags.map(([tag, n]) =>
      el("div", { className: "tag", title: `${tag} : ${n} lieux` }, [
        el("code", { textContent: tag ?? "—" }),
        el("div", { className: "bar", style: `width:${(100 * n) / top}%` }),
        el("span", { textContent: n }),
      ]),
    ),
  );
  $("tags-section").hidden = tags.length === 0;
}

function renderResults(results) {
  markerLayer.clearLayers();
  const items = results.map((r, i) => {
    const item = el("li", {}, [
      el("div", { className: "head" }, [
        el("span", { textContent: `${i + 1}. ${r.name ?? "Sans nom"}` }),
        el("span", { className: "score", textContent: r.score.toFixed(2) }),
      ]),
      el("div", { className: "meta", textContent: `${r.tag ?? "—"} · ${r.source}` }),
      el("q", { textContent: r.text }),
    ]);
    const marker = L.circleMarker([r.lat, r.lon], {
      radius: 6,
      color: "#fff",
      weight: 2,
      fillColor: "#eb6834",
      fillOpacity: 1,
    }).addTo(markerLayer);
    const open = () => focus(r, item);
    marker.on("click", open);
    item.addEventListener("click", open);
    return item;
  });
  $("results").replaceChildren(...items);
  $("results-section").hidden = results.length === 0;
}

function popup(r) {
  const link = (href, textContent) =>
    el("a", { href, target: "_blank", rel: "noopener", textContent });
  return el("div", {}, [
    el("strong", { textContent: r.name ?? "Sans nom" }),
    el("div", { className: "meta", textContent: r.tag ?? "" }),
    el("q", { textContent: r.text }),
    el("div", {}, [
      link(r.url, `Source (${r.source})`),
      " · ",
      link(`https://www.openstreetmap.org/${r.polygon}`, "OSM"),
    ]),
  ]);
}

async function focus(r, item) {
  document.querySelectorAll("#results li.active").forEach((li) => li.classList.remove("active"));
  item.classList.add("active");
  outlineLayer.clearLayers();
  const point = L.latLng(r.lat, r.lon);
  L.popup({ maxWidth: 320 }).setLatLng(point).setContent(popup(r)).openOn(map);
  geometries ??= loadJSON("geometries");
  const shape = L.geoJSON((await geometries)[r.index], {
    style: { color: "#ffd400", weight: 3, fill: false },
  }).addTo(outlineLayer);
  map.fitBounds(shape.getBounds(), { maxZoom: 18, padding: [40, 40] });
}

// Wiring ---------------------------------------------------------------------
$("examples").replaceChildren(
  ...examples.queries.map((q) =>
    el("button", { type: "button", textContent: q, onclick: () => search(q) }),
  ),
);
$("search").addEventListener("submit", (event) => {
  event.preventDefault();
  search($("q").value);
});
$("q").addEventListener(
  "focus",
  () => Promise.all([loadModel(meta.model), loadVectors()]).catch(() => {}),
  {
    once: true,
  },
);
$("search-button").disabled = false;
status(
  `${meta.count.toLocaleString("fr")} phrases. Choisissez un exemple ou tapez une description.`,
);
