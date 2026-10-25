"""Turn ranked sentences into map-ready summaries."""

from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from functools import lru_cache

import h3
import numpy as np


def best_per_polygon(
    rows: np.ndarray, scores: np.ndarray, polygon_ids: Sequence[str]
) -> list[tuple[int, float]]:
    best: dict[str, tuple[int, float]] = {}
    for row, score in zip(rows.tolist(), scores.tolist(), strict=True):
        best.setdefault(polygon_ids[row], (row, score))
    return list(best.values())


@lru_cache(maxsize=65536)
def _hexagon(cell: str) -> list[list[float]]:
    ring = [[round(lon, 5), round(lat, 5)] for lat, lon in h3.cell_to_boundary(cell)]
    return [*ring, ring[0]]


def hex_features(points: Iterable[tuple[float, float, float]], resolution: int) -> dict:
    cells: dict[str, list[float]] = defaultdict(list)
    for lat, lon, score in points:
        cells[h3.latlng_to_cell(lat, lon, resolution)].append(score)
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [_hexagon(cell)]},
            "properties": {"count": len(scores), "score": max(scores)},
        }
        for cell, scores in cells.items()
    ]
    return {"type": "FeatureCollection", "features": features}


def tag_counts(tags: Iterable[str], top: int) -> list[list]:
    return [[tag, n] for tag, n in Counter(tags).most_common(top)]
