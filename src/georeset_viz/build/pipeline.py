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
from georeset_viz.vectors import quantize, top_rows, write_vectors

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


def _index(values: list[str]) -> tuple[list[str], list[int]]:
    """Distinct values in first-seen order, and the position of each value among them."""
    distinct = list(dict.fromkeys(values))
    position = dict(zip(distinct, range(len(distinct)), strict=True))
    return distinct, list(map(position.__getitem__, values))


def _write_polygons(out_dir: Path, rows: list[tuple]) -> dict[str, int]:
    ids, names, tags, lats, lons, wkbs = map(list, zip(*rows, strict=True))
    cells, cell_of = _index(list(map(hex_cell, lats, lons)))
    columns = {
        "id": ids,
        "name": names,
        "tag": tags,
        "lat": np.round(lats, 5).tolist(),
        "lon": np.round(lons, 5).tolist(),
        "cell": cell_of,
    }
    write_json(out_dir / FILES["polygons"], columns)
    write_json(out_dir / FILES["cells"], list(map(hex_ring, cells)))
    write_json(out_dir / FILES["geometries"], list(map(simplified_geojson, wkbs)))
    return dict(zip(ids, range(len(ids)), strict=True))


def _write_examples(out_dir: Path, encode: BatchEncoder, quantized: np.ndarray) -> None:
    """Pre-rank the example queries so the page answers them without vectors or model."""
    ranked = [
        top_rows(quantized, q, config.MAP_SENTENCES) for q in encode(config.EXAMPLES, "query")
    ]
    examples = {
        "queries": config.EXAMPLES,
        "rows": [rows for rows, _ in ranked],
        "scores": [scores for _, scores in ranked],
    }
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
    vectors = quantize(encode(sentences["text"], "passage"))
    write_vectors(out_dir / FILES["vectors"], vectors)
    _write_examples(out_dir, encode, vectors)
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
