"""Gzipped JSON files for the app's data."""

import gzip
import json
from pathlib import Path
from typing import Any


def write_json(path: Path, data: Any) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def read_json(path: Path) -> Any:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)
