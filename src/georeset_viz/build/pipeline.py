"""Offline build: dataset slice -> static files that the page searches in the browser."""

import json
from collections.abc import Callable
from pathlib import Path

import duckdb
import numpy as np

from georeset_viz import config
from georeset_viz.build.extract import extract
from georeset_viz.build.geometry import simplified_geojson
from georeset_viz.hexes import hex_cell, hex_ring
from georeset_viz.store import write_json
from georeset_viz.vectors import write_vectors

BatchEncoder = Callable[[list[str], str], np.ndarray]
HF_ROOT = f"hf://datasets/{config.DATASET}"
FILES = {
    "sentences": "sentences.json.gz",
    "polygons": "polygons.json.gz",
    "cells": "cells.json.gz",
    "geometries": "geometries.json.gz",
    "vectors": "vectors.i8.gz",
    "examples": "examples.json",
}


def _write_polygons(out_dir: Path, rows: list[tuple]) -> dict[str, int]:
    ids, names, tags, lats, lons, wkbs = (list(column) for column in zip(*rows, strict=True))
    cell_ids = [hex_cell(lat, lon) for lat, lon in zip(lats, lons, strict=True)]
    cells = list(dict.fromkeys(cell_ids))
    position = {cell: i for i, cell in enumerate(cells)}
    columns = {
        "id": ids,
        "name": names,
        "tag": tags,
        "lat": [round(v, 5) for v in lats],
        "lon": [round(v, 5) for v in lons],
        "cell": [position[c] for c in cell_ids],
    }
    write_json(out_dir / FILES["polygons"], columns)
    write_json(out_dir / FILES["cells"], [hex_ring(c) for c in cells])
    write_json(out_dir / FILES["geometries"], [simplified_geojson(w) for w in wkbs])
    return {pid: i for i, pid in enumerate(ids)}


def _write_examples(out_dir: Path, encode: BatchEncoder) -> None:
    vectors = np.round(encode(config.EXAMPLES, "query"), 5).tolist()
    examples = {"queries": config.EXAMPLES, "vectors": vectors}
    (out_dir / FILES["examples"]).write_text(json.dumps(examples, ensure_ascii=False))


def build(
    out_dir: Path,
    con: duckdb.DuckDBPyConnection,
    encode: BatchEncoder,
    sentences_glob: str,
    polygons_glob: str,
) -> None:
    sentences, polygons = extract(con, sentences_glob, polygons_glob)
    out_dir.mkdir(parents=True, exist_ok=True)
    position = _write_polygons(out_dir, polygons)
    sentences["polygon"] = [position[p] for p in sentences["polygon"]]
    write_json(out_dir / FILES["sentences"], sentences)
    vectors = encode(sentences["text"], "passage")
    write_vectors(out_dir / FILES["vectors"], vectors)
    _write_examples(out_dir, encode)
    meta = {"count": len(vectors), "dims": vectors.shape[1], "files": FILES}
    (out_dir / "meta.json").write_text(json.dumps(meta | config.BROWSER_SETTINGS))


def main() -> None:  # pragma: no cover - runs against the real dataset
    from georeset_viz.embedder import Embedder

    build(
        config.DATA_DIR,
        duckdb.connect(),
        Embedder.from_hub().encode,
        f"{HF_ROOT}/data/*/{config.LANGUAGE}/*.parquet",
        f"{HF_ROOT}/polygons/*.parquet",
    )


if __name__ == "__main__":  # pragma: no cover
    main()
