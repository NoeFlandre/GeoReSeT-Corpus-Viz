---
title: GeoReSeT Text Atlas
emoji: 🗺️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: odbl
short_description: Search land-use text on a map of Rhône-Alpes
datasets:
  - NoeFlandre/GeoReSeT-Corpus
models:
  - intfloat/multilingual-e5-small
---

# Atlas textuel Rhône-Alpes

Describe a landscape in words ("tourbière drainée", "vignes en terrasses") and see where
the texts of the [GeoReSeT Corpus](https://huggingface.co/datasets/NoeFlandre/GeoReSeT-Corpus)
describe it. Click a place to see its OpenStreetMap polygon on IGN aerial imagery next to the
sentence: what the text says vs what the image shows.

* Sentences: French, labelled land-use, region Rhône-Alpes, de-duplicated, at most 20 per polygon.
* Search: `multilingual-e5-small` (int8 ONNX) on CPU, exact cosine search over int8 vectors.
* Map: hexagons (H3 res. 7) count the polygons among the 2,000 closest sentences.

Code: [NoeFlandre/GeoReSeT-Corpus-Viz](https://github.com/NoeFlandre/GeoReSeT-Corpus-Viz).
