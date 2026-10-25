from georeset_viz.store import read_json, write_json


def test_json_roundtrip_is_gzipped(tmp_path):
    path = tmp_path / "x.json.gz"
    write_json(path, {"é": [1, 2]})
    assert path.read_bytes()[:2] == b"\x1f\x8b"
    assert read_json(path) == {"é": [1, 2]}
