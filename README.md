# docapi — Document API for AI agents (v1 slice)

Send a **document + a schema**, get back **JSON that validates against that schema** plus a
confidence signal — or a precise structured error. This repo is the first vertical slice:
the core extraction pipeline behind `POST /v1/extract`, running at **$0** with a stub model.

> Full spec: `SPEC.md`. What's built so far: ingest → text extraction → understand (stub) →
> validate (+1 retry) → confidence, exposed over REST. Not yet built: real LLM/OCR, auth,
> database, metering, MCP (see "Next" below).

## Quickstart

```bash
uv venv && uv pip install -e ".[dev]"

# 1. See the pipeline on a generated sample invoice with the free stub (placeholders)
uv run python scripts/try_extract.py

# 2. REAL extraction with a free local model (needs Ollama, see below)
uv run python scripts/try_extract.py --ollama
uv run python scripts/try_extract.py path/to/your.pdf --ollama

# 3. Run the API
uv run uvicorn docapi.main:app --reload
#    -> http://127.0.0.1:8000/docs   (interactive OpenAPI)
#    -> GET /healthz

# 4. Call extract over HTTP (set LLM_PROVIDER=ollama for real answers)
curl -s -F 'file=@invoice.pdf' \
     -F 'schema={"invoice_number":"string","total":"number"}' \
     http://127.0.0.1:8000/v1/extract | jq
```

## Free local model with Ollama

```bash
# one-time setup
ollama serve            # if not already running
ollama pull llama3.2    # ~2 GB, free

# point docapi at it
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.2
```

The provider hands Ollama the JSON Schema derived from your pydantic model (`format`
parameter), so the local model is constrained to emit schema-matching JSON. Combined with
the pipeline's one corrective retry, even a small 3B model extracts invoices reliably.

## The schema format

Map field names to types. Append `?` for optional. Arrays are `[ {item} ]`; nest objects freely.

```json
{
  "vendor_name": "string",
  "document_date": "date",
  "total": "number",
  "tax_id": "string?",
  "line_items": [ { "description": "string", "amount": "number" } ]
}
```

Supported scalars: `string`, `number`, `integer`, `boolean`, `date` (ISO-8601).

## How it costs $0

The only paid step is "understand" (content + schema → JSON). It sits behind a swappable seam
(`core/understand.py`):

| `LLM_PROVIDER` | Cost | Notes |
|---|---|---|
| `stub` (default) | $0 | placeholders only — proves the plumbing, no real reading |
| `ollama` | $0 | real extraction with a free local model |
| `anthropic` | paid | not wired yet; best quality (Claude Haiku is cheapest) |

Switching providers changes one env var; nothing else in the pipeline changes.

## Develop

```bash
uv run pytest          # 15 tests
uv run ruff check .
uv run mypy src
```

## Next (per SPEC.md)

- ✅ Free local model via **Ollama** wired in.
- OCR fallback (tesseract) for scans — Phase 2.
- REST hardening: API keys, rate limiting, usage metering, Postgres — Phase 3.
- MCP `extract_document` tool calling the same pipeline — Phase 4.
- Eval harness with real invoice fixtures + accuracy gate — Phase 5.
