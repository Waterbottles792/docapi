"""The understanding step: map extracted content + target schema -> structured data.

This is the ONLY paid step in the product, so it sits behind a swappable seam. The
default `stub` provider costs $0 and needs no network — flip LLM_PROVIDER to wire in a
real model (Anthropic Claude, or a free local model via Ollama) without touching the
pipeline.
"""
from __future__ import annotations

import datetime
import typing
from typing import Protocol

from pydantic import BaseModel

from ..config import get_settings


class Understander(Protocol):
    def understand(
        self, content: str, model: type[BaseModel], feedback: str | None = None
    ) -> dict: ...


class StubUnderstander:
    """Deterministic stand-in for the LLM.

    Returns injected `canned` data when provided (pass a list to simulate a bad-then-good
    retry), otherwise emits schema-shaped placeholders so the whole pipeline runs at $0.
    Replace with a real provider for actual extraction quality.
    """

    def __init__(self, canned: dict | list[dict] | None = None) -> None:
        if canned is None:
            self._responses: list[dict] = []
        elif isinstance(canned, list):
            self._responses = canned
        else:
            self._responses = [canned]
        self._i = 0

    def understand(
        self, content: str, model: type[BaseModel], feedback: str | None = None
    ) -> dict:
        if self._responses:
            resp = self._responses[min(self._i, len(self._responses) - 1)]
            self._i += 1
            return dict(resp)
        return {n: _value_for(f.annotation) for n, f in model.model_fields.items()}


def _value_for(annotation: typing.Any) -> typing.Any:
    """A type-appropriate placeholder so stub output always validates."""
    origin = typing.get_origin(annotation)
    if origin in (list, typing.List):  # noqa: UP006
        return []
    if origin is typing.Union:  # Optional[...] -> None is valid
        return None
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return {n: _value_for(f.annotation) for n, f in annotation.model_fields.items()}
    return {
        str: "",
        int: 0,
        float: 0.0,
        bool: False,
        datetime.date: datetime.date.today(),
    }.get(annotation, None)


def get_understander() -> Understander:
    s = get_settings()
    provider = s.llm_provider
    if provider == "stub":
        return StubUnderstander()
    if provider == "ollama":
        from .providers.ollama import OllamaUnderstander

        return OllamaUnderstander(
            model=s.llm_model,
            host=s.ollama_host,
            timeout=float(s.request_timeout_seconds),
        )
    if provider == "anthropic":
        if not s.anthropic_api_key:
            raise ValueError(
                "LLM_PROVIDER=anthropic requires ANTHROPIC_API_KEY to be set."
            )
        from .providers.anthropic import AnthropicUnderstander

        return AnthropicUnderstander(model=s.llm_model, api_key=s.anthropic_api_key)
    raise ValueError(f"Unknown LLM_PROVIDER {provider!r}")
