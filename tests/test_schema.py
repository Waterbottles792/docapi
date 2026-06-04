from __future__ import annotations

import datetime

import pytest
from pydantic import ValidationError

from docapi.core.schema import build_model


def test_scalars_and_optional():
    M = build_model("M", {"name": "string", "total": "number", "tax_id": "string?"})
    obj = M.model_validate({"name": "ACME", "total": 12.5})
    assert obj.total == 12.5
    assert obj.tax_id is None


def test_date_coercion():
    M = build_model("M", {"d": "date"})
    assert M.model_validate({"d": "2026-05-18"}).d == datetime.date(2026, 5, 18)


def test_nested_and_array():
    M = build_model(
        "M",
        {"vendor": {"name": "string"}, "line_items": [{"desc": "string", "amount": "number"}]},
    )
    obj = M.model_validate(
        {"vendor": {"name": "ACME"}, "line_items": [{"desc": "x", "amount": 1.0}]}
    )
    assert obj.vendor.name == "ACME"
    assert obj.line_items[0].amount == 1.0


def test_missing_required_raises():
    M = build_model("M", {"name": "string"})
    with pytest.raises(ValidationError):
        M.model_validate({})


def test_unknown_type_rejected():
    with pytest.raises(ValueError):
        build_model("M", {"x": "frobnicate"})


def test_empty_schema_rejected():
    with pytest.raises(ValueError):
        build_model("M", {})
