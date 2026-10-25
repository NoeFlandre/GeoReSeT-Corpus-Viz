from georeset_viz.search import SearchService
from tests.conftest import SQUARE, fake_encode


def test_search_lists_each_polygon_once_with_its_best_sentence(data_dir):
    out = SearchService.load(data_dir, fake_encode).search("de l'eau")
    first = out["results"][0]
    assert [r["polygon"] for r in out["results"]] == ["way/1", "way/2"]
    assert first["text"] == "Un lac d'eau claire."
    assert first["name"] == "Lac" and first["tag"] == "natural=water"
    assert first["url"] == "https://w/1" and first["score"] > 0.99


def test_search_summarises_hexes_and_tags(data_dir):
    out = SearchService.load(data_dir, fake_encode).search("forêt")
    assert out["tags"] == [["natural=wood", 1], ["natural=water", 1]]
    assert sum(f["properties"]["count"] for f in out["hexes"]["features"]) == 2


def test_geometry_lookup(data_dir):
    service = SearchService.load(data_dir, fake_encode)
    assert service.geometry("way/1") == SQUARE
    assert service.geometry("way/404") is None


def test_repeated_queries_are_cached(data_dir):
    calls = []

    def counting_encode(text):
        calls.append(text)
        return fake_encode(text)

    service = SearchService.load(data_dir, counting_encode)
    assert service.search("eau") is service.search("  eau ")
    assert calls == ["eau"]
