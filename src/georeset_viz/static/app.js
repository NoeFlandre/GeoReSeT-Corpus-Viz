"use strict";

const EXAMPLES = [
  "tourbière drainée", "vignes en terrasses", "glacier en recul", "ancienne carrière",
  "zone inondable", "forêt de résineux", "friche industrielle", "alpage pâturé",
  "lac de barrage", "vergers et noyers",
];
const RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"];
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

// Map ------------------------------------------------------------------------
const map = L.map("map", { preferCanvas: true, zoomControl: true }).setView([45.55, 5.6], 8);
const photo = L.tileLayer(IGN("ORTHOIMAGERY.ORTHOPHOTOS", "image/jpeg"), {
  maxZoom: 19, attribution: ATTRIBUTION,
}).addTo(map);
const plan = L.tileLayer(IGN("GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2", "image/png"), {
  maxZoom: 19, attribution: ATTRIBUTION,
});
L.control.layers({ "Orthophoto IGN": photo, "Plan IGN": plan }).addTo(map);

const hexLayer = L.geoJSON(null, { style: hexStyle, onEachFeature: bindHex }).addTo(map);
const markerLayer = L.layerGroup().addTo(map);
const outlineLayer = L.layerGroup().addTo(map);
let maxCount = 1;

const legend = L.control({ position: "bottomleft" });
legend.onAdd = () =>
  el("div", { className: "legend", hidden: true, id: "legend" }, [
    "Lieux trouvés par hexagone",
    el("div", { className: "ramp" }, RAMP.map((c) => el("i", { style: `background:${c}` }))),
    el("div", { className: "ends" }, [el("span", { textContent: "1" }), el("span", { id: "legend-max" })]),
  ]);
legend.addTo(map);

function hexStyle(feature) {
  const t = Math.log1p(feature.properties.count) / Math.log1p(maxCount);
  const color = RAMP[Math.min(RAMP.length - 1, Math.round(t * (RAMP.length - 1)))];
  return { fillColor: color, fillOpacity: 0.7, color: "#fff", weight: 0.6 };
}

function bindHex(feature, layer) {
  const { count, score } = feature.properties;
  layer.bindTooltip(`${count} lieu${count > 1 ? "x" : ""} · meilleur score ${score.toFixed(2)}`, { sticky: true });
  layer.on("click", () => map.fitBounds(layer.getBounds(), { maxZoom: 13 }));
}

// Data -----------------------------------------------------------------------
const cache = new Map();
let pendingSearch;

async function getJSON(url, signal) {
  if (cache.has(url)) return cache.get(url);
  const response = await fetch(url, { signal });
  if (!response.ok) throw new Error(response.statusText);
  const body = await response.json();
  cache.set(url, body);
  return body;
}

async function search(query) {
  query = query.trim();
  if (!query) return;
  $("q").value = query;
  $("status").textContent = "Recherche…";
  try {
    pendingSearch?.abort();
    pendingSearch = new AbortController();
    render(await getJSON(`/api/search?q=${encodeURIComponent(query)}`, pendingSearch.signal));
  } catch (error) {
    if (error.name !== "AbortError") $("status").textContent = `Erreur : ${error.message}`;
  }
}

// Rendering ------------------------------------------------------------------
function render({ results, hexes, tags }) {
  maxCount = Math.max(1, ...hexes.features.map((f) => f.properties.count));
  const places = hexes.features.reduce((n, f) => n + f.properties.count, 0);
  hexLayer.clearLayers().addData(hexes);
  outlineLayer.clearLayers();
  $("legend").hidden = false;
  $("legend-max").textContent = maxCount;
  $("status").textContent = `${places} lieux décrits par les phrases les plus proches.`;
  renderTags(tags);
  renderResults(results);
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
      radius: 6, color: "#fff", weight: 2, fillColor: "#eb6834", fillOpacity: 1,
    }).addTo(markerLayer);
    const open = () => focus(r, item);
    marker.on("click", open);
    item.addEventListener("click", open);
    return item;
  });
  $("results").replaceChildren(...items);
  $("results-section").hidden = results.length === 0;
}

function osmLink(polygon) {
  return `https://www.openstreetmap.org/${polygon}`;
}

function popup(r) {
  return el("div", {}, [
    el("strong", { textContent: r.name ?? "Sans nom" }),
    el("div", { className: "meta", textContent: r.tag ?? "" }),
    el("q", { textContent: r.text }),
    el("div", {}, [
      el("a", { href: r.url, target: "_blank", rel: "noopener", textContent: `Source (${r.source})` }),
      " · ",
      el("a", { href: osmLink(r.polygon), target: "_blank", rel: "noopener", textContent: "OSM" }),
    ]),
  ]);
}

async function focus(r, item) {
  document.querySelectorAll("#results li.active").forEach((li) => li.classList.remove("active"));
  item.classList.add("active");
  outlineLayer.clearLayers();
  const point = L.latLng(r.lat, r.lon);
  try {
    const shape = L.geoJSON(await getJSON(`/api/polygon?id=${encodeURIComponent(r.polygon)}`), {
      style: { color: "#ffd400", weight: 3, fill: false },
    }).addTo(outlineLayer);
    map.fitBounds(shape.getBounds(), { maxZoom: 18, padding: [40, 40] });
  } catch {
    map.setView(point, 16);
  }
  L.popup({ maxWidth: 320 }).setLatLng(point).setContent(popup(r)).openOn(map);
}

// Wiring ---------------------------------------------------------------------
$("examples").replaceChildren(
  ...EXAMPLES.map((q) => el("button", { type: "button", textContent: q, onclick: () => search(q) })),
);
$("search").addEventListener("submit", (event) => {
  event.preventDefault();
  search($("q").value);
});
