#!/usr/bin/env python3
"""Run Stage A (axes screen) at full scale with Sonnet."""
import json, os, pathlib, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.perturb.generate_v8_dataset import (
    call, SCREEN_SYS, SCREEN_USR_T, pick_docs, pick_pars, append, DERIVED,
)

MODEL_SONNET = "anthropic/claude-sonnet-4.6"

OUT = DERIVED / "stage_a_full_scale_sonnet.jsonl"
if OUT.exists():
    OUT.unlink()

docs = pick_docs()
print(f"Stage A (axes-touching) full-scale run with Sonnet")
print(f"  N_DOCS_PER_DOCTYPE = {os.environ.get('N_DOCS_PER_DOCTYPE','8')}")
print(f"  N_PARS_PER_DOC     = {os.environ.get('N_PARS_PER_DOC','5')}")
print(f"  model:             {MODEL_SONNET}")
print(f"  total docs={len(docs)}  expected paragraphs≈{len(docs) * int(os.environ.get('N_PARS_PER_DOC','5'))}")
print(f"  output:            {OUT}")
print()

c = {"total": 0, "pass": 0, "drop": 0, "error": 0}
axis_hits = {f"A{i}": 0 for i in range(1, 7)}

t_start = time.time()
for di, doc in enumerate(docs, 1):
    pars = pick_pars(doc["text"])
    print(f"[{di:>3}/{len(docs)}] {doc['docty'][:25]:>25s} | {doc['title'][:55]}")
    for pi, par in enumerate(pars, 1):
        c["total"] += 1
        par_id = f"{doc.get('guid','')[:10]}_{pi}"
        par_text = par["text"]
        try:
            user = SCREEN_USR_T.format(paragraph=par_text)
            s_a = call(MODEL_SONNET, SCREEN_SYS, user, max_tokens=400, temperature=0)
        except Exception as e:
            append(OUT, {"par_id": par_id, "_error": str(e),
                          "_docty": doc.get("docty"),
                          "_doc_id": doc.get("guid")})
            c["error"] += 1
            continue
        axes = s_a.get("axes_touched", []) or []
        rec = {"par_id": par_id,
               "_docty": doc.get("docty"),
               "_doc_title": doc.get("title"),
               "_doc_id": doc.get("guid"),
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
print(f"\n=== SONNET STAGE A FUNNEL ===")
print(f"  paragraphs processed: {c['total']}  (wall: {dt/60:.1f} min)")
print(f"  axes-touched pass:    {c['pass']}  ({100*c['pass']/n:.1f}%)")
print(f"  no-axis drop:         {c['drop']}  ({100*c['drop']/n:.1f}%)")
print(f"  errors:               {c['error']}")
print(f"\n  per-axis hit counts (paragraphs touching that axis):")
for a in sorted(axis_hits):
    pct = 100 * axis_hits[a] / max(1, c['pass'])
    print(f"    {a}: {axis_hits[a]:>4d}  ({pct:.1f}% of axes-pass)")
print(f"\n  Output: {OUT}")
