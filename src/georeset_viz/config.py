"""Settings for the offline build; the browser reads its share from meta.json."""

from pathlib import Path

DATASET = "NoeFlandre/GeoReSeT-Corpus"
REGION = "rhone-alpes"
LANGUAGE = "fra_Latn"

MODEL_REPO = "Xenova/multilingual-e5-small"
MODEL_FILE = "onnx/model_quantized.onnx"
TOKENIZER_FILE = "tokenizer.json"
MAX_TOKENS = 128

MIN_CHARS = 40
MAX_CHARS = 300
MAX_SENTENCES_PER_POLYGON = 20
SIMPLIFY_DEGREES = 0.00005  # about 5 m
HEX_RESOLUTION = 6

EXAMPLES = [
    "glacier en recul",
    "lac de barrage",
    "friche industrielle",
    "éboulement",
    "ancienne carrière",
    "tourbière drainée",
    "domaine skiable",
    "vignoble en coteaux",
    "zone inondable",
    "marais asséché",
]

MAP_SENTENCES = 300

# Read by the page (web/js/app.js) through meta.json.
BROWSER_SETTINGS = {
    "model": MODEL_REPO,
    "mapSentences": MAP_SENTENCES,
    "listSize": 30,
    "topTags": 8,
}

WEB_DIR = Path(__file__).resolve().parents[2] / "web"
DATA_DIR = WEB_DIR / "data"
