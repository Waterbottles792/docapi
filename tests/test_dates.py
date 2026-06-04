from __future__ import annotations

import pytest

from docapi.core.dates import normalize_dates, parse_date
from docapi.core.pipeline import extract_to_schema
from docapi.core.schema import build_model
from docapi.core.understand import StubUnderstander


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("26-05-2025", "2025-05-26"),  # Indian DD-MM-YYYY (the nptel_fee.pdf case)
        ("26/05/2025", "2025-05-26"),
        ("2025-05-26", "2025-05-26"),
        ("26-May-2025", "2025-05-26"),
        ("May 26, 2025", "2025-05-26"),
        ("26.05.2025", "2025-05-26"),
        ("not a date", None),
    ],
)
def test_parse_date(raw, expected):
    assert parse_date(raw) == expected


def test_normalize_top_level_and_nested():
    model = build_model(
        "M",
        {"d": "date", "vendor": {"founded": "date"}, "rows": [{"when": "date"}]},
    )
    data = {"d": "26-05-2025", "vendor": {"founded": "01/02/2020"}, "rows": [{"when": "03-04-2021"}]}
    normalize_dates(data, model)
    assert data == {
        "d": "2025-05-26",
        "vendor": {"founded": "2020-02-01"},
        "rows": [{"when": "2021-04-03"}],
    }


def test_pipeline_repairs_indian_date(sample_pdf):
    # The exact bug from nptel_fee.pdf: model returns DD-MM-YYYY, pipeline normalises it.
    schema = {"invoice_date": "date", "total_amount": "number"}
    stub = StubUnderstander({"invoice_date": "26-05-2025", "total_amount": 1000})
    result = extract_to_schema(sample_pdf, "receipt.pdf", schema, understander=stub)
    assert result.data["invoice_date"] == "2025-05-26"
