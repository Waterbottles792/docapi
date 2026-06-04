"""Free, local understanding step via Ollama (https://ollama.com).

Uses Ollama's structured-output `format` parameter: we hand it the JSON Schema derived
from the caller's pydantic model, so the model is constrained to emit matching JSON. That,
plus the pipeline's corrective retry, is what makes a small local model usable.
"""
from __future__ import annotations

import json
from typing import Any

import httpx
from pydantic import BaseModel

from ..errors import UpstreamModelError

_SYSTEM = (
    "You extract structured data from documents. "
    "Return ONLY a JSON object matching the provided schema. "
    "Use the document text as the source of truth. "
    "If a field is not present in the document, use null."
)


class OllamaUnderstander:
    def __init__(self, model: str, host: str, timeout: float = 60.0) -> None:
        self.model = model or "llama3.2"
        self.host = host.rstrip("/")
        self.timeout = timeout

    def understand(
        self, content: str, model: type[BaseModel], feedback: str | None = None
    ) -> dict:
        json_schema = model.model_json_schema()
        # Don't force the model to reformat dates to ISO — it mangles them. Let it copy the
        # date text as written; the pipeline normalises it deterministically afterwards.
        _relax_date_formats(json_schema)
        user = (
            f"Document content:\n\"\"\"\n{content}\n\"\"\"\n\n"
            "Extract the requested fields into JSON."
        )
        if feedback:
            user += (
                f"\n\nYour previous answer failed validation: {feedback}\n"
                "Correct those fields and return valid JSON only."
            )

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user},
            ],
            "format": json_schema,
            "stream": False,
            "options": {"temperature": 0},
        }

        try:
            resp = httpx.post(
                f"{self.host}/api/chat", json=payload, timeout=self.timeout
            )
            resp.raise_for_status()
        except httpx.ConnectError as exc:
            raise UpstreamModelError(
                f"Could not reach Ollama at {self.host}. Is `ollama serve` running?"
            ) from exc
        except httpx.HTTPError as exc:
            raise UpstreamModelError(f"Ollama request failed: {exc}") from exc

        text = resp.json().get("message", {}).get("content", "")
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise UpstreamModelError(
                "Ollama did not return valid JSON", raw=text[:500]
            ) from exc
        if not isinstance(parsed, dict):
            raise UpstreamModelError("Ollama returned non-object JSON", raw=text[:500])
        return parsed


def _relax_date_formats(node: Any) -> None:
    """Strip `format: date` constraints so the model returns the raw date string."""
    if isinstance(node, dict):
        if node.get("format") in ("date", "date-time"):
            node.pop("format", None)
        for value in node.values():
            _relax_date_formats(value)
    elif isinstance(node, list):
        for value in node:
            _relax_date_formats(value)
