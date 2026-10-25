import pytest
from fastapi.testclient import TestClient

from georeset_viz.app import create_app
from georeset_viz.search import SearchService
from tests.conftest import SQUARE, fake_encode


@pytest.fixture
def client(data_dir):
    return TestClient(create_app(SearchService.load(data_dir, fake_encode)))


def test_search_endpoint(client):
    body = client.get("/api/search", params={"q": "eau"}).json()
    assert body["results"][0]["polygon"] == "way/1"


def test_search_rejects_empty_and_long_queries(client):
    assert client.get("/api/search", params={"q": ""}).status_code == 422
    assert client.get("/api/search", params={"q": "x" * 201}).status_code == 422


def test_polygon_endpoint(client):
    assert client.get("/api/polygon", params={"id": "way/1"}).json() == SQUARE
    assert client.get("/api/polygon", params={"id": "way/9"}).status_code == 404


def test_serves_page(client):
    assert "<title>" in client.get("/").text


def test_search_response_is_gzipped(client):
    response = client.get("/api/search", params={"q": "eau"}, headers={"Accept-Encoding": "gzip"})
    assert response.headers["content-encoding"] == "gzip"
