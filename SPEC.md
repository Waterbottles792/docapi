# Document API for AI Agents — Build Spec (v1)

> **Purpose of this file:** a concrete, buildable engineering specification for an AI coding
> agent to implement the **v1** of this product.
>
> **Scope discipline:** v1 ships **one** operation — **extract-to-schema** — done reliably,
> exposed over a REST API **and** an MCP server, with API keys, usage metering, and a small
> eval harness. Everything else is explicitly out of scope until v1 works end to end.

---

## 2. Product overview

**The core loop:** a caller (an AI agent or the developer building one) sends a **document**
plus a **schema** describing the fields they want, and receives **structured JSON that validates
against that schema**, plus a confidence signal — or a precise, structured error explaining why
it couldn't.

```
file + schema  ──►  [ingest → process → validate → return]  ──►  schema-shaped JSON + confidence
```

The product's value is **reliability on messy real-world inputs**, not access to a model. That
guarantee is the moat. Build accordingly.

---

## 3. v1 scope

### In scope
- One operation: **`extract`** (extract-to-schema) for **PDF and common image formats**
  (`.pdf`, `.png`, `.jpg`, `.jpeg`).
- Synchronous processing for reasonably sized files.
- **REST API** + **MCP server**.
- **API keys**, per-key **rate limiting**, and **usage metering** recorded to the database.
- **Reliability engine**: schema validation, one corrective retry, an OCR fallback for scans,
  confidence score, structured errors.
- A small **eval harness** with real (anonymized) fixtures.
- Minimal **docs**: a `README.md` quickstart + the API reference generated from OpenAPI.

### Out of scope (do NOT build yet)
- Other operations (form-fill, table extraction, document generation, standalone OCR).
- Asynchronous jobs / webhooks (sync only in v1).
- A web dashboard / UI (keys are issued via CLI/admin script in v1).
- Multi-tenant orgs, teams, roles.
- Live Stripe billing enforcement (record usage now; wire Stripe in a later phase).
- Self-hosting / on-prem packaging.

### Limits (v1 defaults; make them config)
- Max file size: **20 MB**.
- Max pages per document: **30**.
- Request timeout: **60s** (sync).

---

## 4. Tech stack (opinionated defaults)

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| API framework | FastAPI + uvicorn |
| Validation/models | pydantic v2 |
| PDF text/tables | pdfplumber, pypdf |
| OCR fallback | pytesseract + pdf2image (poppler) |
| Understanding step | swappable: stub / Ollama (local, free) / Anthropic Claude |
| Database | PostgreSQL + SQLAlchemy 2.0 + Alembic |
| Object storage | S3-compatible (boto3) |
| Billing | Stripe (metered) — later phase |
| MCP | official `mcp` Python SDK |
| Tests | pytest |
| Lint/format/types | ruff, mypy |
| Packaging/run | Docker + pyproject.toml (uv) |

---

## 11. The extraction pipeline (`core/pipeline.py`)

Single entry point used by both REST and MCP:

```python
def extract_to_schema(file_bytes: bytes, filename: str,
                      schema: dict, options: dict) -> ExtractResult: ...
```

Stages:

1. **Ingest** — validate type & size; count pages; detect digital-text vs scan.
2. **Acquire text/content** — deterministic extraction (pdfplumber/pypdf); OCR fallback for scans.
3. **Understand** — map extracted content + target schema → structured data (LLM).
4. **Validate** — validate JSON against the schema; **one corrective retry** on failure.
5. **Score & return** — confidence, pages, warnings.
6. **Meter** — write a `usage_records` row.

---

## 13. Reliability & error handling

This is the product. Build it deliberately.

- **Schema validation** on every output. Never return data that doesn't match the requested shape.
- **One corrective retry** feeding validation errors back to the model before giving up.
- **OCR fallback** when text extraction is weak or the input is an image/scan.
- **Deterministic over model** wherever a library suffices (e.g. date normalisation).
- **Confidence signal** on every successful response.
- **Structured errors** — every error is JSON with a stable `type`, a human `message`, context.
- **No silent failure.** Better a precise error than wrong data.

---

## 17. Build plan (work phase by phase)

- [x] **Phase 0 — Scaffold.** FastAPI app, config, `/healthz`, ruff/mypy/pytest.
- [x] **Phase 1 — Core extract (happy path).** ingest + extractors + understand + validate.
- [~] **Phase 2 — Reliability.** Corrective retry ✅, deterministic date repair ✅, structured
      errors ✅, limits ✅. OCR fallback for scans — TODO.
- [~] **Phase 3 — REST.** `POST /v1/extract` ✅, `GET /healthz` ✅. Auth + metering + DB — TODO.
- [x] **Phase 4 — MCP server.** `extract_document` tool calling the same pipeline.
- [ ] **Phase 5 — Eval harness + docs.** Fixtures + accuracy gate.
- [ ] **Phase 6 — Deploy.** Containerized; secrets via env.

---

## 19. Roadmap (after v1)

1. PDF form fill. 2. Table extraction. 3. Document generation. 4. Async jobs + webhooks.
5. Stripe billing enforcement. 6. Thin dashboard for keys + usage. 7. Enterprise tier.

Each new operation should be **a new process module + a new route + a new MCP tool**, reusing
the ingest/validate/meter machinery. Keep the core small.
