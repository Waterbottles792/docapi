from __future__ import annotations

import json
from pathlib import Path

import pytest

from docapi.eval_scoring import match_field, score

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize(
    "expected,actual,ok",
    [
        (1000.0, 1000, True),          # int/float equality
        (1000.0, 1000.004, True),      # float tolerance
        (1000.0, 1001, False),
        ("INV-1", " inv-1 ", True),    # trimmed + case-insensitive
        ("abc", "abd", False),
        (True, True, True),
        (True, 1, False),              # bool is not 1
        ("2025-05-26", "2025-05-26", True),
    ],
)
def test_match_field(expected, actual, ok):
    assert match_field(expected, actual) is ok


def test_score_perfect():
    exp = {"a": "x", "b": 2.0}
    assert score(exp, {"a": "X", "b": 2}) == (2, 2, [])


def test_score_reports_mismatch_paths():
    exp = {"a": "x", "b": 2.0}
    matched, total, misses = score(exp, {"a": "wrong", "b": 2})
    assert (matched, total) == (1, 2)
    assert misses == ["a"]


def test_score_nested_and_list_paths():
    exp = {"vendor": {"name": "ACME"}, "rows": [{"amt": 10.0}, {"amt": 20.0}]}
    act = {"vendor": {"name": "ACME"}, "rows": [{"amt": 10.0}, {"amt": 99.0}]}
    matched, total, misses = score(exp, act)
    assert (matched, total) == (2, 3)  # vendor.name + rows[0].amt correct, rows[1].amt wrong
    assert misses == ["rows[1].amt"]


def test_score_missing_field_counts_as_miss():
    matched, total, misses = score({"a": 1.0, "b": 2.0}, {"a": 1.0})
    assert (matched, total) == (1, 2)
    assert misses == ["b"]


def test_eval_cases_are_wellformed():
    """Every case manifest pins a real fixture and matching schema/expected keys."""
    cases_dir = ROOT / "evals" / "cases"
    fixtures_dir = ROOT / "evals" / "fixtures"
    cases = list(cases_dir.glob("*.json"))
    assert cases, "no eval cases found"
    for path in cases:
        case = json.loads(path.read_text())
        assert (fixtures_dir / case["document"]).is_file(), f"missing fixture for {path.name}"
        assert set(case["expected"]) <= set(case["schema"]), f"expected/schema mismatch in {path.name}"
