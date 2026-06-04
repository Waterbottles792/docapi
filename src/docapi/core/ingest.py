"""Validate file type & size, count pages, detect scan-vs-digital. No model calls."""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from ..config import get_settings
from .errors import FileTooLarge, TooManyPages, UnsupportedFileType

SUPPORTED = {".pdf", ".png", ".jpg", ".jpeg"}


@dataclass
class Ingested:
    kind: str  # "pdf" | "image"
    pages: int
    is_scan: bool


def _ext(filename: str) -> str:
    return ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""


def ingest(file_bytes: bytes, filename: str) -> Ingested:
    s = get_settings()
    ext = _ext(filename)
    if ext not in SUPPORTED:
        raise UnsupportedFileType(
            f"Unsupported file type {ext!r}", supported=sorted(SUPPORTED)
        )
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > s.max_file_mb:
        raise FileTooLarge(f"File is {size_mb:.1f} MB; max is {s.max_file_mb} MB")

    if ext == ".pdf":
        pages, is_scan = _pdf_pages(file_bytes)
        if pages > s.max_pages:
            raise TooManyPages(f"Document has {pages} pages; max is {s.max_pages}")
        return Ingested(kind="pdf", pages=pages, is_scan=is_scan)
    return Ingested(kind="image", pages=1, is_scan=True)


def _pdf_pages(file_bytes: bytes) -> tuple[int, bool]:
    from pypdf import PdfReader

    try:
        reader = PdfReader(BytesIO(file_bytes))
    except Exception as exc:  # noqa: BLE001 - surface as structured error upstream
        raise UnsupportedFileType("Could not parse PDF") from exc
    pages = len(reader.pages)
    text = "".join((p.extract_text() or "") for p in reader.pages[: min(pages, 3)])
    is_scan = len(text.strip()) < 20  # crude: little extractable text => likely a scan
    return pages, is_scan
