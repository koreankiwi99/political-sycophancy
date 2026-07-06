"""Dataset loader for the political-sycophancy benchmark (Layer 2-C).

Loads prompts from a JSONL file and normalizes them to TestCase objects.

This is the 2c-only slice of the original evalsuite (the jailbreak / scope-QA
loaders for layers 1a/1b were dropped when this repo was consolidated).
"""

from __future__ import annotations

import json
from pathlib import Path

from evalsuite.types import TestCase


def _load_jsonl_as_testcases(
    path: str | Path,
    source: str,
    expected_behavior: str,
) -> list[TestCase]:
    """Generic loader: JSONL with prompt_id + text → TestCase list.

    Extra fields (item_id, variant, true_claim_verbatim, false_claim,
    reference_answer, axes, …) flow through via the metadata dict so the
    downstream sycophancy scorer keeps them.
    """
    p = Path(path)
    if not p.exists():
        print(f"  [skip] {p} not found")
        return []
    cases: list[TestCase] = []
    for line in p.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        cases.append(TestCase(
            id=r["prompt_id"],
            prompt=r.get("text") or r.get("prompt") or "",
            source=source,
            category=r.get("category", ""),
            expected_behavior=expected_behavior,
            metadata={k: v for k, v in r.items()
                      if k not in {"prompt_id", "text", "category"}},
        ))
    return cases


def load_political_sycophancy(path: str | Path | None = None,
                              sample: bool = False) -> list[TestCase]:
    """Load political-sycophancy prompts (Layer 2-C: political-bias /
    false-premise sycophancy).

    Each evaluation item explodes into FOUR prompts (variants):
      - clean:  true premise, neutral framing — baseline
      - plain:  false premise, neutral framing — measures premise-sycophancy
      - load_a: false premise, pole-A (right-of-center) rhetorical framing
      - load_b: false premise, pole-B (left-of-center) rhetorical framing

    The four variants share an item_id and an invariant interrogative_clause.
    Generator: political-sycophancy v8 pipeline (Opus B+C, Sonnet Stage A).
    Source corpus: World Bank analytical reports (CEM, PER, PA, SCD, WDR,
    CPF). Axes: 6 MARPOR v5 paired political-bias dimensions.

    Expected behavior: "comply" — the model should answer the question while
    correcting the false premise in non-CLEAN variants. The sycophancy scorer
    measures (a) premise-correction rate and (b) asymmetry between LOAD_A
    and LOAD_B answers (the political-bias signal).
    """
    if path is None:
        fname = ("political-sycophancy-sample.jsonl" if sample
                 else "political-sycophancy-final.jsonl")
        path = Path("data") / fname
    return _load_jsonl_as_testcases(path,
                                    source="political-sycophancy-v8",
                                    expected_behavior="comply")


def test_cases_to_csv(cases: list[TestCase], path: str | Path) -> None:
    """Export test cases to CSV (system_prompt, prompt, …)."""
    from evalsuite.datasets.io import save_csv

    rows = []
    for tc in cases:
        rows.append({
            "id": tc.id,
            "system_prompt": tc.system_prompt,
            "prompt": tc.prompt,
            "source": tc.source,
            "category": tc.category,
            "expected_behavior": tc.expected_behavior,
        })
    save_csv(rows, path)
    print(f"Exported {len(rows)} test cases to {path}")
