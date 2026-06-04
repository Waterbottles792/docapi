"""Field-level scoring for the eval harness — pure, deterministic, unit-testable.

Kept in the package (not in scripts/) so the comparison logic the accuracy number
rests on is covered by tests.
"""
from __future__ import annotations

from typing import Any


def match_field(expected: Any, actual: Any) -> bool:
    """Lenient leaf comparison: float tolerance for numbers, trimmed/case-insensitive
    for strings, exact for the rest."""
    if isinstance(expected, bool) or isinstance(actual, bool):
        # Keep bools distinct from 1/0 (True == 1 in Python otherwise).
        return type(expected) is bool and type(actual) is bool and expected == actual
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return abs(float(expected) - float(actual)) < 0.01
    if isinstance(expected, str) and isinstance(actual, str):
        return expected.strip().casefold() == actual.strip().casefold()
    return expected == actual


def score(expected: Any, actual: Any) -> tuple[int, int, list[str]]:
    """Recursively count matching leaf fields.

    Returns (matched, total, mismatch_paths) where paths name the fields that differ,
    e.g. ``["invoice_date", "line_items[0].amount"]``.
    """
    if isinstance(expected, dict):
        matched = total = 0
        misses: list[str] = []
        for key, exp in expected.items():
            act = actual.get(key) if isinstance(actual, dict) else None
            m, t, sub = score(exp, act)
            matched += m
            total += t
            # join with "." unless the child is a list index ("[0]..."), which attaches directly
            misses += [key + s if s.startswith("[") else (f"{key}.{s}" if s else key) for s in sub]
        return matched, total, misses
    if isinstance(expected, list):
        matched = total = 0
        misses = []
        for i, exp in enumerate(expected):
            act = actual[i] if isinstance(actual, list) and i < len(actual) else None
            m, t, sub = score(exp, act)
            matched += m
            total += t
            misses += [f"[{i}].{s}" if s else f"[{i}]" for s in sub]
        return matched, total, misses
    ok = match_field(expected, actual)
    return (1 if ok else 0), 1, ([] if ok else [""])
