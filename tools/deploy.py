"""Create or update the static Hugging Face Space from web/.

Usage: HF_TOKEN=... uv run python -m tools.deploy [owner/space-name]
"""

import sys
from pathlib import Path

from huggingface_hub import CommitOperationAdd, HfApi

from georeset_viz import config

CARD = Path(__file__).resolve().parents[1] / "space" / "README.md"
SPACE = "NoeFlandre/GeoReSeT-Text-Atlas"


def operations() -> list[CommitOperationAdd]:
    web = config.WEB_DIR
    files = sorted(
        p for p in web.rglob("*") if p.is_file() and "tests" not in p.relative_to(web).parts
    )
    adds = [CommitOperationAdd(str(p.relative_to(web)), p) for p in files]
    return [*adds, CommitOperationAdd("README.md", CARD)]


def main() -> None:  # pragma: no cover - talks to the Hub
    space = sys.argv[1] if len(sys.argv) > 1 else SPACE
    api = HfApi()
    api.create_repo(space, repo_type="space", space_sdk="static", exist_ok=True)
    api.create_commit(space, operations(), commit_message="Deploy", repo_type="space")
    print(f"https://huggingface.co/spaces/{space}")


if __name__ == "__main__":  # pragma: no cover
    main()
