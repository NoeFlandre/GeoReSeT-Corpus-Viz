from tools.crap import crap, function_scores


def test_crap_formula():
    assert crap(complexity=1, coverage=1.0) == 1
    assert crap(complexity=3, coverage=0.0) == 12


def test_function_scores_use_covered_lines(tmp_path):
    source = tmp_path / "m.py"
    source.write_text("def f(x):\n    if x:\n        return 1\n    return 2\n")
    report = {"files": {str(source): {"executed_lines": [1, 2, 4], "missing_lines": [3]}}}
    [(name, score)] = function_scores(report)
    assert name.endswith("m.py:f")
    assert score == crap(2, 3 / 4)
