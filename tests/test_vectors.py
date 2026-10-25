import gzip

import numpy as np

from georeset_viz.vectors import quantize, top_rows, write_vectors


def test_quantize_maps_unit_range_to_int8():
    q = quantize(np.array([[1.0, -1.0, 0.5]]))
    assert q.dtype == np.int8
    np.testing.assert_array_equal(q, [[127, -127, 64]])


def test_write_vectors_is_gzipped_row_major_int8(tmp_path):
    path = tmp_path / "v.i8.gz"
    write_vectors(path, quantize(np.array([[1.0, 0.0], [0.0, -1.0]])))
    raw = np.frombuffer(gzip.decompress(path.read_bytes()), dtype=np.int8)
    np.testing.assert_array_equal(raw, [127, 0, 0, -127])


def test_top_rows_ranks_int8_rows_like_the_browser():
    rows, scores = top_rows(
        quantize(np.array([[1.0, 0.0], [0.0, 1.0], [0.6, 0.8]])), np.array([0.0, 1.0]), k=2
    )
    assert rows == [1, 2]
    assert scores == [1.0, 0.8031]
