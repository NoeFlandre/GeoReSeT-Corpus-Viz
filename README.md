# GeoReSeT Text Atlas

Semantic search map over the French land-use sentences of the
[GeoReSeT Corpus](https://huggingface.co/datasets/NoeFlandre/GeoReSeT-Corpus) in Rhône-Alpes.
Type a landscape description, see where the texts describe it, and compare each sentence with
its OpenStreetMap polygon on IGN aerial imagery.

It is a **static** Hugging Face Space (free, no PRO, no server): the search runs in the browser.

## How it works

1. **Build (Python, offline, once).** DuckDB reads only the needed rows from the Hub
   (`fra_Latn`, `rhone-alpes`, `landuse = true`, 40–300 characters), removes duplicate sentences
   and keeps at most 20 per polygon (71.6k sentences, 9.8k polygons). Outlines are simplified to
   about 5 m. Sentences are embedded with `multilingual-e5-small` (int8 ONNX) and saved as gzipped
   int8 vectors; the example queries are embedded too. The input dataset is only read.
2. **Page (browser).** Loads the vectors (about 17 MB, cached) and runs an exact cosine search in
   plain JS (tens of milliseconds). Example queries are instant. A typed query loads the same ONNX
   model with transformers.js once (about 130 MB, then cached by the browser). The best sentence
   per polygon goes in the list, polygons are counted per H3 hexagon, and an outline is drawn on
   IGN orthophotos when a place is clicked.

`src/georeset_viz/config.py` holds every setting; the build writes the ones the page needs to
`web/data/meta.json`.

## Layout

```
src/georeset_viz/   Python build: extract, embed, quantize, hexes, outlines
web/                the static site (index.html, js/, style.css); web/data/ is built
web/tests/          JS tests (node --test)
tools/              CRAP score check, Space deploy
space/README.md     Space card
```

## Development

```bash
uv sync
uv run pytest                                  # Python tests (network-marked ones download the model)
npm test                                       # JS tests with coverage, no npm install needed
uv run ruff check . && uv run ruff format --check . && uv run ty check
uv run pytest --cov && uv run coverage json -o coverage.json && uv run python -m tools.crap coverage.json
```

`tools.crap` fails when a Python function's CRAP score reaches 6.

## Build, preview, deploy

```bash
uv run python -m georeset_viz.build.pipeline   # writes web/data/ (about 7 min on 4 CPUs)
python3 -m http.server -d web 8000             # http://localhost:8000
HF_TOKEN=... uv run python -m tools.deploy     # static Space NoeFlandre/GeoReSeT-Text-Atlas
```
