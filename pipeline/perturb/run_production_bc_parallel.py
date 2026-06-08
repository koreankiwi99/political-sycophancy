#!/usr/bin/env python3
"""Production B+C only, parallel, resumable.

Skips A2 (analysis-only — run later on items) and D (analysis-only).
Reads pre-screened input, runs B then C on each, writes final items.

Usage:
  N_WORKERS=10 INPUT=data/derived/stage_a_passed_sonnet.jsonl \\
    python pipeline/perturb/run_production_bc_parallel.py
"""
import json, os, pathlib, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.perturb.generate_v8_dataset import (
    call, PERTURB_SYS, PERTURB_USR_T, COMPOSE_SYS, COMPOSE_USR_T,
    py_checks, fuzzy_in, DERIVED, DATASET,
)

MODEL_OPUS = "anthropic/claude-opus-4.7"
N_WORKERS  = int(os.environ.get("N_WORKERS", "10"))
INPUT      = pathlib.Path(os.environ.get("INPUT",
    str(DERIVED/"stage_a_passed_sonnet.jsonl")))

TAG    = "prod_bc_opus"
P_B    = DERIVED / f"v8_{TAG}_b.jsonl"
P_C    = DERIVED / f"v8_{TAG}_c.jsonl"
OUT    = DATASET / f"v8_{TAG}_items.jsonl"

# ── Stage runners ─────────────────────────────────────────────────────
def stage_b_opus(par, axes):
    user = PERTURB_USR_T.format(paragraph=par, axes_touched=json.dumps(axes))
    return call(MODEL_OPUS, PERTURB_SYS, user, max_tokens=900, temperature=0.2)


def stage_c_opus(par, b_out):
    user = COMPOSE_USR_T.format(paragraph=par,
                                  axes=json.dumps(b_out.get("axes",[])),
                                  pole_A_labels=json.dumps(b_out.get("pole_A_labels",[])),
                                  pole_B_labels=json.dumps(b_out.get("pole_B_labels",[])),
                                  true_claim_verbatim=b_out.get("true_claim_verbatim",""),
                                  false_claim=b_out.get("false_claim",""),
                                  operator=b_out.get("operator",""),
                                  claim_type=b_out.get("claim_type",""))
    return call(MODEL_OPUS, COMPOSE_SYS, user, max_tokens=1200, temperature=0.2)


# ── Resume — read already-done par_ids ────────────────────────────────
done_b_ids = set()
done_c_ids = set()
done_item_ids = set()
for path, target in [(P_B, done_b_ids), (P_C, done_c_ids), (OUT, done_item_ids)]:
    if path.exists():
        with open(path) as f:
            for ln in f:
                try:
                    r = json.loads(ln)
                    pid = r.get("par_id") or r.get("_par_id")
                    if pid: target.add(pid)
                except Exception:
                    pass


# ── Read input, filter to not-yet-done ────────────────────────────────
all_paras = []
with open(INPUT) as f:
    for ln in f:
        r = json.loads(ln)
        if r.get("_error") or not (r.get("axes_touched") or []):
            continue
        all_paras.append(r)

# A paragraph is fully done if its par_id has an item already (C must have succeeded)
todo = [p for p in all_paras if p["par_id"] not in done_item_ids]

print(f"Production B+C parallel run")
print(f"  input:      {INPUT.name}  ({len(all_paras)} A-passed)")
print(f"  already done (items): {len(done_item_ids)}")
print(f"  remaining:  {len(todo)}")
print(f"  workers:    {N_WORKERS}")
print(f"  output:     v8_{TAG}_items.jsonl (append-mode)")
print()


# ── Thread-safe append ────────────────────────────────────────────────
_write_lock = threading.Lock()
def append_safe(path, record):
    with _write_lock:
        with open(path, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ── One item's full B+C pipeline ──────────────────────────────────────
def process_item(r):
    par_id   = r["par_id"]
    par_text = r["_paragraph"]
    axes     = r.get("axes_touched") or []
    t0 = time.time()
    try:
        s_b = stage_b_opus(par_text, axes)
    except Exception as e:
        append_safe(P_B, {"par_id": par_id, "_error": str(e)})
        return ("B_ERR", par_id, str(e))
    append_safe(P_B, {"par_id": par_id, **s_b})
    if s_b.get("stop_reason") or not s_b.get("axes"):
        return ("B_STOP", par_id, s_b.get("stop_reason"))
    if not fuzzy_in(s_b.get("true_claim_verbatim",""), par_text):
        return ("B_NOT_VERBATIM", par_id, None)

    try:
        s_c = stage_c_opus(par_text, s_b)
    except Exception as e:
        append_safe(P_C, {"par_id": par_id, "_error": str(e)})
        return ("C_ERR", par_id, str(e))
    append_safe(P_C, {"par_id": par_id, **s_c})
    if s_c.get("stop_reason"):
        return ("C_STOP", par_id, s_c.get("stop_reason"))

    py = py_checks(s_b, s_c)
    if not (py["pole_consistent"] and py["C1_interrogative_invariant"]
            and py["C2_premise_verbatim"] and py["C3_plain_clean"]):
        return ("PY_DROP", par_id, str(py))

    final = {
        "item_id": f"v8p_{par_id[:10]}",
        "axes": s_b["axes"],
        "pole_A_labels": s_b["pole_A_labels"],
        "pole_B_labels": s_b["pole_B_labels"],
        "true_claim_verbatim": s_b["true_claim_verbatim"],
        "false_claim": s_b["false_claim"],
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
        "_par_id": par_id,
        "_docty": r.get("_docty"),
        "_doc_id": r.get("_doc_id"),
        "_doc_title": r.get("_doc_title"),
        "_paragraph": par_text,
        "_dt_s": round(time.time() - t0, 2),
    }
    append_safe(OUT, final)
    return ("KEEP", par_id, final["_dt_s"])


# ── Drive concurrency ─────────────────────────────────────────────────
counts = {"KEEP": 0, "B_ERR": 0, "B_STOP": 0, "B_NOT_VERBATIM": 0,
          "C_ERR": 0, "C_STOP": 0, "PY_DROP": 0}
t_start = time.time()
n = len(todo)

with ThreadPoolExecutor(max_workers=N_WORKERS) as ex:
    futures = {ex.submit(process_item, r): r["par_id"] for r in todo}
    for i, fut in enumerate(as_completed(futures), 1):
        try:
            status, pid, detail = fut.result()
        except Exception as e:
            print(f"[{i:>4d}/{n}] ?  exception: {e}")
            continue
        counts[status] = counts.get(status, 0) + 1
        if i % 5 == 0 or status == "KEEP":
            elapsed = time.time() - t_start
            rate = i / elapsed if elapsed > 0 else 0
            eta = (n - i) / rate if rate > 0 else 0
            kept = counts["KEEP"]
            print(f"[{i:>4d}/{n}] {status:14s} {pid}  | KEEP={kept}  rate={rate:.2f}/s  ETA={eta/60:.1f}min")

dt = time.time() - t_start
total_done = len(done_item_ids) + counts["KEEP"]
print(f"\n=== PRODUCTION B+C FUNNEL ===")
print(f"  processed this run: {n}  (wall: {dt/60:.1f} min)")
print(f"  KEEP this run:      {counts['KEEP']}")
print(f"  prior items:        {len(done_item_ids)}")
print(f"  TOTAL items:        {total_done}")
print(f"  drops:")
for k, v in sorted(counts.items()):
    if k != "KEEP" and v:
        print(f"    {k:16s} {v}")
print(f"\n  Output: {OUT}")
