"""int8 storage for unit vectors, read by the browser as a gzipped Int8Array."""

import gzip
from pathlib import Path

import numpy as np

SCALE = 127.0


def quantize(vectors: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(vectors * SCALE), -SCALE, SCALE).astype(np.int8)


def write_vectors(path: Path, vectors: np.ndarray) -> None:
    path.write_bytes(gzip.compress(quantize(vectors).tobytes(order="C"), compresslevel=9))
