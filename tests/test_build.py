import gzip
import json

import duckdb
import numpy as np
import pytest
import shapely

from georeset_viz import config
from georeset_viz.build.extract import extract
from georeset_viz.build.geometry import simplified_geojson
from georeset_viz.build.pipeline import build
from georeset_viz.store import read_json

LONG = "x" * 50


def _sentences(path):
    rows = [
        # id, text, landuse, region, polygon
        ("a", f"lac {LONG}", True, "rhone-alpes", "way/1"),
        ("b", f"lac {LONG}", True, "rhone-alpes", "way/2"),  # duplicate text
        ("c", f"bois {LONG}", True, "rhone-alpes", "way/2"),
        ("d", f"menu {LONG}", False, "rhone-alpes", "way/2"),  # not land use
        ("e", "court", True, "rhone-alpes", "way/2"),  # too short
        ("f", f"mer {LONG}", True, "bretagne", "way/3"),  # other region
        ("g", f"pré {LONG}", True, "rhone-alpes", "way/1"),
    ]
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE t (id VARCHAR, text VARCHAR, landuse BOOLEAN, region VARCHAR, "
        "polygon_ids VARCHAR[], language VARCHAR, source VARCHAR, url VARCHAR)"
    )
    for id_, text, landuse, region, polygon in rows:
        con.execute(
            "INSERT INTO t VALUES (?, ?, ?, ?, [?], 'fra_Latn', 'wikipedia', 'u')",
            [id_, text, landuse, region, polygon],
        )
    con.execute(f"COPY t TO '{path}'")


def _polygons(path):
    square = shapely.box(5.0, 45.0, 5.001, 45.001).wkb
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE p (polygon_id VARCHAR, name VARCHAR, osm_tag VARCHAR, region VARCHAR, "
        "lat DOUBLE, lon DOUBLE, area_m2 DOUBLE, geometry BLOB)"
    )
    for pid in ["way/1", "way/2", "way/9"]:
        con.execute(
            "INSERT INTO p VALUES (?, 'n', 'natural=water', 'rhone-alpes', 45.0, 5.0, 10.0, ?)",
            [pid, square],
        )
    con.execute(f"COPY p TO '{path}'")


@pytest.fixture
def parquet(tmp_path):
    _sentences(tmp_path / "s.parquet")
    _polygons(tmp_path / "p.parquet")
    return str(tmp_path / "s.parquet"), str(tmp_path / "p.parquet")


def test_extract_filters_dedupes_and_caps(parquet, monkeypatch):
    monkeypatch.setattr(config, "MAX_SENTENCES_PER_POLYGON", 1)
    sentences, polygons = extract(duckdb.connect(), *parquet)
    assert sentences["text"] == [f"lac {LONG}", f"bois {LONG}"]
    assert sentences["polygon"] == ["way/1", "way/2"]
    assert [p[0] for p in polygons] == ["way/1", "way/2"]


def test_simplified_geojson_drops_redundant_vertices():
    wkb = shapely.Polygon([(5, 45), (5.5, 45), (6, 45), (6, 46), (5, 46)]).wkb
    geojson = simplified_geojson(wkb)
    assert geojson["type"] == "Polygon"
    assert len(geojson["coordinates"][0]) == 5


def fake_encode(texts, prefix):
    return np.tile([0.6, 0.8] if prefix == "passage" else [1.0, 0.0], (len(texts), 1))


@pytest.fixture
def site(parquet, tmp_path):
    out = tmp_path / "site"
    build(out, duckdb.connect(), fake_encode, *parquet)
    return out


def test_build_writes_meta_pointing_to_every_file(site):
    meta = json.loads((site / "meta.json").read_text())
    assert meta["count"] == 3 and meta["dims"] == 2
    assert meta["mapSentences"] == config.BROWSER_SETTINGS["mapSentences"]
    assert all((site / name).exists() for name in meta["files"].values())


def test_build_links_sentences_to_polygons_and_cells(site):
    meta = json.loads((site / "meta.json").read_text())
    sentences = read_json(site / meta["files"]["sentences"])
    polygons = read_json(site / meta["files"]["polygons"])
    cells = read_json(site / meta["files"]["cells"])
    geometries = read_json(site / meta["files"]["geometries"])
    assert polygons["id"] == ["way/1", "way/2"] and polygons["tag"][0] == "natural=water"
    assert [polygons["id"][i] for i in sentences["polygon"]] == ["way/1", "way/1", "way/2"]
    assert polygons["cell"] == [0, 0] and len(cells) == 1 and len(cells[0]) == 7
    assert [g["type"] for g in geometries] == ["Polygon", "Polygon"]


def test_build_writes_int8_vectors_and_example_queries(site):
    meta = json.loads((site / "meta.json").read_text())
    vectors = np.frombuffer(
        gzip.decompress((site / meta["files"]["vectors"]).read_bytes()), np.int8
    )
    assert vectors.tolist() == [76, 102] * 3
    examples = json.loads((site / meta["files"]["examples"]).read_text())
    assert examples["queries"] == config.EXAMPLES
    assert examples["vectors"][0] == [1.0, 0.0]
