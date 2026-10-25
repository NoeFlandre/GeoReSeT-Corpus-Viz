"""CRAP score per function from radon complexity and a coverage.py JSON report.

Usage: uv run coverage json -o coverage.json && uv run python -m tools.crap coverage.json
"""

import json
import sys
from pathlib import Path

from radon.complexity import cc_visit

THRESHOLD = 6


def crap(complexity: int, coverage: float) -> float:
    return complexity**2 * (1 - coverage) ** 3 + complexity


def _coverage(lines: range, executed: set[int], missing: set[int]) -> float:
    measured = [n for n in lines if n in executed or n in missing]
    return sum(n in executed for n in measured) / len(measured) if measured else 1.0


def function_scores(report: dict) -> list[tuple[str, float]]:
    scores = []
    for path, data in report["files"].items():
        executed, missing = set(data["executed_lines"]), set(data["missing_lines"])
        for block in cc_visit(Path(path).read_text()):
            lines = range(block.lineno, block.endline + 1)
            score = crap(block.complexity, _coverage(lines, executed, missing))
            scores.append((f"{path}:{block.fullname}", score))
    return scores


def main() -> None:  # pragma: no cover
    scores = sorted(function_scores(json.loads(Path(sys.argv[1]).read_text())), key=lambda s: -s[1])
    for name, score in scores[:10]:
        print(f"{score:6.2f}  {name}")
    sys.exit(int(scores[0][1] >= THRESHOLD))


if __name__ == "__main__":  # pragma: no cover
    main()
