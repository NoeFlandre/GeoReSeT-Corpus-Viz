"""Offline build: dataset slice -> sentences, polygons and int8 vectors for the app."""

from collections.abc import Callable
from pathlib import Path

import duckdb
import numpy as np

from georeset_viz import config
from georeset_viz.build.extract import extract
from georeset_viz.build.geometry import simplified_geojson
from georeset_viz.index import quantize
from georeset_viz.store import write_json

BatchEncoder = Callable[[list[str], str], np.ndarray]
HF_ROOT = f"hf://datasets/{config.DATASET}"


def _polygon_record(name, tag, lat, lon, area, wkb) -> dict:
    return {
        "name": name,
        "tag": tag,
        "lat": lat,
        "lon": lon,
        "area": area,
        "geometry": simplified_geojson(wkb),
    }


def build(
    out_dir: Path,
    con: duckdb.DuckDBPyConnection,
    encode: BatchEncoder,
    sentences_glob: str,
    polygons_glob: str,
) -> None:
    sentences, polygons = extract(con, sentences_glob, polygons_glob)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / config.SENTENCES_FILE, sentences)
    write_json(
        out_dir / config.POLYGONS_FILE, {pid: _polygon_record(*rest) for pid, *rest in polygons}
    )
    np.save(out_dir / config.VECTORS_FILE, quantize(encode(sentences["text"], "passage")))


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
