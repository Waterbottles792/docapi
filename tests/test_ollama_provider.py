"""Unit tests for the Ollama provider — mocked, so they need no running server."""
from __future__ import annotations

import json

import httpx
import pytest

from docapi.core.errors import UpstreamModelError
from docapi.core.providers.ollama import OllamaUnderstander
from docapi.core.schema import build_model

MODEL = build_model("M", {"invoice_number": "string", "total": "number"})


def _mock_post(monkeypatch, *, content: str):
    def fake_post(url, json=None, timeout=None):  # noqa: A002
        return httpx.Response(
            200,
            json={"message": {"content": content}},
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr("docapi.core.providers.ollama.httpx.post", fake_post)


def test_parses_valid_json(monkeypatch):
    _mock_post(monkeypatch, content=json.dumps({"invoice_number": "INV-1", "total": 99.5}))
    out = OllamaUnderstander("llama3.2", "http://x").understand("text", MODEL)
    assert out == {"invoice_number": "INV-1", "total": 99.5}


def test_non_json_raises_upstream(monkeypatch):
    _mock_post(monkeypatch, content="sorry I cannot do that")
    with pytest.raises(UpstreamModelError):
        OllamaUnderstander("llama3.2", "http://x").understand("text", MODEL)


def test_connect_error_is_friendly(monkeypatch):
    def boom(url, json=None, timeout=None):  # noqa: A002
        raise httpx.ConnectError("refused", request=httpx.Request("POST", url))

    monkeypatch.setattr("docapi.core.providers.ollama.httpx.post", boom)
    with pytest.raises(UpstreamModelError, match="ollama serve"):
        OllamaUnderstander("llama3.2", "http://x").understand("text", MODEL)
