"""Brute-force cosine search over int8-quantized unit vectors."""

import numpy as np

SCALE = 127.0


def quantize(vectors: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(vectors * SCALE), -SCALE, SCALE).astype(np.int8)


class SearchIndex:
    def __init__(self, vectors: np.ndarray) -> None:
        self._matrix = vectors.astype(np.float32) / SCALE

    def top(self, query: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
        scores = self._matrix @ query.astype(np.float32)
        k = min(k, len(scores))
        rows = np.argpartition(-scores, k - 1)[:k]
        rows = rows[np.argsort(-scores[rows])]
        return rows, scores[rows]
