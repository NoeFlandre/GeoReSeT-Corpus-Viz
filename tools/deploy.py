"""Create or update the Hugging Face Space from this repository.

Usage: uv run python -m tools.deploy [owner/space-name]
"""

import sys
from pathlib import Path

from huggingface_hub import CommitOperationAdd, HfApi

ROOT = Path(__file__).resolve().parents[1]
SPACE = "NoeFlandre/GeoReSeT-Text-Atlas"
FILES = ["Dockerfile", "pyproject.toml", "uv.lock", "README.md", "src/**/*", "data/*"]


def operations() -> list[CommitOperationAdd]:
    paths = {p for pattern in FILES for p in ROOT.glob(pattern) if p.is_file()}
    adds = [
        CommitOperationAdd(str(p.relative_to(ROOT)), p)
        for p in sorted(paths)
        if "__pycache__" not in p.parts and p.name != "README.md"
    ]
    return [*adds, CommitOperationAdd("README.md", ROOT / "space" / "README.md")]


def main() -> None:  # pragma: no cover - talks to the Hub
    space = sys.argv[1] if len(sys.argv) > 1 else SPACE
    api = HfApi()
    api.create_repo(space, repo_type="space", space_sdk="docker", exist_ok=True)
    api.create_commit(space, operations(), commit_message="Deploy", repo_type="space")
    print(f"https://huggingface.co/spaces/{space}")


if __name__ == "__main__":  # pragma: no cover
    main()
