"""THE core. One entry point shared by the REST handler and (later) the MCP tool.

    ingest -> acquire text -> understand -> validate (+1 retry) -> score
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from .dates import normalize_dates
from .errors import ValidationFailed
from .extractors import extract_text
from .grounding import find_ungrounded
from .ingest import ingest
from .schema import build_model
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

    # understand + validate, with one corrective retry feeding errors back to the model.
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

    if obj is None:
        partial = {k: v for k, v in raw.items() if k not in fields}
        raise ValidationFailed(
            f"Output did not match schema after retry. Problem fields: {', '.join(fields)}",
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


def _confidence(obj: Any, model: type[BaseModel]) -> float:
    """Start simple: how many fields came back populated. Refine from eval data later."""
    names = list(model.model_fields)
    total = len(names) or 1
    present = sum(1 for n in names if getattr(obj, n) not in (None, "", [], 0))
    return round(0.5 + 0.5 * present / total, 2)
