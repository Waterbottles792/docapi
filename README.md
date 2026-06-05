<h1 align="center">docapi</h1>

<p align="center">
  <b>Reliable document extraction for AI agents.</b><br>
  Give it a file + the fields you want → get back JSON guaranteed to match your schema, or a precise error.
</p>

<p align="center">
  <i>Stripe-for-documents, built agent-native — REST API + MCP. Runs 100% local & free.</i>
</p>

<p align="center">
  <img alt="Python 3.11+" src="https://img.shields.io/badge/python-3.11%2B-blue">
  <img alt="tests" src="https://img.shields.io/badge/tests-57%20passing-brightgreen">
  <img alt="typed" src="https://img.shields.io/badge/mypy-clean-brightgreen">
  <img alt="cost" src="https://img.shields.io/badge/runs-%240%20local-success">
  <img alt="license" src="https://img.shields.io/badge/license-Apache--2.0-blue">
</p>

<!-- 📹 Drop your demo GIF here once recorded:
<p align="center"><img src="docs/demo.gif" alt="docapi demo" width="700"></p>
-->

---

## Why

AI agents are impressive — until a real-world PDF hits them: a scanned invoice, a receipt, a messy form. They hallucinate, return half-broken data, or fail silently.

**The hard part was never the model. It's reliability on messy inputs.** That's what docapi is.

Every response is validated against *your* schema. If it can't match, you get a structured error — **never silently-wrong data.**

## What it does

```
messy file  ──►  ingest → extract → understand → validate → normalize  ──►  schema-shaped JSON
```

A real example — an Indian receipt with a `DD-MM-YYYY` date that trips up language models:

<table>
<tr><th>In (PDF text)</th><th>You ask for</th><th>Out (guaranteed valid)</th></tr>
<tr>
<td><pre>Payment ID: pay_S6lDhbqEbjQ6Bs
Payment Date: 26-05-2025
Course Fee: Rs. 1000</pre></td>
<td><pre>{
  "invoice_number": "string",
  "invoice_date": "date",
  "total_amount": "number"
}</pre></td>
<td><pre>{
  "invoice_number": "pay_S6lDhbqEbjQ6Bs",
  "invoice_date": "2025-05-26",
  "total_amount": 1000.0
}</pre></td>
</tr>
</table>

> The model alone reads `26-05-2025` as the year **2605**. docapi fixes it deterministically —
> dates are a solved problem in code, so we don't make the model guess. *Reliability is the product.*

## Quickstart

```bash
uv venv && uv pip install -e ".[dev]"

# See it run instantly (free stub, no model needed)
uv run python scripts/demo.py --stub

# Real extraction with a free local model (see Ollama below)
uv run python scripts/demo.py
uv run python scripts/try_extract.py path/to/your.pdf --ollama

# Or run the API + interactive docs
uv run uvicorn docapi.main:app --reload   # http://127.0.0.1:8000/docs
curl -s -F 'file=@invoice.pdf' \
     -F 'schema={"invoice_number":"string","total":"number"}' \
     http://127.0.0.1:8000/v1/extract | jq
```

## Agent-native: the MCP server

The same pipeline is exposed as an [MCP](https://modelcontextprotocol.io) tool, so an AI
agent can extract documents directly — no HTTP glue. Point Claude Desktop (or any MCP
client) at it:

```jsonc
// claude_desktop_config.json
{
  "mcpServers": {
    "docapi": {
      "command": "uv",
      "args": ["run", "python", "-m", "docapi.mcp_server"],
      "cwd": "/absolute/path/to/document_api_playbook"
    }
  }
}
```

Then just ask: *"Extract the invoice number, date, and total from ~/receipt.pdf."* The agent
calls the `extract_document` tool and gets back schema-valid JSON — or a structured error.
REST and MCP are two faces of the **exact same** `extract_to_schema` core.

## Free & local with Ollama

No API key, no cloud, no cost:

```bash
ollama pull llama3.2          # ~2 GB, free
export LLM_PROVIDER=ollama LLM_MODEL=llama3.2
```

docapi hands Ollama the JSON Schema derived from your model, so a small local model is
*constrained* to emit schema-matching JSON. Combined with one corrective retry + deterministic
date repair, even a 3B model extracts invoices reliably.

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

## The understand step is swappable

The only step that could cost money sits behind one env var:

| `LLM_PROVIDER` | Cost | Notes |
|---|---|---|
| `stub` (default) | $0 | placeholders — proves the plumbing |
| `ollama` | $0 | real extraction, fully local |
| `anthropic` | paid | highest quality (Claude Haiku is cheapest) — *seam ready, not wired* |

## Reliability engine

- ✅ **Schema validation** on every output — never returns the wrong shape
- ✅ **Grounding check** — every extracted string is verified against the source text; anything the model *invented* is flagged and confidence drops (catches hallucination, and surfaces silent context-window truncation on long docs)
- ✅ **One corrective retry** feeding errors back to the model
- ✅ **Deterministic date normalization** (no more `2605` bugs)
- ✅ **Structured errors** with stable `type` + human message
- ✅ **Confidence signal** on every success
- ⏳ OCR fallback for scans — *next*

## Does it actually work? (eval harness)

Tests prove the plumbing; the eval harness measures whether the pipeline returns the
**correct values** on real documents — scoring each output field-by-field against a
known-correct answer.

```bash
LLM_PROVIDER=ollama LLM_MODEL=llama3.2 uv run python scripts/eval.py
#  ✓ acme_invoice    3/3 fields
#  ✓ euro_invoice    3/3 fields    (slash-format date)
#  ✓ nptel_receipt   3/3 fields    (the 2605 date case)
#  ✓ resume          13/13 fields  (lists + nested objects, not an invoice)
#  field accuracy: 100% (22/22 across 4 docs)
```

On the starter set, **100% field accuracy (22/22) on a free 3B local model** — across flat
invoices *and* a résumé with skill lists, nested job history, and an experience count
inferred from prose. That's a small, directional set — see [`evals/`](./evals) to grow it.
The harness doubles as a regression gate: `--threshold 0.85` makes it exit non-zero if
accuracy slips.

## Status & roadmap

Early, but **working end-to-end today**: core pipeline + REST API + MCP server + reliability layer + eval harness + 57 tests.

- [x] Extract-to-schema pipeline (REST `POST /v1/extract`)
- [x] Free local model (Ollama) + deterministic date repair
- [x] MCP `extract_document` tool (same pipeline, agent-native)
- [x] Eval harness with field-level accuracy + regression gate
- [ ] OCR fallback for scanned docs
- [ ] Auth, usage metering, deploy

See [`SPEC.md`](./SPEC.md) for the full v1 spec.

## Develop

```bash
uv run pytest        # 57 tests
uv run ruff check .
uv run mypy src
LLM_PROVIDER=ollama uv run python scripts/eval.py   # accuracy on real docs
```

## License & commercial use

Open source under the **[Apache-2.0](./LICENSE)** license — use it, self-host it, build on it.

A managed, hosted version (an API key instead of a local model, plus auth, usage metering,
and scale) is on the way — the open core here is the same engine that will power it. If you'd
like early access or want to talk integration, open an issue or reach out.

---

<p align="center"><i>Building in public. Issues, ideas, and DMs welcome.</i></p>
