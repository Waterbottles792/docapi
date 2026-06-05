"""Grounding check: catch values the model invented.

Schema validation proves the output has the right *shape*. It says nothing about whether
the values are *true*. A small model handed a long document will happily fabricate a
plausible string — and return it at high confidence. (Observed in the wild: a 15-page
restaurant guide that yielded invented pizza toppings the source never mentioned.)

So after validation we verify every free-text string leaf actually appears in the source
text. Strings are where fabrication happens; dates get reformatted (26-05-2025 ->
2025-05-26) and numbers vary in formatting, so verbatim presence isn't meaningful for
them — those are skipped. Anything ungrounded is reported by path so the caller can warn
and lower confidence instead of returning silently-wrong data.
"""
from __future__ import annotations

import re
import typing

from pydantic import BaseModel

from .dates import _submodel

_WS = re.compile(r"\s+")


def _norm(text: str) -> str:
    """Whitespace-collapsed, case-folded form for tolerant substring matching."""
    return _WS.sub(" ", text).strip().casefold()


def _is_str_type(ann: typing.Any) -> bool:
    if ann is str:
        return True
    if typing.get_origin(ann) is typing.Union:
        return any(a is str for a in typing.get_args(ann))
    return False


def find_ungrounded(data: dict, model: type[BaseModel], source: str) -> list[str]:
    """Dotted paths of string leaves whose value isn't found verbatim in `source`.

    e.g. ``["cuisine", "menu_items[2]"]``. Empty list means every checked string is
    grounded in the source text.
    """
    haystack = _norm(source)
    misses: list[str] = []
    _walk(data, model, haystack, "", misses)
    return misses


def _check(value: str, path: str, haystack: str, misses: list[str]) -> None:
    needle = _norm(value)
    if needle and needle not in haystack:
        misses.append(path)


def _walk(
    data: typing.Any,
    model: type[BaseModel],
    haystack: str,
    prefix: str,
    misses: list[str],
) -> None:
    if not isinstance(data, dict):
        return
    for name, field in model.model_fields.items():
        value = data.get(name)
        if value is None:
            continue
        path = f"{prefix}.{name}" if prefix else name

        if isinstance(value, str):
            if _is_str_type(field.annotation):  # skip reformatted dates
                _check(value, path, haystack, misses)
            continue

        if isinstance(value, list):
            sub = _submodel(field.annotation)
            for i, item in enumerate(value):
                ipath = f"{path}[{i}]"
                if isinstance(item, dict) and sub is not None:
                    _walk(item, sub, haystack, ipath, misses)
                elif isinstance(item, str):
                    _check(item, ipath, haystack, misses)
            continue

        if isinstance(value, dict):
            sub = _submodel(field.annotation)
            if sub is not None:
                _walk(value, sub, haystack, path, misses)
