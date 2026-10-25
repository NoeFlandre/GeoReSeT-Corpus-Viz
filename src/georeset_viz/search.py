"""Query the sentence index and shape the answer for the map."""

from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

import numpy as np

from georeset_viz import config
from georeset_viz.index import SearchIndex
from georeset_viz.results import best_per_polygon, hex_features, tag_counts
from georeset_viz.store import read_json

Encoder = Callable[[str], np.ndarray]


class SearchService:
    def __init__(
        self, encode: Encoder, index: SearchIndex, sentences: dict, polygons: dict
    ) -> None:
        self._encode = encode
        self._index = index
        self._sentences = sentences
        self._polygons = polygons
        self._cached_search = lru_cache(maxsize=512)(self._search)

    @classmethod
    def load(cls, data_dir: Path, encode: Encoder) -> "SearchService":
        return cls(
            encode,
            SearchIndex(np.load(data_dir / config.VECTORS_FILE)),
            read_json(data_dir / config.SENTENCES_FILE),
            read_json(data_dir / config.POLYGONS_FILE),
        )

    def _result(self, row: int, score: float) -> dict:
        polygon_id = self._sentences["polygon"][row]
        meta = self._polygons[polygon_id]
        return {
            "polygon": polygon_id,
            "name": meta["name"],
            "tag": meta["tag"],
            "lat": meta["lat"],
            "lon": meta["lon"],
            "score": round(score, 4),
            "text": self._sentences["text"][row],
            "source": self._sentences["source"][row],
            "url": self._sentences["url"][row],
        }

    def search(self, query: str) -> dict:
        return self._cached_search(" ".join(query.split()))

    def _search(self, query: str) -> dict:
        rows, scores = self._index.top(self._encode(query), config.MAP_SENTENCES)
        hits = [
            self._result(r, s)
            for r, s in best_per_polygon(rows, scores, self._sentences["polygon"])
        ]
        return {
            "results": hits[: config.LIST_SIZE],
            "hexes": hex_features(
                ((h["lat"], h["lon"], h["score"]) for h in hits), config.HEX_RESOLUTION
            ),
            "tags": tag_counts((h["tag"] for h in hits), config.TOP_TAGS),
        }

    def geometry(self, polygon_id: str) -> dict | None:
        return self._polygons.get(polygon_id, {}).get("geometry")
