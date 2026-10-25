"""Settings shared by the offline build and the web app."""

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

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SENTENCES_FILE = "sentences.json.gz"
VECTORS_FILE = "vectors.npy"
POLYGONS_FILE = "polygons.json.gz"

MAP_SENTENCES = 2000
LIST_SIZE = 30
HEX_RESOLUTION = 7
TOP_TAGS = 8
