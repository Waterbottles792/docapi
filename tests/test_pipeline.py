from __future__ import annotations

import pytest

from docapi.core.errors import UnsupportedFileType, ValidationFailed
from docapi.core.pipeline import extract_to_schema
from docapi.core.understand import StubUnderstander

SCHEMA = {"invoice_number": "string", "total": "number"}


def test_happy_path_with_canned_data(sample_pdf):
    stub = StubUnderstander({"invoice_number": "INV-2043", "total": 1280.0})
    result = extract_to_schema(sample_pdf, "invoice.pdf", SCHEMA, understander=stub)
    assert result.data == {"invoice_number": "INV-2043", "total": 1280.0}
    assert result.pages == 1
    assert 0.0 <= result.confidence <= 1.0


def test_corrective_retry_recovers(sample_pdf):
    # first response is invalid (total is not a number), retry fixes it
    stub = StubUnderstander(
        [{"invoice_number": "INV-2043", "total": "oops"}, {"invoice_number": "INV-2043", "total": 1280.0}]
    )
    result = extract_to_schema(sample_pdf, "invoice.pdf", SCHEMA, understander=stub)
    assert result.data["total"] == 1280.0


def test_validation_failed_after_retry(sample_pdf):
    stub = StubUnderstander({"invoice_number": "INV-2043", "total": "still-bad"})
    with pytest.raises(ValidationFailed) as exc:
        extract_to_schema(sample_pdf, "invoice.pdf", SCHEMA, understander=stub)
    assert "total" in exc.value.context["fields"]
    assert exc.value.context["partial_data"]["invoice_number"] == "INV-2043"


def test_unsupported_file_type(sample_pdf):
    with pytest.raises(UnsupportedFileType):
        extract_to_schema(b"data", "notes.txt", SCHEMA, understander=StubUnderstander())


def test_stub_placeholder_runs_without_canned(sample_pdf):
    # default stub emits schema-valid placeholders -> pipeline completes at $0
    result = extract_to_schema(sample_pdf, "invoice.pdf", SCHEMA, understander=StubUnderstander())
    assert set(result.data) == {"invoice_number", "total"}
