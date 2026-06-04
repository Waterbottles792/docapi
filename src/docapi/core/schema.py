"""Translate the caller's friendly schema into a pydantic model.

The friendly schema maps field names to types:
    "string", "number", "integer", "boolean", "date"  (append "?" => optional)
    [ {item schema} ]  => array of objects/scalars
    { ... }            => nested object

That one pydantic model drives both the prompt we give the model and validation.
"""
from __future__ import annotations

import datetime
from typing import Any, Optional

from pydantic import BaseModel, create_model

_SCALARS: dict[str, type] = {
    "string": str,
    "number": float,
    "integer": int,
    "boolean": bool,
    "date": datetime.date,
}


def _camel(name: str) -> str:
    return "".join(part.title() for part in name.replace("-", "_").split("_")) or "Field"


def _resolve(name: str, spec: Any) -> tuple[Any, bool]:
    """Return (python_type, is_optional) for one field spec."""
    if isinstance(spec, str):
        optional = spec.endswith("?")
        base = spec[:-1] if optional else spec
        if base not in _SCALARS:
            raise ValueError(f"Unknown type {spec!r} for field {name!r}")
        return _SCALARS[base], optional
    if isinstance(spec, dict):
        return build_model(_camel(name) + "Obj", spec), False
    if isinstance(spec, list):
        if len(spec) != 1:
            raise ValueError(f"Array spec for {name!r} must have exactly one item schema")
        item_type, _ = _resolve(name + "_item", spec[0])
        return list[item_type], False  # type: ignore[valid-type]
    raise ValueError(f"Unsupported schema spec for {name!r}: {spec!r}")


def build_model(name: str, schema: dict[str, Any]) -> type[BaseModel]:
    if not isinstance(schema, dict) or not schema:
        raise ValueError("schema must be a non-empty JSON object")
    fields: dict[str, tuple[Any, Any]] = {}
    for field_name, spec in schema.items():
        py_type, optional = _resolve(field_name, spec)
        fields[field_name] = (Optional[py_type], None) if optional else (py_type, ...)
    return create_model(name, **fields)  # type: ignore[call-overload]
