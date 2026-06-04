from __future__ import annotations

import base64

from docapi.mcp_server import run_extract

SCHEMA = {"invoice_number": "string", "invoice_date": "date", "total_amount": "number"}


def test_run_extract_from_path(sample_pdf, tmp_path):
    pdf = tmp_path / "receipt.pdf"
    pdf.write_bytes(sample_pdf)
    # Default provider is the stub, so this runs offline and free.
    out = run_extract(SCHEMA, path=str(pdf))
    assert "data" in out
    assert set(SCHEMA) <= set(out["data"])
    assert out["pages"] == 1
    assert 0.0 <= out["confidence"] <= 1.0


def test_run_extract_from_base64(sample_pdf):
    b64 = base64.b64encode(sample_pdf).decode()
    out = run_extract(SCHEMA, content_base64=b64, filename="receipt.pdf")
    assert "data" in out


def test_run_extract_normalizes_date_via_pipeline(sample_pdf, tmp_path, monkeypatch):
    # The MCP tool inherits the same deterministic date repair as the REST path.
    from docapi.core import pipeline
    from docapi.core.understand import StubUnderstander

    monkeypatch.setattr(
        pipeline, "get_understander", lambda: StubUnderstander({"invoice_date": "26-05-2025"})
    )
    pdf = tmp_path / "r.pdf"
    pdf.write_bytes(sample_pdf)
    out = run_extract({"invoice_date": "date"}, path=str(pdf))
    assert out["data"]["invoice_date"] == "2025-05-26"


def test_missing_document_returns_structured_error():
    out = run_extract(SCHEMA)
    assert out["error"]["type"] == "bad_request"


def test_path_and_base64_conflict():
    out = run_extract(SCHEMA, path="x.pdf", content_base64="abc")
    assert out["error"]["type"] == "bad_request"


def test_unsupported_file_type_is_structured(tmp_path):
    f = tmp_path / "notes.txt"
    f.write_bytes(b"hello")
    out = run_extract(SCHEMA, path=str(f))
    assert out["error"]["type"] == "unsupported_file_type"
