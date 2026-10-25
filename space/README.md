---
title: GeoReSeT Text Atlas
emoji: 🗺️
colorFrom: blue
colorTo: green
sdk: static
app_file: index.html
pinned: false
license: odbl
short_description: Search land-use text on a map of Rhône-Alpes
datasets:
  - NoeFlandre/GeoReSeT-Corpus
models:
  - Xenova/multilingual-e5-small
---

# Atlas textuel Rhône-Alpes

Describe a landscape in words ("tourbière drainée", "glacier en recul") and see where the texts
of the [GeoReSeT Corpus](https://huggingface.co/datasets/NoeFlandre/GeoReSeT-Corpus) describe
it. Click a place to see its OpenStreetMap polygon on IGN aerial imagery next to the sentence:
what the text says vs what the image shows.

* Sentences: French, labelled land-use, region Rhône-Alpes, de-duplicated, at most 20 per polygon
  (71.6k sentences, 9.8k polygons).
* Search runs in your browser: exact cosine search over int8 vectors (`multilingual-e5-small`).
  Example queries are pre-computed; a typed query loads the model once (about 130 MB, then cached).
* Map: hexagons (H3 res. 6) count the polygons among the 300 closest sentences.

Code: [NoeFlandre/GeoReSeT-Corpus-Viz](https://github.com/NoeFlandre/GeoReSeT-Corpus-Viz).
