import numpy as np
import pytest

from georeset_viz import config
from georeset_viz.index import quantize
from georeset_viz.store import write_json

SQUARE = {"type": "Polygon", "coordinates": [[[5.7, 45.1], [5.8, 45.1], [5.8, 45.2], [5.7, 45.1]]]}


def fake_encode(text: str) -> np.ndarray:
    return np.array([1.0, 0.0]) if "eau" in text else np.array([0.0, 1.0])


@pytest.fixture
def data_dir(tmp_path):
    write_json(
        tmp_path / config.SENTENCES_FILE,
        {
            "text": ["Un lac d'eau claire.", "Une forêt dense.", "Les berges du lac."],
            "source": ["wikipedia", "website", "wikipedia"],
            "url": ["https://w/1", "https://s/2", "https://w/3"],
            "polygon": ["way/1", "way/2", "way/1"],
        },
    )
    write_json(
        tmp_path / config.POLYGONS_FILE,
        {
            "way/1": {
                "name": "Lac",
                "tag": "natural=water",
                "lat": 45.15,
                "lon": 5.75,
                "area": 1e5,
                "geometry": SQUARE,
            },
            "way/2": {
                "name": "Bois",
                "tag": "natural=wood",
                "lat": 45.5,
                "lon": 6.0,
                "area": 2e4,
                "geometry": SQUARE,
            },
        },
    )
    np.save(
        tmp_path / config.VECTORS_FILE, quantize(np.array([[1.0, 0.0], [0.0, 1.0], [0.9, 0.1]]))
    )
    return tmp_path
