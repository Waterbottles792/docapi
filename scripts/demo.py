"""A screen-recordable demo of docapi: messy document in -> clean schema-valid JSON out.

    uv run python scripts/demo.py            # uses free local Ollama (llama3.2)
    uv run python scripts/demo.py --stub     # offline, instant (canned), for a quick capture
"""
from __future__ import annotations

import json
import sys
import time
from io import BytesIO

from docapi.core.pipeline import extract_to_schema
from docapi.core.understand import StubUnderstander

C = {
    "cyan": "\033[36m", "green": "\033[32m", "yellow": "\033[33m",
    "dim": "\033[2m", "bold": "\033[1m", "reset": "\033[0m", "mag": "\033[35m",
}


def c(text: str, color: str) -> str:
    return f"{C[color]}{text}{C['reset']}"


RECEIPT_LINES = [
    "NPTEL Online Certification",
    "Payment Receipt",
    "",
    "Payment ID: pay_S6lDhbqEbjQ6Bs",
    "Payment Date: 26-05-2025",
    "Course Fee: Rs. 1000",
    "Status: Captured",
]

SCHEMA = {
    "invoice_number": "string",
    "invoice_date": "date",
    "total_amount": "number",
}


def _receipt_pdf() -> bytes:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    buf = BytesIO()
    cv = canvas.Canvas(buf, pagesize=letter)
    y = 740
    for line in RECEIPT_LINES:
        cv.drawString(72, y, line)
        y -= 18
    cv.showPage()
    cv.save()
    return buf.getvalue()


def _slow_print(text: str = "", delay: float = 0.0) -> None:
    print(text)
    if delay:
        time.sleep(delay)


def main() -> None:
    stub = "--stub" in sys.argv
    print()
    _slow_print(c("  docapi", "bold") + c("  ·  reliable document extraction for AI agents", "dim"), 0.4)
    _slow_print(c("  ────────────────────────────────────────────────────────", "dim"), 0.4)
    print()

    _slow_print(c("  📄 INPUT", "cyan") + c("  — a messy real-world receipt (PDF)", "dim"), 0.3)
    for line in RECEIPT_LINES:
        if line:
            tag = c("   ← Indian DD-MM-YYYY date", "yellow") if "Payment Date" in line else ""
            _slow_print("     " + c(line, "dim") + tag, 0.05)
    print()

    _slow_print(c("  🎯 YOU ASK FOR", "cyan") + c("  — just describe the fields you want:", "dim"), 0.3)
    for ln in json.dumps(SCHEMA, indent=2).splitlines():
        _slow_print("     " + c(ln, "mag"), 0.04)
    print()

    _slow_print(c("  ⚙️  docapi", "cyan") + c("  ingest → extract → understand → validate → normalize", "dim"), 0.3)
    src = "stub (offline)" if stub else "llama3.2 (free, 100% local)"
    _slow_print(c(f"     running on {src} …", "dim"), 0.2)
    print()

    t0 = time.time()
    if stub:
        understander = StubUnderstander(
            {"invoice_number": "pay_S6lDhbqEbjQ6Bs", "invoice_date": "26-05-2025", "total_amount": 1000}
        )
    else:
        from docapi.core.providers.ollama import OllamaUnderstander

        understander = OllamaUnderstander(model="llama3.2", host="http://localhost:11434", timeout=180)

    result = extract_to_schema(_receipt_pdf(), "receipt.pdf", SCHEMA, understander=understander)
    dt = time.time() - t0

    _slow_print(c("  ✅ OUT", "green") + c("  — JSON guaranteed to match your schema:", "dim"), 0.3)
    for ln in json.dumps(result.data, indent=2).splitlines():
        tag = c("   ← normalized from 26-05-2025", "yellow") if "2025-05-26" in ln else ""
        _slow_print("     " + c(ln, "green") + tag, 0.05)
    print()
    _slow_print(
        c(f"     confidence {result.confidence}  ·  {result.pages} page  ·  {dt:.1f}s  ·  $0  ·  no API key", "dim"),
        0.2,
    )
    print()
    _slow_print(c("  Same pipeline ships as a REST API and an MCP tool your agent can call.", "dim"))
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()  # exit cleanly on Ctrl-C instead of dumping a traceback
