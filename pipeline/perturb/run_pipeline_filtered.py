#!/usr/bin/env python3
"""Run A2 → B → C → D1+D2+D3 on a pre-filtered Stage-A-passed file.

Usage:
  N_SAMPLE=20 INPUT=data/derived/stage_a_passed_sonnet.jsonl \\
    python pipeline/perturb/run_pipeline_filtered.py
"""
import json, os, pathlib, random, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.perturb.generate_v8_dataset import (
    stage_a2, stage_b, stage_c, stage_d1_axis, stage_d2_query, stage_d3_neutral,
    py_checks, fuzzy_in, append, DERIVED, DATASET, VALID_POLES,
)

INPUT_PATH = pathlib.Path(os.environ.get("INPUT",
    str(DERIVED/"stage_a_passed_sonnet.jsonl")))
N_SAMPLE = int(os.environ.get("N_SAMPLE", "20"))
SEED     = int(os.environ.get("SEED", "42"))

# Output files (separate from production)
TAG = "filtered_pilot"
P_A2     = DERIVED / f"v8_{TAG}_a2.jsonl"
P_B      = DERIVED / f"v8_{TAG}_b.jsonl"
P_C      = DERIVED / f"v8_{TAG}_c.jsonl"
P_D      = DERIVED / f"v8_{TAG}_d.jsonl"
OUT      = DATASET / f"v8_{TAG}_items.jsonl"
for p in (P_A2, P_B, P_C, P_D, OUT):
    if p.exists(): p.unlink()

# Read pre-filtered paragraphs
paras = []
with open(INPUT_PATH) as f:
    for ln in f:
        r = json.loads(ln)
        if r.get("_error") or not (r.get("axes_touched") or []):
            continue
        paras.append(r)

rng = random.Random(SEED)
rng.shuffle(paras)
sample = paras[:N_SAMPLE]

print(f"Filtered-pipeline run")
print(f"  input:      {INPUT_PATH.name}  ({len(paras)} Stage-A-passed paragraphs)")
print(f"  sample:     {len(sample)} (seed={SEED})")
print(f"  outputs:    v8_{TAG}_{{a2,b,c,d}}.jsonl + v8_{TAG}_items.jsonl")
print()

c = {k: 0 for k in (
    "total","b_pass","b_drop","c_pass","c_drop","py_pass","py_drop",
    "d1_pass","d1_drop","d2_pass","d2_drop","d3_pass","d3_drop",
    "final_items","cfs_with","cfs_without",
)}

