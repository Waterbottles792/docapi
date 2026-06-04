"""MCP server — exposes the same extraction pipeline as an agent-callable tool.

This is the "agent-native" half of docapi: an AI agent (Claude Desktop, etc.) connects
over MCP and calls `extract_document` directly, instead of you wiring up an HTTP client.
It reuses `extract_to_schema` verbatim — the REST API and this tool are two faces of the
exact same core.

Run it::

    uv run python -m docapi.mcp_server          # stdio transport (for Claude Desktop)

Claude Desktop config (claude_desktop_config.json)::

    {
      "mcpServers": {
        "docapi": {
          "command": "uv",
          "args": ["run", "python", "-m", "docapi.mcp_server"],
          "cwd": "/absolute/path/to/document_api_playbook"
        }
      }
    }
"""
from __future__ import annotations

import base64
import binascii
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .core.errors import DocApiError
from .core.pipeline import extract_to_schema

mcp = FastMCP("docapi")


def run_extract(
    schema: dict[str, Any],
    path: str | None = None,
    content_base64: str | None = None,
    filename: str | None = None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Pure function behind the tool — load bytes, run the pipeline, shape the result.

    Returns either ``{"data", "confidence", "pages", "warnings"}`` on success or
    ``{"error": {"type", "message", ...}}`` on a known failure. Never raises for an
    expected error, so the agent always gets clean, structured feedback.
    """
    try:
        file_bytes, name = _load_bytes(path, content_base64, filename)
    except ValueError as exc:
        return {"error": {"type": "bad_request", "message": str(exc)}}

    try:
        result = extract_to_schema(file_bytes, name, schema, options or {})
    except DocApiError as exc:
        return exc.to_dict()
    except ValueError as exc:  # bad schema shape
        return {"error": {"type": "bad_request", "message": str(exc)}}

    return {
        "data": result.data,
        "confidence": result.confidence,
        "pages": result.pages,
        "warnings": result.warnings,
    }


def _load_bytes(
    path: str | None, content_base64: str | None, filename: str | None
) -> tuple[bytes, str]:
    if path and content_base64:
        raise ValueError("Provide either `path` or `content_base64`, not both.")
    if path:
        p = Path(path).expanduser()
        if not p.is_file():
            raise ValueError(f"No file at path: {p}")
        return p.read_bytes(), filename or p.name
    if content_base64:
        try:
            data = base64.b64decode(content_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError(f"content_base64 is not valid base64: {exc}") from exc
        return data, filename or "upload"
    raise ValueError("Provide a document via `path` or `content_base64`.")


@mcp.tool()
def extract_document(
    schema: dict[str, Any],
    path: str | None = None,
    content_base64: str | None = None,
    filename: str | None = None,
    options: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract structured data from a document into JSON guaranteed to match your schema.

    Give a document (a local file `path`, or `content_base64` for inline bytes) and a
    `schema` describing the fields you want. Returns JSON validated against that schema
    plus a confidence score — or a structured error explaining why it couldn't, never
    silently-wrong data.

    Args:
        schema: Field-name -> type map. Types: string, number, integer, boolean, date.
            Append `?` for optional; `[ {..} ]` for arrays; `{..}` for nested objects.
            Example: {"invoice_number": "string", "invoice_date": "date", "total": "number"}
        path: Path to a local document (.pdf, .png, .jpg, .jpeg).
        content_base64: Alternative to `path` — the document bytes, base64-encoded.
        filename: Optional name (used to detect file type when passing base64).
        options: Optional, e.g. {"ocr": "auto"}.

    Returns:
        On success: {"data": {...}, "confidence": float, "pages": int, "warnings": [...]}.
        On failure: {"error": {"type": str, "message": str, ...}}.
    """
    return run_extract(schema, path, content_base64, filename, options)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
