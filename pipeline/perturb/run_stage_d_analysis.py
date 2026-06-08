#!/usr/bin/env python3
"""Run Stage D (D1 axis-realism + alignment, D2 query realism, D3 self-
contained / direction-neutral) analysis ONLY — no gating — on the 216-item
trimmed dataset. Reports how many items pass each check.

Parallel via ThreadPoolExecutor.

Usage:
  N_WORKERS=8 python pipeline/perturb/run_stage_d_analysis.py
"""
import json, os, pathlib, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.perturb.generate_v8_dataset import (
    stage_d1_axis, stage_d2_query, stage_d3_neutral,
    DERIVED,
)

N_WORKERS = int(os.environ.get("N_WORKERS", "8"))
IN  = ROOT / "data" / "dataset" / "v8_items_216_trimmed.jsonl"
OUT = DERIVED / "stage_d_analysis_216.jsonl"
if OUT.exists():
    OUT.unlink()

items = []
with open(IN) as f:
    for ln in f:
        items.append(json.loads(ln))
print(f"Stage D analysis on {len(items)} items ({N_WORKERS} workers)")
print()

_write_lock = threading.Lock()

def process(item):
    par_text = item.get("_paragraph", "")
    par_id   = item.get("_par_id") or item.get("par_id")
    item_id  = item["item_id"]

    # Recover Stage C fields for D inputs (faithful_answer_sketch lives in C, but
    # for D we only need claim/interrogative/loaded — those are in the item)
    b_out = {
        "axes":            item.get("axes", []),
        "pole_A_labels":   item.get("pole_A_labels", []),
        "pole_B_labels":   item.get("pole_B_labels", []),
        "true_claim_verbatim": item.get("true_claim_verbatim",""),
        "false_claim":     item.get("false_claim",""),
        "operator":        item.get("operator",""),
    }
    c_out = {
        "interrogative_clause":     item.get("interrogative_clause",""),
        "loaded_pole_A_question":   item.get("loaded_pole_A_question",""),
        "loaded_pole_B_question":   item.get("loaded_pole_B_question",""),
    }

    d1 = d2 = d3 = None
    err = []
    try:
        d1 = stage_d1_axis(par_text, b_out, c_out)
    except Exception as e:
        err.append(f"D1: {e}")
    try:
        d2 = stage_d2_query(par_text, c_out)
    except Exception as e:
        err.append(f"D2: {e}")
    try:
        d3 = stage_d3_neutral(b_out, c_out)
    except Exception as e:
        err.append(f"D3: {e}")

    rec = {
        "item_id": item_id,
        "par_id":  par_id,
        "axes":    b_out["axes"],
        "d1":      d1,
        "d2":      d2,
        "d3":      d3,
        "errors":  err,
    }
    with _write_lock:
        with open(OUT, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


t_start = time.time()
done = 0
with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
    futures = {ex.submit(process, it): it["item_id"] for it in items}
    for fut in as_completed(futures):
        done += 1
        rec = fut.result()
        if done % 20 == 0:
            elapsed = time.time() - t_start
            rate = done / elapsed
            eta = (len(items) - done) / rate if rate > 0 else 0
            print(f"  {done}/{len(items)}  rate={rate:.2f}/s  ETA={eta/60:.1f}min")
dt = time.time() - t_start

# Summarize
n = len(items)
d1_aligned = 0; d1_ambiguous = 0; d1_min_score = Counter()
d2_yes = 0
d3_self = 0; d3_neut = 0; d3_both = 0
errors = 0
with open(OUT) as f:
    for ln in f:
        r = json.loads(ln)
        if r["errors"]:
            errors += 1
        if r["d1"]:
            aligns = r["d1"].get("false_claim_aligns_with")
            if aligns in ("pole_A","pole_B"):
                d1_aligned += 1
            else:
                d1_ambiguous += 1
            d1_min_score[r["d1"].get("min_aside_score")] += 1
        if r["d2"]:
            if r["d2"].get("is_realistic_user_query"):
                d2_yes += 1
        if r["d3"]:
            sc = r["d3"].get("is_self_contained")
            dn = r["d3"].get("is_direction_neutral")
            if sc: d3_self += 1
            if dn: d3_neut += 1
            if sc and dn: d3_both += 1

print(f"\n=== STAGE D ANALYSIS — 216 ITEMS ===")
print(f"  wall: {dt/60:.1f} min  errors: {errors}")
print()
print(f"D1 (axis realism + alignment):")
print(f"  false_claim_aligned (pole_A or pole_B): {d1_aligned}/{n} ({100*d1_aligned/n:.0f}%)")
print(f"  false_claim ambiguous:                  {d1_ambiguous}/{n} ({100*d1_ambiguous/n:.0f}%)")
print(f"  min_aside_score distribution:")
for s in sorted(d1_min_score.keys(), key=lambda x: (x is None, x)):
    print(f"    score={s}: {d1_min_score[s]}")
print()
print(f"D2 (realistic user query):")
print(f"  is_realistic_user_query=True: {d2_yes}/{n} ({100*d2_yes/n:.0f}%)")
print()
print(f"D3 (self-contained + direction-neutral):")
print(f"  is_self_contained=True:    {d3_self}/{n} ({100*d3_self/n:.0f}%)")
print(f"  is_direction_neutral=True: {d3_neut}/{n} ({100*d3_neut/n:.0f}%)")
print(f"  BOTH (sc & dn):            {d3_both}/{n} ({100*d3_both/n:.0f}%)")
print()
print(f"Output: {OUT}")
