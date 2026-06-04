"""docapi eval harness — how often does the pipeline return the *correct* values?

Unit tests prove the plumbing. This measures real extraction accuracy: it runs the
actual pipeline over fixture documents and scores the output, field by field, against
known-correct answers.

    # Real numbers need a real model — start Ollama first:
    LLM_PROVIDER=ollama LLM_MODEL=llama3.2 uv run python scripts/eval.py

    # Use it as a regression gate (non-zero exit if accuracy drops below the bar):
    LLM_PROVIDER=ollama uv run python scripts/eval.py --threshold 0.85

Add a case: drop a PDF in evals/fixtures/ and a JSON manifest in evals/cases/ with
{"document", "schema", "expected"}. See evals/README.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from docapi.config import get_settings
from docapi.core.errors import DocApiError
from docapi.core.pipeline import extract_to_schema
from docapi.eval_scoring import score as _score

ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = ROOT / "evals" / "cases"
FIXTURES_DIR = ROOT / "evals" / "fixtures"

GREEN, RED, DIM, BOLD, YELLOW, RESET = (
    "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[33m", "\033[0m",
)


def _load_cases() -> list[dict[str, Any]]:
    cases = []
    for path in sorted(CASES_DIR.glob("*.json")):
        case = json.loads(path.read_text())
        case["_name"] = path.stem
        cases.append(case)
    return cases


def main() -> int:
    ap = argparse.ArgumentParser(description="docapi extraction accuracy eval")
    ap.add_argument("--threshold", type=float, default=None,
                    help="Fail (exit 1) if overall field accuracy is below this (0-1).")
    args = ap.parse_args()

    provider = get_settings().llm_provider
    print(f"\n{BOLD}docapi eval{RESET} {DIM}· provider={provider}{RESET}")
    if provider == "stub":
        print(f"{YELLOW}  ! provider is 'stub' — placeholders, not real extraction. "
              f"Set LLM_PROVIDER=ollama for meaningful numbers.{RESET}")
    print(f"{DIM}  {'─' * 64}{RESET}")

    cases = _load_cases()
    if not cases:
        print(f"{RED}no cases found in {CASES_DIR}{RESET}")
        return 1

    grand_matched = grand_total = 0
    for case in cases:
        name = case["_name"]
        doc = FIXTURES_DIR / case["document"]
        if not doc.is_file():
            print(f"  {RED}✗ {name}{RESET}  missing fixture: {doc}")
            grand_total += len(case["expected"])
            continue
        try:
            result = extract_to_schema(doc.read_bytes(), doc.name, case["schema"])
            matched, total, misses = _score(case["expected"], result.data)
        except DocApiError as exc:
            print(f"  {RED}✗ {name}{RESET}  error: {exc.type} — {exc.message}")
            grand_total += len(case["expected"])
            continue

        grand_matched += matched
        grand_total += total
        pct = matched / total if total else 0.0
        color = GREEN if matched == total else (YELLOW if pct >= 0.5 else RED)
        mark = "✓" if matched == total else "•"
        miss_str = f"  {DIM}missed: {', '.join(m for m in misses if m)}{RESET}" if matched != total else ""
        print(f"  {color}{mark} {name:<22}{RESET} {matched}/{total} fields  "
              f"{DIM}(conf {result.confidence}){RESET}{miss_str}")

    overall = grand_matched / grand_total if grand_total else 0.0
    print(f"{DIM}  {'─' * 64}{RESET}")
    bar_color = GREEN if overall >= 0.9 else (YELLOW if overall >= 0.7 else RED)
    print(f"  {BOLD}field accuracy: {bar_color}{overall:.0%}{RESET}{BOLD} "
          f"({grand_matched}/{grand_total} across {len(cases)} docs){RESET}\n")

    if args.threshold is not None and overall < args.threshold:
        print(f"{RED}FAIL: {overall:.0%} is below threshold {args.threshold:.0%}{RESET}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
