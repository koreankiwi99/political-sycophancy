# Dataset spec (locked)

## Item schema (one JSON object per base fact)
```json
{
  "id": "crs_IF11175_03",
  "source": {"corpus": "CRS", "doc_id": "IF11175", "passage": "<gold sentence text>"},
  "source_fact": "<true atomic fact, as stated by the corpus>",
  "claim_type": "comparison",            // statistic|dated_event|attribution|comparison|causal
  "issue": "immigration",
  "misperception_ref": "liar:immigration:right",   // inventory entry it matches (Shaar-style)
  "perturbation": {"operator": "comparative_flip", "plausibility": "blatant"},
  "direction": "right",                  // right|left|none ; constructed + validated
  "variants": {
    "clean":        "<true-premise question, matched stem>",
    "neutral_false":"<false-premise question, neutral wording>",
    "loaded_false_right": "<right-loaded>",
    "loaded_false_left":  "<left-loaded, if fact admits both>"
  },
  "gold_evidence": {"doc_id": "IF11175", "passage": "<refuting sentence>"},
  "validation": {"factuality": null, "refutation_retrievable": null,
                 "minimal_pair": null, "direction_kappa": null}
}
```

## Correctness definition
**Corpus-relative** (knowledge-conflict framing; Longpre 2021 / FaithEval / ClashEval):
a premise is "false" iff the retrieval corpus authoritatively contradicts it. World-truth is NOT
re-verified per fact; political items are additionally restricted to uncontested facts + anchored
to a documented misperception (spot-checked).

## Sources (roles locked)
- **Wikipedia (FEVER dump)** — retrieval backbone + Branch-B ready items + retrieval-recall ground truth.
- **CRS, GAO** — Branch-A extraction sources (political facts). [primary political track]
- **LIAR, CARDS** — misperception inventory (direction anchor) + claim-matching bank.
- **World Bank, Climate-FEVER** — complementary.

## Sizes
- ~300 base facts (Branch A), each → clean / neutral_false / loaded_false(+both directions where feasible).
- ≈ 900–1,200 queries. Minimum-viable 150 facts.
- Human-validated subset: 150–200 items, 2 annotators, report κ on the 4 validation fields.
- FEVER/Climate-FEVER backbone: additional, apolitical, for machinery + retrieval-recall.

## Power
FP (neutral_false vs loaded_false, paired McNemar) primary: ~250–300 paired items → 80% power, α=.05,
correction drop ~0.10–0.15. DA paired (left vs right loaded of same fact) where constructible.
