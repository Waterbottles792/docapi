# Eval harness

Unit tests prove the plumbing works. **This measures whether the pipeline returns the
*correct* values** on real documents — the number behind "reliability is the product."

## Run it

Real numbers need a real model, so start Ollama first:

```bash
LLM_PROVIDER=ollama LLM_MODEL=llama3.2 uv run python scripts/eval.py
```

Use it as a regression gate (non-zero exit if accuracy drops):

```bash
LLM_PROVIDER=ollama uv run python scripts/eval.py --threshold 0.85
```

## How it works

For each case it runs the **actual** `extract_to_schema` pipeline over a fixture document,
then scores the output field-by-field against a known-correct answer:

- numbers match within a small tolerance,
- strings match trimmed + case-insensitive,
- nested objects and list items are scored recursively, and mismatches are named
  (e.g. `line_items[1].amount`).

It prints per-document results and an overall **field accuracy** %.

## Add a case

1. Drop your document in `evals/fixtures/` (e.g. `my_invoice.pdf`).
2. Add `evals/cases/my_invoice.json`:

```json
{
  "document": "my_invoice.pdf",
  "note": "why this doc is interesting",
  "schema": { "invoice_number": "string", "invoice_date": "date", "total_amount": "number" },
  "expected": { "invoice_number": "...", "invoice_date": "2025-01-31", "total_amount": 1234.56 }
}
```

That's it — the runner picks up every `*.json` in `evals/cases/`.

> The three starter fixtures are tiny and directional, not a benchmark. Accuracy is only
> as trustworthy as the fixture set — grow it with real, varied documents.

The committed PDFs are reproducible via `uv run python evals/generate_fixtures.py`.
