"""Deterministic date handling.

Language models are unreliable at reformatting dates (e.g. Indian DD-MM-YYYY -> ISO):
they hallucinate years like 2605. So we let the model return the date *as written* and
normalise it here, in code, where it's a solved problem.
"""
from __future__ import annotations

import datetime
import typing

from pydantic import BaseModel

# Tried in order. Day-first formats come before month-first because that's the more common
# global convention; genuinely ambiguous inputs like "05/06/2025" are an accepted limitation.
_FORMATS = (
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%Y/%m/%d",
    "%d-%b-%Y",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d, %Y",
    "%B %d, %Y",
    "%d.%m.%Y",
)


def parse_date(raw: str) -> str | None:
    """Best-effort parse of a human date string into ISO 'YYYY-MM-DD', else None."""
    text = raw.strip()
    for fmt in _FORMATS:
        try:
            return datetime.datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _is_date_type(ann: typing.Any) -> bool:
    if ann is datetime.date:
        return True
    if typing.get_origin(ann) is typing.Union:
        return any(a is datetime.date for a in typing.get_args(ann))
    return False


def _submodel(ann: typing.Any) -> type[BaseModel] | None:
    """Extract a nested BaseModel from `Model`, `Optional[Model]`, or `list[Model]`."""
    candidates = (
        list(typing.get_args(ann))
        if typing.get_origin(ann) is typing.Union
        else [ann]
    )
    for cand in candidates:
        if typing.get_origin(cand) is list:
            for inner in typing.get_args(cand):
                if isinstance(inner, type) and issubclass(inner, BaseModel):
                    return inner
        if isinstance(cand, type) and issubclass(cand, BaseModel):
            return cand
    return None


def normalize_dates(data: typing.Any, model: type[BaseModel]) -> typing.Any:
    """Walk the model + data; rewrite date-typed string fields to ISO in place."""
    if not isinstance(data, dict):
        return data
    for name, field in model.model_fields.items():
        if data.get(name) is None:
            continue
        value = data[name]
        if _is_date_type(field.annotation) and isinstance(value, str):
            iso = parse_date(value)
            if iso is not None:
                data[name] = iso
            continue
        sub = _submodel(field.annotation)
        if sub is None:
            continue
        if isinstance(value, dict):
            normalize_dates(value, sub)
        elif isinstance(value, list):
            for item in value:
                normalize_dates(item, sub)
    return data
