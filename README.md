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
  <img alt="tests" src="https://img.shields.io/badge/tests-80%20passing-brightgreen">
  <img alt="typed" src="https://img.shields.io/badge/mypy-clean-brightgreen">
  <img alt="cost" src="https://img.shields.io/badge/runs-%240%20local-success">
  <img alt="license" src="https://img.shields.io/badge/license-Apache--2.0-blue">
</p>

<p align="center">
  🌐 <b><a href="https://docapi-one.vercel.app">Live site &amp; demo</a></b> &nbsp;·&nbsp; want the hosted version (no setup, just an API key)? <b><a href="https://docapi-one.vercel.app">Join the waitlist →</a></b>
</p>

---

## Why

AI agents are impressive — until a real-world PDF hits them: a scanned invoice, a receipt, a messy form. They hallucinate, return half-broken data, or fail silently.

**The hard part was never the model. It's reliability on messy inputs.** That's what docapi is.

Every response is validated against *your* schema. If it can't match, you get a structured error — **never silently-wrong data.**

## What it does

```
messy file  ──►  ingest → extract → understand → validate → normalize → ground  ──►  schema-shaped JSON
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

---

## 1. Install

You need **Python 3.11+**. [`uv`](https://docs.astral.sh/uv/) is recommended (fast), but plain `pip` works too.

```bash
git clone https://github.com/Waterbottles792/docapi.git
cd docapi

# with uv (recommended)
uv venv
uv pip install -e .

# …or with plain pip
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

Want to verify it installed? Run the offline demo — it needs no model and no key:

```bash
uv run python scripts/demo.py --stub      # (or: python scripts/demo.py --stub)
```

---

## 2. Pick how the "understand" step runs

docapi does everything deterministically **except** one step — *understand*, where a model maps
messy text onto your fields. That single step is swappable behind one env var, `LLM_PROVIDER`:

| `LLM_PROVIDER` | Needs a key? | Cost | Best for |
|---|---|---|---|
| `stub` *(default)* | no | $0 | kicking the tires — returns canned data, proves the plumbing |
| `ollama` | no | $0 | **real extraction, 100% local & private** |
| `anthropic` | yes (your Claude key) | paid | **speed + quality**, big context, long documents |

Choose your path below. 👇

### 🟢 If you DON'T have an API key — run it free & local with Ollama

This is the recommended way to use docapi for free. It runs a small model on your own machine — no cloud, no cost, nothing leaves your computer.

```bash
# 1. Install Ollama:  https://ollama.com/download
# 2. Pull a small model (~2 GB, one-time)
ollama pull llama3.2

# 3. Tell docapi to use it
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.2
```

That's it — every command below now does real extraction, locally and free. docapi hands the
model a JSON Schema so it's *constrained* to emit matching JSON; combined with a corrective
retry and deterministic date repair, even a 3B model extracts invoices reliably.

> Long documents on a small local model can be slow (it chunks them to fit). For multi-page
> docs at speed, use the Claude path below.

### 🔵 If you HAVE a Claude (Anthropic) API key — use it for speed + quality

```bash
# 1. Install the optional Anthropic dependency
uv pip install -e ".[anthropic]"        # (or: pip install -e ".[anthropic]")

# 2. Point docapi at Claude with your key
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...      # your key from console.anthropic.com
# optional: export LLM_MODEL=claude-haiku-4-5   (the default — cheapest & fast)
```

Claude's large context window means long documents extract in **seconds** with no chunking, at
higher accuracy. Your key is read from the environment and never leaves your machine. Haiku is
the cheapest model and plenty for most extraction; set `LLM_MODEL` to a Sonnet/Opus id for harder docs.

### ⚪ Just want to see it work? — the stub (no model, no key)

```bash
unset LLM_PROVIDER            # or: export LLM_PROVIDER=stub
uv run python scripts/demo.py --stub
```

Returns realistic canned data instantly so you can see the full pipeline without installing anything.

---

## 3. Use it — four ways

