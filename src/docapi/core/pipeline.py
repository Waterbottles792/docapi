"""THE core. One entry point shared by the REST handler and (later) the MCP tool.

    ingest -> acquire text -> understand -> validate (+1 retry) -> score
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from .chunking import CHUNK_CHARS, merge_partials, split_text
from .dates import normalize_dates
from .errors import ValidationFailed
from .extractors import extract_text
from .grounding import find_ungrounded
from .ingest import ingest
from .schema import build_model, make_all_optional
from .understand import Understander, get_understander
from .validate import validate


@dataclass
class ExtractResult:
    data: dict[str, Any]
    confidence: float
    pages: int
    warnings: list[str] = field(default_factory=list)


def extract_to_schema(
    file_bytes: bytes,
    filename: str,
    schema: dict,
    options: dict | None = None,
    understander: Understander | None = None,
) -> ExtractResult:
    options = options or {}
    understander = understander or get_understander()
    model = build_model("Extracted", schema)

    info = ingest(file_bytes, filename)
    warnings: list[str] = []

    ocr_mode = options.get("ocr", "auto")
    content = extract_text(file_bytes, info.kind)
    if info.is_scan or ocr_mode == "force" or (ocr_mode != "off" and len(content) < 20):
        # OCR fallback lands in Phase 2; note it rather than failing silently.
        warnings.append("ocr_fallback_not_available_in_this_build")

    # Long docs blow past a small model's context window and get silently truncated, so
    # split them into windows, extract each, and merge. Short docs take the direct path.
    chunks = split_text(content) if len(content) > CHUNK_CHARS else [content]
    if len(chunks) > 1:
        warnings.append(f"long_document_chunked_into_{len(chunks)}_windows")
        obj, fields, raw = _extract_chunked(understander, chunks, model)
    else:
        obj, fields, raw = _extract_single(understander, content, model)

    if obj is None:
        partial = {k: v for k, v in raw.items() if k not in fields}
        raise ValidationFailed(
            f"Output did not match schema. Problem fields: {', '.join(fields)}",
            fields=fields,
            partial_data=partial,
        )

    data = obj.model_dump(mode="json")
    confidence = _confidence(obj, model)

    # Grounding: flag any string the model returned that isn't in the source text.
    # Schema validation guarantees shape, not truth — this guards against hallucination
    # (and surfaces silent context-window truncation, where late-page values go missing).
    if options.get("grounding", "on") != "off":
        ungrounded = find_ungrounded(data, model, content)
        if ungrounded:
            warnings.append(
                "ungrounded_fields (not found in source text, possibly hallucinated): "
                + ", ".join(ungrounded)
            )
            confidence = round(max(0.1, confidence - 0.25 * len(ungrounded)), 2)

    return ExtractResult(
        data=data,
        confidence=confidence,
        pages=info.pages,
        warnings=warnings,
    )


def _extract_single(
    understander: Understander, content: str, model: type[BaseModel]
) -> tuple[Any, list[str], dict]:
    """Understand + validate, with one corrective retry feeding errors back to the model."""
    obj = None
    fields: list[str] = []
    raw: dict = {}
    feedback: str | None = None
    for _ in range(2):
        raw = understander.understand(content, model, feedback)
        normalize_dates(raw, model)  # deterministic date repair before validation
        obj, fields, feedback = validate(raw, model)
        if obj is not None:
            break
    return obj, fields, raw


def _extract_chunked(
    understander: Understander, chunks: list[str], model: type[BaseModel]
) -> tuple[Any, list[str], dict]:
    """Extract each window against an all-optional schema, then merge + validate strictly.

    The relaxed schema lets a window legitimately return null for fields it doesn't
    contain, instead of being forced by structured output to fabricate them.
    """
    relaxed = make_all_optional(model)
    partials: list[dict] = []
    for chunk in chunks:
        raw = understander.understand(chunk, relaxed)
        normalize_dates(raw, relaxed)
        obj, _, _ = validate(raw, relaxed)
        if obj is not None:
            partials.append(obj.model_dump(mode="json"))
    merged = merge_partials(partials, model)
    obj, fields, _ = validate(merged, model)
    return obj, fields, merged


def _confidence(obj: Any, model: type[BaseModel]) -> float:
    """Start simple: how many fields came back populated. Refine from eval data later."""
    names = list(model.model_fields)
    total = len(names) or 1
    present = sum(1 for n in names if getattr(obj, n) not in (None, "", [], 0))
    return round(0.5 + 0.5 * present / total, 2)
