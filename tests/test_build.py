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


def test_build_writes_app_data(parquet, tmp_path):
    def encode(texts, prefix):
        assert prefix == "passage"
        return np.tile([0.6, 0.8], (len(texts), 1))

    build(tmp_path, duckdb.connect(), encode, *parquet)
    sentences = read_json(tmp_path / config.SENTENCES_FILE)
    polygons = read_json(tmp_path / config.POLYGONS_FILE)
    vectors = np.load(tmp_path / config.VECTORS_FILE)
    assert len(sentences["text"]) == 3 == len(vectors)
    assert vectors.dtype == np.int8
    assert set(polygons) == {"way/1", "way/2"}
    assert polygons["way/1"]["tag"] == "natural=water"
