#!/usr/bin/env python3
"""Transform v8 pipeline output → red_teaming JSONL format.

Reads:  data/dataset/v8_filtered_pilot_opus_items.jsonl  (final items)
Writes: /Users/default/red_teaming/data/political-sycophancy-final.jsonl
        /Users/default/red_teaming/data/political-sycophancy-sample.jsonl  (50 items)

Each input item explodes into 4 prompt records (clean / plain / load_a / load_b)
so the red_teaming runner can dispatch them individually.
"""
import json, pathlib, random

ROOT = pathlib.Path(__file__).resolve().parents[2]
IN     = ROOT / "data" / "dataset" / "v8_items_clean_110.jsonl"
IN_C   = ROOT / "data" / "derived" / "v8_prod_bc_opus_c.jsonl"  # for faithful_answer_sketch
RED_DATA = pathlib.Path("/Users/default/red_teaming/data")
OUT_FULL   = RED_DATA / "political-sycophancy-final.jsonl"
OUT_SAMPLE = RED_DATA / "political-sycophancy-sample.jsonl"
SAMPLE_N = 50
ITEM_CAP = 10_000   # effectively no cap — push all items
SEED = 42

# Read final items
items = []
with open(IN) as f:
    for ln in f:
        items.append(json.loads(ln))
print(f"Read {len(items)} items from {IN.name}")
if len(items) > ITEM_CAP:
    items = items[:ITEM_CAP]
    print(f"Capped at {ITEM_CAP} items")

# Join Stage C output to recover faithful_answer_sketch + plausibility_note
# (the Opus runner's final item dict drops these; we recover by par_id)
c_by_par = {}
with open(IN_C) as f:
    for ln in f:
        r = json.loads(ln)
        if r.get("stop_reason") or not r.get("interrogative_clause"): continue
        c_by_par[r["par_id"]] = r
print(f"Read {len(c_by_par)} Stage C records for joining")


def explode(item):
    """Yield 4 TestCase-shaped records (one per variant)."""
    par_id = item.get("_par_id")
    c_rec = c_by_par.get(par_id, {})
    reference_answer = (item.get("faithful_answer_sketch")
                        or c_rec.get("faithful_answer_sketch", ""))
    plausibility_note = (item.get("plausibility_note")
                         or c_rec.get("plausibility_note", ""))
    base = {
        "category": "political_sycophancy",
        "source": "political-sycophancy-v8",
        # Source grounding
        "doc_id": item.get("_doc_id"),
        "doc_title": item.get("_doc_title"),
        "docty": item.get("_docty"),
        "_paragraph": item.get("_paragraph", ""),
        "par_id": par_id,
        # Reference (ground truth)
        "reference_answer": reference_answer,
        "plausibility_note": plausibility_note,
        "true_claim_verbatim": item.get("true_claim_verbatim", ""),
        # Political-bias metadata
        "axes": item.get("axes", []),
        "pole_A_labels": item.get("pole_A_labels", []),
        "pole_B_labels": item.get("pole_B_labels", []),
        "false_claim": item.get("false_claim", ""),
        "false_claim_aligns_with": item.get("false_claim_aligns_with"),
        "perturbation_operator": item.get("operator", ""),
        "perturbation_tier": item.get("operator_tier"),
        "claim_type": item.get("claim_type", ""),
        "interrogative_clause": item.get("interrogative_clause", ""),
        # D-stage analysis labels (analysis-only)
        "_d1": item.get("_d1", {}),
        "_d2": item.get("_d2", {}),
        "_d3": item.get("_d3", {}),
        # Generator provenance
        "generator_version": "political_sycophancy_v8_opus",
        "generator_model": "anthropic/claude-opus-4.7",
    }

    iid = item.get("item_id", "ps_unknown")
    for variant_key, text_key in [
        ("clean",  "clean_question"),
        ("plain",  "plain_question"),
        ("load_a", "loaded_pole_A_question"),
        ("load_b", "loaded_pole_B_question"),
    ]:
        yield {
            "prompt_id": f"{iid}_{variant_key}",
            "item_id": iid,
            "variant": variant_key,
            "text": item.get(text_key, ""),
            **base,
        }


# Write full
n_records = 0
with open(OUT_FULL, "w", encoding="utf-8") as f:
    for item in items:
        for rec in explode(item):
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n_records += 1
print(f"Wrote {n_records} records → {OUT_FULL}")

# Write sample (random N items × 4 variants)
rng = random.Random(SEED)
sample_items = rng.sample(items, min(SAMPLE_N, len(items)))
n_sample = 0
with open(OUT_SAMPLE, "w", encoding="utf-8") as f:
    for item in sample_items:
        for rec in explode(item):
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n_sample += 1
print(f"Wrote {n_sample} sample records (from {len(sample_items)} items) → {OUT_SAMPLE}")

print()
print(f"Summary:")
print(f"  full   : {len(items):>4d} items × 4 variants = {n_records} prompts")
print(f"  sample : {len(sample_items):>4d} items × 4 variants = {n_sample} prompts")
