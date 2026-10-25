# GeoReSeT Text Atlas

Semantic search map over the French land-use sentences of the
[GeoReSeT Corpus](https://huggingface.co/datasets/NoeFlandre/GeoReSeT-Corpus) in Rhône-Alpes.
Type a landscape description, see where the texts describe it, and compare each sentence with
its OpenStreetMap polygon on IGN aerial imagery.

## How it works

1. **Build (offline, once).** DuckDB reads only the needed rows from the Hub
   (`fra_Latn`, `rhone-alpes`, `landuse = true`, 40–300 characters), removes duplicate
   sentences and keeps at most 20 per polygon (71.6k sentences, 9.8k polygons). Polygon outlines
   are simplified to about 5 m. Sentences are embedded with `multilingual-e5-small`
   (int8 ONNX) and stored as int8 vectors. The input dataset is only read.
2. **Serve.** FastAPI loads the vectors once, embeds the query (about 4 ms on CPU), runs an
   exact cosine search, keeps the best sentence per polygon, and counts polygons per H3 hexagon.
   Responses are gzipped and repeated queries are cached.
3. **Page.** Leaflet (Canvas renderer) on IGN Géoplateforme orthophotos. Outlines are fetched
   only when a place is clicked.

| File | Size |
|---|---|
| `data/vectors.npy` (int8) | ~28 MB |
| `data/sentences.json.gz` | 3.5 MB |
| `data/polygons.json.gz` | 1.5 MB |

## Development

```bash
uv sync --all-groups
uv run pytest                                  # tests (network-marked ones download the model)
uv run ruff check . && uv run ruff format --check . && uv run ty check
uv run pytest --cov && uv run coverage json -o coverage.json && uv run python -m tools.crap coverage.json
```

`tools.crap` fails when a function's CRAP score reaches 6.

## Build the data and run locally

```bash
uv run python -m georeset_viz.build.pipeline   # writes data/ (about 6 min on 4 CPUs)
uv run georeset-viz                            # http://localhost:7860
```

## Deploy the Space

Needs a Hugging Face token with write access in `HF_TOKEN`.

```bash
uv run python -m tools.deploy                  # NoeFlandre/GeoReSeT-Text-Atlas
```

The Space is a Docker Space on the free CPU tier. The model is downloaded while the image is
built, so the app starts without network calls. `space/README.md` is the Space card.
