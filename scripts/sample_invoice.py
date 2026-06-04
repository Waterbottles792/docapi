"""Generate a realistic, text-based invoice PDF for demos and tests (uses reportlab)."""
from __future__ import annotations

from io import BytesIO


def make_invoice_pdf() -> bytes:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    y = 740
    lines = [
        "ACME Studio",
        "",
        "INVOICE",
        "Invoice Number: INV-2043",
        "Invoice Date: 2026-05-18",
        "",
        "Description                 Amount",
        "Design retainer             1200.00",
        "Hosting                       80.00",
        "",
        "Total Amount: 1280.00",
    ]
    for line in lines:
        c.drawString(72, y, line)
        y -= 18
    c.showPage()
    c.save()
    return buf.getvalue()


if __name__ == "__main__":
    from pathlib import Path

    out = Path("sample_invoice.pdf")
    out.write_bytes(make_invoice_pdf())
    print(f"wrote {out.resolve()}")
