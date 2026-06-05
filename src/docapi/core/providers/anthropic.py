"""Paid, high-quality understanding step via the Anthropic API (Claude).

This is the only step in docapi that costs money, kept behind the same swappable seam as
the free providers. It uses Claude's structured-output `output_config.format` with the
JSON Schema derived from the caller's model, so the response is constrained to matching
JSON — exactly like the Ollama path, so validation, date repair, grounding, and chunking
all work unchanged downstream.

The API key is read from the environment (`ANTHROPIC_API_KEY`), never hard-coded. In a
self-hosted deploy that's the operator's own key; in a hosted deploy it's the service's
key — same code, both models.

Default model is Claude Haiku 4.5 (cheapest, big context, fast) — override with LLM_MODEL.
"""
from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from ..errors import UpstreamModelError
from .ollama import _relax_date_formats  # reuse: strip format:date so dates come raw

_SYSTEM = (
    "You extract structured data from documents. "
    "Return ONLY a JSON object matching the provided schema, using the document text as "
    "the source of truth — never invent values that aren't in the document. "
    "If a field is not present in the document, use null. "
    "For boolean (true/false) fields, always answer true or false based on whether the "
    "document supports it — never null. Answer false if there is no supporting evidence."
)

DEFAULT_MODEL = "claude-haiku-4-5"


class AnthropicUnderstander:
    def __init__(
        self,
        model: str,
        api_key: str,
        max_tokens: int = 8192,
        client: Any | None = None,
    ) -> None:
        self.model = model or DEFAULT_MODEL
        self.max_tokens = max_tokens
        self._api_key = api_key
        self._client = client  # injectable for tests; built lazily otherwise

    def _ensure_client(self) -> Any:
        if self._client is None:
            try:
                import anthropic
            except ImportError as exc:  # optional dependency
                raise UpstreamModelError(
                    "The 'anthropic' package is required for LLM_PROVIDER=anthropic. "
                    "Install it with:  uv pip install 'docapi[anthropic]'"
                ) from exc
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def understand(
        self, content: str, model: type[BaseModel], feedback: str | None = None
    ) -> dict:
        json_schema = model.model_json_schema()
        # Let Claude copy dates as written; the pipeline normalises them deterministically.
        _relax_date_formats(json_schema)
        # Structured outputs require additionalProperties:false on every object.
        _force_strict_objects(json_schema)

        user = (
            f'Document content:\n"""\n{content}\n"""\n\n'
            "Extract the requested fields into JSON."
        )
        if feedback:
            user += (
                f"\n\nYour previous answer failed validation: {feedback}\n"
                "Correct those fields and return valid JSON only."
            )

        client = self._ensure_client()
        try:
            resp = client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=_SYSTEM,
                messages=[{"role": "user", "content": user}],
                output_config={"format": {"type": "json_schema", "schema": json_schema}},
            )
        except Exception as exc:  # surface API/auth/rate-limit errors with context
            raise UpstreamModelError(f"Anthropic request failed: {exc}") from exc

        text = next(
            (b.text for b in resp.content if getattr(b, "type", None) == "text"), ""
        )
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise UpstreamModelError(
                "Anthropic did not return valid JSON", raw=text[:500]
            ) from exc
        if not isinstance(parsed, dict):
            raise UpstreamModelError("Anthropic returned non-object JSON", raw=text[:500])
        return parsed


def _force_strict_objects(node: Any) -> None:
    """Set additionalProperties:false on every object in the JSON Schema (incl. $defs)."""
    if isinstance(node, dict):
        if node.get("type") == "object":
            node["additionalProperties"] = False
        for value in node.values():
            _force_strict_objects(value)
    elif isinstance(node, list):
        for value in node:
            _force_strict_objects(value)
