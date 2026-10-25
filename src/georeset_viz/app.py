"""FastAPI app: JSON search API plus the static map page."""

from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from georeset_viz import config
from georeset_viz.search import SearchService

STATIC_DIR = Path(__file__).parent / "static"


def create_app(service: SearchService) -> FastAPI:
    app = FastAPI(title="GeoReSeT text atlas")
    app.add_middleware(GZipMiddleware, minimum_size=500)

    @app.get("/api/search")
    def search(q: Annotated[str, Query(min_length=1, max_length=200)]) -> dict:
        return service.search(q)

    @app.get("/api/polygon")
    def polygon(id: str) -> dict:
        geometry = service.geometry(id)
        if geometry is None:
            raise HTTPException(404, "unknown polygon")
        return geometry

    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True))
    return app


def main() -> None:  # pragma: no cover - wiring for the Space
    import uvicorn

    from georeset_viz.embedder import Embedder

    service = SearchService.load(config.DATA_DIR, Embedder.from_hub().query)
    uvicorn.run(create_app(service), host="0.0.0.0", port=7860)