All four run the **exact same** `extract_to_schema` core, so the reliability guarantees are identical.

### a) Try it on your own PDF (CLI)

```bash
uv run python scripts/try_extract.py path/to/your.pdf
```

(Uses whatever `LLM_PROVIDER` you set above. Add `--ollama` to force the local model for one run.)

### b) REST API

```bash
uv run uvicorn docapi.main:app --reload     # interactive docs at http://127.0.0.1:8000/docs

curl -s -F 'file=@invoice.pdf' \
     -F 'schema={"invoice_number":"string","invoice_date":"date","total_amount":"number"}' \
     http://127.0.0.1:8000/v1/extract | jq
```

Response: `{ "data": {...}, "confidence": 0.97, "pages": 1, "warnings": [] }` — or a structured
error if it couldn't produce schema-valid data.

### c) MCP tool (let an agent call it directly)

The same pipeline is exposed as an [MCP](https://modelcontextprotocol.io) tool, so an AI agent
can extract documents with no HTTP glue. Point Claude Desktop (or any MCP client) at it:

```jsonc
// claude_desktop_config.json
{
  "mcpServers": {
    "docapi": {
      "command": "uv",
      "args": ["run", "python", "-m", "docapi.mcp_server"],
      "cwd": "/absolute/path/to/docapi",
      "env": { "LLM_PROVIDER": "ollama", "LLM_MODEL": "llama3.2" }
    }
  }
}
```

Then just ask: *"Extract the invoice number, date, and total from ~/receipt.pdf."* The agent calls
the `extract_document` tool and gets back schema-valid JSON. (Swap the `env` block for your
Anthropic key to use Claude instead.)

### d) In Python

```python
from docapi.core.pipeline import extract_to_schema

with open("invoice.pdf", "rb") as f:
    result = extract_to_schema(
        f.read(), "invoice.pdf",
        {"invoice_number": "string", "invoice_date": "date", "total_amount": "number"},
    )

result.data        # → schema-valid dict
result.confidence  # → 0.0–1.0
result.warnings    # → e.g. ungrounded (possibly hallucinated) fields
```

---

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

## Reliability engine

- ✅ **Schema validation** on every output — never returns the wrong shape
- ✅ **Grounding check** — every extracted string is verified against the source text; anything the model *invented* is flagged and confidence drops (catches hallucination)
- ✅ **Long-document chunking** — big docs are split into windows that fit a small model's context, extracted independently, then merged (lists unioned, booleans OR-ed); no more silent truncation of late pages
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

## Develop / contribute

```bash
uv pip install -e ".[dev]"
uv run pytest        # 80 tests
uv run ruff check .
uv run mypy src
LLM_PROVIDER=ollama uv run python scripts/eval.py   # accuracy on real docs
```

Issues and PRs welcome. See [`SPEC.md`](./SPEC.md) for the full v1 spec.

## Status & roadmap

Working end-to-end today: core pipeline + REST API + MCP server + reliability layer + eval harness + 80 tests.

- [x] Extract-to-schema pipeline (REST `POST /v1/extract`)
- [x] Free local model (Ollama) + deterministic date repair
- [x] MCP `extract_document` tool (same pipeline, agent-native)
- [x] Eval harness with field-level accuracy + regression gate
- [x] Grounding (hallucination) check + long-document chunking
- [x] Anthropic (Claude) provider for the paid, high-quality path
- [ ] OCR fallback for scanned docs
- [ ] Hosted version: accounts, API keys, usage metering

## License & commercial use

Open source under the **[Apache-2.0](./LICENSE)** license — use it, self-host it, build on it.

A managed, **hosted** version is on the way: an API key instead of running a model yourself, plus
auth, usage metering, and scale — the same open core you see here is the engine behind it.

**👉 Want early access? Join the waitlist at [docapi-one.vercel.app](https://docapi-one.vercel.app)** — or open an issue / reach out.

---

<p align="center"><i>Building in public. Issues, ideas, and DMs welcome.</i></p>
