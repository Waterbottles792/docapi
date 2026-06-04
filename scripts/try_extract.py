"""Run a real PDF through the pipeline locally, at $0.

    uv run python scripts/try_extract.py [path/to/invoice.pdf] [--ollama]

With no path it generates a tiny sample invoice PDF so you can see the full flow.
By default the free stub returns canned data (so output looks realistic). Pass --ollama
(or set LLM_PROVIDER=ollama) to do a real extraction with your local Ollama model.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from docapi.config import get_settings
from docapi.core.pipeline import extract_to_schema
from docapi.core.understand import StubUnderstander, get_understander

SCHEMA = {
    "invoice_number": "string",
    "invoice_date": "date",
    "total_amount": "number",
    "line_items": [{"description": "string", "amount": "number"}],
}

CANNED = {
    "invoice_number": "INV-2043",
    "invoice_date": "2026-05-18",
    "total_amount": 1280.00,
    "line_items": [
        {"description": "Design retainer", "amount": 1200.00},
        {"description": "Hosting", "amount": 80.00},
    ],
}


def _ollama_understander():
    from docapi.core.providers.ollama import OllamaUnderstander

    s = get_settings()
    return OllamaUnderstander(model=s.llm_model, host=s.ollama_host)


def _sample_pdf() -> bytes:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from sample_invoice import make_invoice_pdf

    return make_invoice_pdf()


def main() -> None:
    args = [a for a in sys.argv[1:] if a != "--ollama"]
    # Use a real model if --ollama is passed or LLM_PROVIDER is set to a real provider.
    real = "--ollama" in sys.argv or get_settings().llm_provider != "stub"

    if args:
        path = Path(args[0])
        file_bytes = path.read_bytes()
        filename = path.name
    else:
        print("No file given — using a generated sample invoice.\n")
        file_bytes = _sample_pdf()
        filename = "sample_invoice.pdf"

    if real:
        understander = _ollama_understander() if get_settings().llm_provider == "stub" else get_understander()
        print(f"Using real provider: ollama ({understander.model})\n")  # type: ignore[attr-defined]
    else:
        understander = StubUnderstander(CANNED)

    result = extract_to_schema(file_bytes, filename, SCHEMA, understander=understander)
    print(
        json.dumps(
            {
                "data": result.data,
                "confidence": result.confidence,
                "pages": result.pages,
                "warnings": result.warnings,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
