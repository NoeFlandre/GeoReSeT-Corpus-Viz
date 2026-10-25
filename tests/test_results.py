import numpy as np

from georeset_viz.results import best_per_polygon, hex_features, tag_counts


def test_best_per_polygon_keeps_first_hit_of_each_polygon():
    rows = np.array([4, 2, 0, 3])
    scores = np.array([0.9, 0.8, 0.7, 0.6])
    polygon_ids = ["a", "b", "b", "a", "a"]
    assert best_per_polygon(rows, scores, polygon_ids) == [(4, 0.9), (2, 0.8)]


def test_hex_features_count_points_and_keep_max_score():
    points = [(45.76, 4.83, 0.5), (45.76, 4.83, 0.9), (45.19, 5.72, 0.7)]
    features = hex_features(points, resolution=7)["features"]
    by_count = sorted(features, key=lambda f: f["properties"]["count"])
    assert [f["properties"]["count"] for f in by_count] == [1, 2]
    assert by_count[1]["properties"]["score"] == 0.9
    ring = by_count[0]["geometry"]["coordinates"][0]
    assert ring[0] == ring[-1] and 5.6 < ring[0][0] < 5.8


def test_tag_counts_sorted_and_truncated():
    assert tag_counts(["a", "b", "a", "c", "a", "b"], top=2) == [["a", 3], ["b", 2]]


def test_hex_coordinates_are_rounded():
    ring = hex_features([(45.123456789, 5.123456789, 1.0)], resolution=7)["features"][0]
    lon, lat = ring["geometry"]["coordinates"][0][0]
    assert lon == round(lon, 5) and lat == round(lat, 5)
