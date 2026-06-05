"""Translate the caller's friendly schema into a pydantic model.

The friendly schema maps field names to types:
    "string", "number", "integer", "boolean", "date"  (append "?" => optional)
    [ {item schema} ]  => array of objects/scalars
    { ... }            => nested object

That one pydantic model drives both the prompt we give the model and validation.
"""
from __future__ import annotations

import datetime
import typing
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


def make_all_optional(model: type[BaseModel], name: str | None = None) -> type[BaseModel]:
    """A copy of `model` with every field (recursively) optional, defaulting to None.

    Used for chunked extraction: each chunk sees only part of a long document, so a field
    absent from that chunk must be allowed back as null — rather than forced (and so
    fabricated) by the structured-output schema. The merged result is re-validated against
    the original strict model.
    """
    fields: dict[str, tuple[Any, Any]] = {}
    for fname, f in model.model_fields.items():
        if f.annotation is bool:
            # Booleans are total — a presence question always has an answer (False if
            # absent). Keep them required so the model commits true/false per window
            # instead of dodging to null, which would lose the fact at merge time.
            fields[fname] = (bool, ...)
        else:
            fields[fname] = (Optional[_relax_annotation(f.annotation)], None)
    return create_model(name or model.__name__ + "Optional", **fields)  # type: ignore[call-overload]


def _relax_annotation(ann: Any) -> Any:
    """Recurse into list/Optional/nested-model annotations, relaxing nested models."""
    origin = typing.get_origin(ann)
    if origin is list:
        (item,) = typing.get_args(ann)
        if isinstance(item, type) and issubclass(item, BaseModel):
            return list[make_all_optional(item)]  # type: ignore[valid-type,misc]
        return ann
    if origin is typing.Union:
        inner = [a for a in typing.get_args(ann) if a is not type(None)]
        return _relax_annotation(inner[0]) if len(inner) == 1 else ann
    if isinstance(ann, type) and issubclass(ann, BaseModel):
        return make_all_optional(ann)
    return ann
