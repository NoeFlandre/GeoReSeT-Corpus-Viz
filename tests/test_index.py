import numpy as np

from georeset_viz.index import SearchIndex, quantize


def test_quantize_maps_unit_range_to_int8():
    q = quantize(np.array([[1.0, -1.0, 0.5]]))
    assert q.dtype == np.int8
    np.testing.assert_array_equal(q, [[127, -127, 64]])


def test_top_returns_best_rows_in_descending_order():
    vectors = quantize(np.array([[1.0, 0.0], [0.0, 1.0], [0.6, 0.8]]))
    rows, scores = SearchIndex(vectors).top(np.array([0.0, 1.0]), k=2)
    np.testing.assert_array_equal(rows, [1, 2])
    np.testing.assert_allclose(scores, [1.0, 0.8], atol=0.01)


def test_top_caps_k_at_index_size():
    rows, _ = SearchIndex(quantize(np.eye(2))).top(np.array([1.0, 0.0]), k=10)
    assert len(rows) == 2
