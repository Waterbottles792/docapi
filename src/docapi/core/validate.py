"""Validate model output against the caller's schema; surface fields + feedback for retry."""
from __future__ import annotations

from pydantic import BaseModel, ValidationError


def validate(
    data: dict, model: type[BaseModel]
) -> tuple[BaseModel | None, list[str], str]:
    """Return (validated_obj | None, failing_top_level_fields, feedback_for_model)."""
    try:
        return model.model_validate(data), [], ""
    except ValidationError as exc:
        fields = sorted({str(e["loc"][0]) for e in exc.errors() if e["loc"]})
        feedback = "; ".join(
            f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors()
        )
        return None, fields, feedback
