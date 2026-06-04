"""Shared test helpers: a real (reportlab-backed) one-page PDF generator."""
from __future__ import annotations

from io import BytesIO

import pytest


def make_pdf(text: str) -> bytes:
    """A genuine, pdfplumber-readable one-page PDF with each whitespace-token on its line."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    y = 740
    for line in text.splitlines() or [text]:
        c.drawString(72, y, line)
        y -= 18
    c.showPage()
    c.save()
    return buf.getvalue()


@pytest.fixture
def sample_pdf() -> bytes:
    return make_pdf("INVOICE\nInvoice Number: INV-2043\nInvoice Date: 2026-05-18\nTotal: 1280.00")
