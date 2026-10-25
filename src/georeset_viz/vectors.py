"""int8 storage for unit vectors, read by the browser as a gzipped Int8Array."""

import gzip
from pathlib import Path

import numpy as np

SCALE = 127.0


def quantize(vectors: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(vectors * SCALE), -SCALE, SCALE).astype(np.int8)


def write_vectors(path: Path, quantized: np.ndarray) -> None:
    path.write_bytes(gzip.compress(quantized.tobytes(order="C"), compresslevel=9))


def top_rows(quantized: np.ndarray, query: np.ndarray, k: int) -> tuple[list[int], list[float]]:
    """Best rows for a query, scored exactly as web/js/search.js does."""
    scores = quantized.astype(np.float32) @ query.astype(np.float32) / SCALE
    rows = np.argsort(-scores, kind="stable")[:k]
    return rows.tolist(), [round(float(s), 4) for s in scores[rows]]
