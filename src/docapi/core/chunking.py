"""Long-document handling: split oversized text, extract per window, merge the results.

A small local model has a limited context window (Ollama defaults to ~2k tokens). Hand it
a 15-page document in one shot and the tail is silently truncated — late-page facts come
back wrong, or get fabricated. So when the extracted text is large, we split it into
windows that comfortably fit, extract each independently against an all-optional schema,
and merge the partials field by field:

  * lists      -> union (deduped) across windows
  * booleans   -> True if any window saw it True  (a presence question, OR-ed)
  * scalars    -> the first non-empty value found
  * objects    -> merged recursively

The merged dict is then re-validated against the original strict schema.
"""
from __future__ import annotations

import json
import typing

from pydantic import BaseModel

from .dates import _submodel

# ~3.5k chars (~900 tokens) leaves room for the system prompt + JSON schema inside a
# default ~2k-token context, so each window is seen in full rather than truncated.
CHUNK_CHARS = 3500


def split_text(text: str, max_chars: int = CHUNK_CHARS) -> list[str]:
    """Greedily pack lines into windows of at most `max_chars`, never splitting a line."""
    chunks: list[str] = []
    cur: list[str] = []
    size = 0
    for line in text.split("\n"):
        if cur and size + len(line) + 1 > max_chars:
            chunks.append("\n".join(cur))
            cur, size = [], 0
        cur.append(line)
        size += len(line) + 1
    if cur:
        chunks.append("\n".join(cur))
    return chunks or [""]


def merge_partials(partials: list[dict], model: type[BaseModel]) -> dict:
    """Combine per-window extraction dicts into one, guided by each field's type."""
    return {
        name: _merge_field([p.get(name) for p in partials], field.annotation)
        for name, field in model.model_fields.items()
    }


def _merge_field(values: list[typing.Any], ann: typing.Any) -> typing.Any:
    origin = typing.get_origin(ann)
    if origin is typing.Union:  # unwrap Optional[X]
        inner = [a for a in typing.get_args(ann) if a is not type(None)]
        if len(inner) == 1:
            return _merge_field(values, inner[0])

    non_null = [v for v in values if v is not None]

    # Lists and booleans are total: "no window found anything" has a real answer (an empty
    # list, or False) rather than null — so these never collapse to None and crash the
    # strict re-validation of a required field.
    if origin is list:
        return _merge_list(non_null)
    if ann is bool:
        return any(v is True for v in non_null)

    if not non_null:
        return None

    sub = _submodel(ann)
    if sub is not None:
        dicts = [v for v in non_null if isinstance(v, dict)]
        return merge_partials(dicts, sub) if dicts else non_null[0]

    for v in non_null:  # first non-empty scalar wins
        if v not in ("", []):
            return v
    return non_null[0]


def _merge_list(lists: list[typing.Any]) -> list:
    """Union list items across windows, preserving order and deduping."""
    out: list = []
    seen: set = set()
    for lst in lists:
        if not isinstance(lst, list):
            continue
        for item in lst:
            key = _key(item)
            if key not in seen:
                seen.add(key)
                out.append(item)
    return out


def _key(item: typing.Any) -> typing.Any:
    if isinstance(item, str):
        return item.strip().casefold()
    if isinstance(item, (dict, list)):
        return json.dumps(item, sort_keys=True, default=str)
    return item
