"""Generate the reproducible PDF fixtures used by the eval harness.

Run once (or whenever you tweak a fixture):

    uv run python evals/generate_fixtures.py

Each fixture deliberately exercises something real-world and tricky (Indian DD-MM-YYYY
dates, slash dates, line items). The expected answers live next to them in evals/cases/.
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

FIXTURES = Path(__file__).parent / "fixtures"

DOCS: dict[str, list[str]] = {
    # The original date-fix case: DD-MM-YYYY that a raw model reads as the year 2605.
    "nptel_receipt.pdf": [
        "NPTEL Online Certification",
        "Payment Receipt",
        "",
        "Payment ID: pay_S6lDhbqEbjQ6Bs",
        "Payment Date: 26-05-2025",
        "Course Fee: Rs. 1000",
        "Status: Captured",
    ],
    # A cleaner invoice with an ISO date and line items.
    "acme_invoice.pdf": [
        "ACME Corporation",
        "INVOICE",
        "",
        "Invoice Number: INV-2024-042",
        "Invoice Date: 2024-03-15",
        "Bill To: Globex Inc.",
        "",
        "Line Items:",
        "  Widget Pro   x2    $1500.00",
        "  Setup Fee    x1    $250.00",
        "",
        "Total Due: $3250.00",
    ],
    # Slash-format DD/MM/YYYY — ambiguous to a model, deterministic to us.
    "euro_invoice.pdf": [
        "Lumen Ltd.",
        "Tax Invoice",
        "",
        "Invoice No: LUM-9981",
        "Date: 03/04/2021",
        "Amount Payable: EUR 780.50",
    ],
    # A totally different document shape: a resume. Exercises lists (skills, jobs),
    # nested objects, an integer pulled from prose, and an optional field.
    "resume.pdf": [
        "JANE DOE",
        "Senior Backend Engineer",
        "",
        "Email: jane.doe@example.com",
        "Phone: +1 415 555 0132",
        "Location: San Francisco, CA",
        "",
        "SUMMARY",
        "8 years building distributed systems and payment APIs.",
        "",
        "SKILLS",
        "Python, Go, PostgreSQL, Kubernetes, gRPC",
        "",
        "EXPERIENCE",
        "Staff Engineer, Globex Corp (2021 - Present)",
        "Senior Engineer, Initech (2017 - 2021)",
        "",
        "EDUCATION",
        "B.S. Computer Science, MIT, 2015",
    ],
}


def _write_pdf(path: Path, lines: list[str]) -> None:
    cv = canvas.Canvas(str(path), pagesize=letter)
    y = 740
    for line in lines:
        cv.drawString(72, y, line)
        y -= 18
    cv.showPage()
    cv.save()


def main() -> None:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    for name, lines in DOCS.items():
        _write_pdf(FIXTURES / name, lines)
        print(f"wrote {FIXTURES / name}")


if __name__ == "__main__":
    main()
