from __future__ import annotations

import json

from fastapi.testclient import TestClient

from conftest import make_pdf
from docapi.main import app

client = TestClient(app)
SCHEMA = {"invoice_number": "string", "total": "number"}


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_extract_ok():
    pdf = make_pdf("INVOICE INV-2043 total 1280.00")
    r = client.post(
        "/v1/extract",
        files={"file": ("invoice.pdf", pdf, "application/pdf")},
        data={"schema": json.dumps(SCHEMA)},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"data", "confidence", "pages", "warnings"}
    assert set(body["data"]) == {"invoice_number", "total"}


def test_extract_unsupported_type():
    r = client.post(
        "/v1/extract",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        data={"schema": json.dumps(SCHEMA)},
    )
    assert r.status_code == 415
    assert r.json()["error"]["type"] == "unsupported_file_type"


def test_extract_bad_schema_json():
    pdf = make_pdf("x")
    r = client.post(
        "/v1/extract",
        files={"file": ("invoice.pdf", pdf, "application/pdf")},
        data={"schema": "{not json"},
    )
    assert r.status_code == 400
