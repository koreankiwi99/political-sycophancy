#!/usr/bin/env python3
"""Re-run Stage A with Haiku on the same 60 small-pilot paragraphs (the
original small-pilot Haiku output was overwritten by the full-scale run)."""
import json, pathlib, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.perturb.generate_v8_dataset import (
    call, SCREEN_SYS, SCREEN_USR_T, append, DERIVED,
)

MODEL_HAIKU = "anthropic/claude-haiku-4.5"

IN  = DERIVED / "stage_a_full_scale_opus.jsonl"
OUT = DERIVED / "stage_a_small_haiku.jsonl"
if OUT.exists():
    OUT.unlink()

records = []
with open(IN) as f:
    for ln in f:
        r = json.loads(ln)
        if r.get("_error"): continue
        records.append(r)

print(f"Haiku Stage A small-pilot rerun")
print(f"  input:      {IN.name}")
print(f"  output:     {OUT.name}")
print(f"  model:      {MODEL_HAIKU}")
print(f"  paragraphs: {len(records)}")
print()

c = {"total": 0, "pass": 0, "drop": 0, "error": 0}
axis_hits = {f"A{i}": 0 for i in range(1, 7)}
t_start = time.time()

for i, r in enumerate(records, 1):
    par_text = r["_paragraph"]
    par_id = r["par_id"]
    c["total"] += 1
    try:
        user = SCREEN_USR_T.format(paragraph=par_text)
        s_a = call(MODEL_HAIKU, SCREEN_SYS, user, max_tokens=300, temperature=0)
    except Exception as e:
        append(OUT, {"par_id": par_id, "_error": str(e),
                      "_docty": r.get("_docty"),
                      "_doc_id": r.get("_doc_id")})
        c["error"] += 1
        continue
    axes = s_a.get("axes_touched", []) or []
    rec = {"par_id": par_id,
           "_docty": r.get("_docty"),
           "_doc_title": r.get("_doc_title"),
           "_doc_id": r.get("_doc_id"),
           "_paragraph": par_text,
           **s_a}
    append(OUT, rec)
    if axes:
        c["pass"] += 1
        for a in axes:
            if a in axis_hits:
                axis_hits[a] += 1
    else:
        c["drop"] += 1

dt = time.time() - t_start
n = max(1, c["total"])
print(f"\n=== HAIKU STAGE A FUNNEL ===")
print(f"  paragraphs processed: {c['total']}  (wall: {dt/60:.1f} min)")
print(f"  axes-touched pass:    {c['pass']}  ({100*c['pass']/n:.1f}%)")
print(f"  no-axis drop:         {c['drop']}  ({100*c['drop']/n:.1f}%)")
print(f"  errors:               {c['error']}")
print(f"\n  per-axis hit counts:")
for a in sorted(axis_hits):
    pct = 100 * axis_hits[a] / max(1, c['pass'])
    print(f"    {a}: {axis_hits[a]:>4d}  ({pct:.1f}% of axes-pass)")
print(f"\n  Output: {OUT}")
