"""Deterministic text extraction. Do as much here as possible to minimise model use."""
from __future__ import annotations

from io import BytesIO


def extract_text(file_bytes: bytes, kind: str) -> str:
    if kind == "pdf":
        return _pdf_text(file_bytes)
    return ""  # images are handled by the OCR fallback (Phase 2)


def _pdf_text(file_bytes: bytes) -> str:
    import pdfplumber

    parts: list[str] = []
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()
