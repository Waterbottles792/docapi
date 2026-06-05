"""Unit tests for the Anthropic provider — a fake client is injected, so no key/network."""
from __future__ import annotations

import json

import pytest

from docapi.core.errors import UpstreamModelError
from docapi.core.providers.anthropic import AnthropicUnderstander
from docapi.core.schema import build_model

MODEL = build_model(
    "M",
    {"invoice_number": "string", "invoice_date": "date", "total": "number"},
)


class _Block:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class _Resp:
    def __init__(self, text: str) -> None:
        self.content = [_Block(text)]


class _Messages:
    def __init__(self, text: str, captured: dict) -> None:
        self._text = text
        self._captured = captured

    def create(self, **kwargs):
        self._captured.update(kwargs)
        return _Resp(self._text)


class _FakeClient:
    def __init__(self, text: str) -> None:
        self.captured: dict = {}
        self.messages = _Messages(text, self.captured)


def _understander(text: str) -> tuple[AnthropicUnderstander, _FakeClient]:
    client = _FakeClient(text)
    und = AnthropicUnderstander(model="claude-haiku-4-5", api_key="sk-test", client=client)
    return und, client


def test_parses_valid_json() -> None:
    und, _ = _understander(json.dumps({"invoice_number": "INV-1", "total": 99.5}))
    assert und.understand("text", MODEL) == {"invoice_number": "INV-1", "total": 99.5}


def test_sends_structured_output_schema() -> None:
    und, client = _understander(json.dumps({"invoice_number": "INV-1"}))
    und.understand("the document text", MODEL)
    fmt = client.captured["output_config"]["format"]
    assert fmt["type"] == "json_schema"
    schema = fmt["schema"]
    # Structured outputs require additionalProperties:false on the root object.
    assert schema["additionalProperties"] is False
    # The date field's `format: date` is stripped so the date comes back as written.
    assert "format" not in schema["properties"]["invoice_date"]
    assert client.captured["model"] == "claude-haiku-4-5"


def test_includes_document_and_system() -> None:
    und, client = _understander(json.dumps({"invoice_number": "X"}))
    und.understand("HELLO-DOC-TEXT", MODEL)
    assert "HELLO-DOC-TEXT" in client.captured["messages"][0]["content"]
    assert "extract structured data" in client.captured["system"].lower()


def test_feedback_is_appended_on_retry() -> None:
    und, client = _understander(json.dumps({"invoice_number": "X"}))
    und.understand("doc", MODEL, feedback="total: field required")
    assert "failed validation" in client.captured["messages"][0]["content"]
    assert "total: field required" in client.captured["messages"][0]["content"]


def test_non_json_raises_upstream() -> None:
    und, _ = _understander("I'm sorry, I can't do that")
    with pytest.raises(UpstreamModelError):
        und.understand("doc", MODEL)


def test_non_object_json_raises_upstream() -> None:
    und, _ = _understander(json.dumps(["not", "an", "object"]))
    with pytest.raises(UpstreamModelError):
        und.understand("doc", MODEL)


def test_api_failure_is_wrapped() -> None:
    class _Boom:
        def create(self, **kwargs):
            raise RuntimeError("401 authentication_error")

    client = _FakeClient("")
    client.messages = _Boom()
    und = AnthropicUnderstander("claude-haiku-4-5", "sk-test", client=client)
    with pytest.raises(UpstreamModelError, match="Anthropic request failed"):
        und.understand("doc", MODEL)


class _Settings:
    llm_provider = "anthropic"
    anthropic_api_key = ""
    llm_model = ""
    ollama_host = "http://x"
    request_timeout_seconds = 60


def test_get_understander_requires_key(monkeypatch) -> None:
    from docapi.core import understand as u

    monkeypatch.setattr(u, "get_settings", lambda: _Settings())
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        u.get_understander()


def test_get_understander_builds_anthropic(monkeypatch) -> None:
    from docapi.core import understand as u

    s = _Settings()
    s.anthropic_api_key = "sk-x"
    s.llm_model = "claude-haiku-4-5"
    monkeypatch.setattr(u, "get_settings", lambda: s)
    und = u.get_understander()
    assert isinstance(und, AnthropicUnderstander)
    assert und.model == "claude-haiku-4-5"


def test_missing_sdk_is_friendly() -> None:
    # No client injected and the package import fails -> a clear, actionable error.
    und = AnthropicUnderstander("claude-haiku-4-5", "sk-test")
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "anthropic":
            raise ImportError("No module named 'anthropic'")
        return real_import(name, *args, **kwargs)

    builtins.__import__ = fake_import
    try:
        with pytest.raises(UpstreamModelError, match="docapi\\[anthropic\\]"):
            und.understand("doc", MODEL)
    finally:
        builtins.__import__ = real_import