t_start = time.time()
for i, r in enumerate(sample, 1):
    par_id   = r["par_id"]
    par_text = r["_paragraph"]
    axes     = r.get("axes_touched") or []
    c["total"] += 1
    t_item = time.time()

    # Stage A2 — analysis only (labels per sentence)
    try:
        s_a2 = stage_a2(par_text)
        sents = s_a2.get("sentences", []) or []
        cfs_sents = [s.get("sentence_verbatim","") for s in sents if s.get("label") == "CFS"]
        rec_a2 = {"par_id": par_id, "sentences": sents,
                   "contains_cfs": len(cfs_sents) > 0,
                   "cfs_sentences_verbatim": cfs_sents}
        append(P_A2, rec_a2)
        if cfs_sents: c["cfs_with"] += 1
        else: c["cfs_without"] += 1
    except Exception as e:
        append(P_A2, {"par_id": par_id, "_error": str(e)})

    # Stage B
    try:
        s_b = stage_b(par_text, {"docty": r.get("_docty"), "title": r.get("_doc_title")}, axes)
    except Exception as e:
        append(P_B, {"par_id": par_id, "_error": str(e)})
        c["b_drop"] += 1
        print(f"[{i:>3d}/{len(sample)}] {par_id} B_ERR")
        continue
    rec_b = {"par_id": par_id, **s_b}
    append(P_B, rec_b)
    if s_b.get("stop_reason") or not s_b.get("axes"):
        c["b_drop"] += 1
        print(f"[{i:>3d}/{len(sample)}] {par_id} B_STOP={s_b.get('stop_reason')}")
        continue
    if not fuzzy_in(s_b.get("true_claim_verbatim",""), par_text):
        c["b_drop"] += 1
        print(f"[{i:>3d}/{len(sample)}] {par_id} B_NOT_VERBATIM")
        continue
    c["b_pass"] += 1

    # Stage C
    try:
        s_c = stage_c(par_text, s_b)
    except Exception as e:
        append(P_C, {"par_id": par_id, "_error": str(e)})
        c["c_drop"] += 1
        continue
    rec_c = {"par_id": par_id, **s_c}
    append(P_C, rec_c)
    if s_c.get("stop_reason"):
        c["c_drop"] += 1
        print(f"[{i:>3d}/{len(sample)}] {par_id} C_STOP={s_c.get('stop_reason')}")
        continue

    # Python checks (variant invariance, premise verbatim)
    py = py_checks(s_b, s_c)
    if not (py["pole_consistent"] and py["C1_interrogative_invariant"]
            and py["C2_premise_verbatim"] and py["C3_plain_clean"]):
        c["py_drop"] += 1
        print(f"[{i:>3d}/{len(sample)}] {par_id} PY_DROP {py}")
        continue
    c["c_pass"] += 1
    c["py_pass"] += 1

    # Stage D1/D2/D3 — ANALYSIS ONLY (no gating). Labels recorded for inspection.
    d1, d2, d3 = {}, {}, {}
    try:
        d1 = stage_d1_axis(par_text, s_b, s_c)
        append(P_D, {"par_id": par_id, "stage": "d1", **d1})
        if (d1.get("min_aside_score") or 0) >= 3 and d1.get("false_claim_aligns_with") in ("pole_A","pole_B"):
            c["d1_pass"] += 1
        else:
            c["d1_drop"] += 1
    except Exception as e:
        append(P_D, {"par_id": par_id, "stage": "d1", "_error": str(e)})
    try:
        d2 = stage_d2_query(par_text, s_c)
        append(P_D, {"par_id": par_id, "stage": "d2", **d2})
        if d2.get("is_realistic_user_query"): c["d2_pass"] += 1
        else: c["d2_drop"] += 1
    except Exception as e:
        append(P_D, {"par_id": par_id, "stage": "d2", "_error": str(e)})
    try:
        d3 = stage_d3_neutral(s_b, s_c)
        append(P_D, {"par_id": par_id, "stage": "d3", **d3})
        if d3.get("is_self_contained") and d3.get("is_direction_neutral"):
            c["d3_pass"] += 1
        else:
            c["d3_drop"] += 1
    except Exception as e:
        append(P_D, {"par_id": par_id, "stage": "d3", "_error": str(e)})

    # Final item
    final = {
        "item_id": f"v8f_{c['final_items']+1:04d}",
        "axes": s_b["axes"],
        "pole_A_labels": s_b["pole_A_labels"],
        "pole_B_labels": s_b["pole_B_labels"],
        "true_claim_verbatim": s_b["true_claim_verbatim"],
        "false_claim": s_b["false_claim"],
        "false_claim_aligns_with": d1.get("false_claim_aligns_with"),
        "operator": s_b["operator"],
        "operator_tier": s_b.get("operator_tier"),
        "claim_type": s_b.get("claim_type"),
        "topic_phrase": s_b.get("topic_phrase",""),
        "interrogative_clause": s_c["interrogative_clause"],
        "faithful_answer_sketch": s_c.get("faithful_answer_sketch",""),
        "plausibility_note": s_c.get("plausibility_note",""),
        "clean_question": s_c["clean_question"],
        "plain_question": s_c["plain_question"],
        "loaded_pole_A_question": s_c["loaded_pole_A_question"],
        "loaded_pole_B_question": s_c["loaded_pole_B_question"],
        "_d1": d1, "_d2": d2, "_d3": d3,
        "_par_id": par_id,
        "_docty": r.get("_docty"),
        "_doc_id": r.get("_doc_id"),
        "_doc_title": r.get("_doc_title"),
        "_paragraph": par_text,
        "_dt_s": round(time.time() - t_item, 2),
    }
    append(OUT, final)
    c["final_items"] += 1
    print(f"[{i:>3d}/{len(sample)}] {par_id} KEEP  axes={','.join(s_b['axes'])} aligns={d1.get('false_claim_aligns_with')} D2={d2.get('is_realistic_user_query')} D3sc={d3.get('is_self_contained')} D3dn={d3.get('is_direction_neutral')} ({final['_dt_s']}s)")

dt = time.time() - t_start
n = max(1, c["total"])
print(f"\n=== FUNNEL ===")
print(f"  paragraphs in:   {c['total']}  (wall: {dt/60:.1f} min)")
print(f"  Stage A2:        {c['cfs_with']} with CFS / {c['cfs_without']} without (no gate)")
print(f"  Stage B pass:    {c['b_pass']:>3d}/{n} ({100*c['b_pass']/n:.0f}%)")
print(f"  Stage C+py pass: {c['c_pass']:>3d}/{c['b_pass'] or 1} ({100*c['c_pass']/(c['b_pass'] or 1):.0f}%)")
print(f"  Stage D1 pass:   {c['d1_pass']:>3d}/{c['c_pass'] or 1} ({100*c['d1_pass']/(c['c_pass'] or 1):.0f}%)")
print(f"  Stage D2 pass:   {c['d2_pass']:>3d}/{c['d1_pass'] or 1} ({100*c['d2_pass']/(c['d1_pass'] or 1):.0f}%)")
print(f"  Stage D3 pass:   {c['d3_pass']:>3d}/{c['d2_pass'] or 1} ({100*c['d3_pass']/(c['d2_pass'] or 1):.0f}%)")
print(f"  FINAL ITEMS:     {c['final_items']}  ({100*c['final_items']/n:.0f}% end-to-end)")
print(f"\n  Output: {OUT}")
