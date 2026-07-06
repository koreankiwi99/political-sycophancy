#!/usr/bin/env python3
"""Run Stage A2 (per-sentence ClaimBuster classification) on paragraphs that
passed Haiku's Stage A (axes-touched non-empty).

Input:  data/derived/screened.jsonl  (Stage A output)
Output: data/derived/claims.jsonl
"""
import json, pathlib, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.utils import (
    call, CLAIMFL_SYS, CLAIMFL_USR_T, append, DERIVED,
)

MODEL_HAIKU = "anthropic/claude-haiku-4.5"

IN  = DERIVED / "screened.jsonl"
OUT = DERIVED / "claims.jsonl"
if OUT.exists():
    OUT.unlink()


def classify_claims(par):
    """Per-sentence ClaimBuster-style labels (NFS / UFS / CFS)."""
    user = CLAIMFL_USR_T.format(paragraph=par)
    return call(MODEL_HAIKU, CLAIMFL_SYS, user, max_tokens=800, temperature=0)

# Filter to Haiku-passed paragraphs (axes_touched non-empty)
passed = []
with open(IN) as f:
    for ln in f:
        r = json.loads(ln)
        if r.get("_error"): continue
        if r.get("axes_touched"):
            passed.append(r)

print(f"Stage A2 on Haiku-passed paragraphs")
print(f"  input:      {IN.name}")
print(f"  output:     {OUT.name}")
print(f"  paragraphs: {len(passed)} (filtered to axes-touched only)")
print()

c = {"total": 0, "cfs_pass": 0, "cfs_drop": 0, "error": 0,
     "nfs_sents": 0, "ufs_sents": 0, "cfs_sents": 0}
t_start = time.time()

for i, r in enumerate(passed, 1):
    par_text = r["_paragraph"]
    par_id = r["par_id"]
    c["total"] += 1
    try:
        s_a2 = classify_claims(par_text)
    except Exception as e:
        append(OUT, {"par_id": par_id, "_error": str(e)})
        c["error"] += 1
        continue
    sents = s_a2.get("sentences", []) or []
    nfs = [s for s in sents if s.get("label") == "NFS"]
    ufs = [s for s in sents if s.get("label") == "UFS"]
    cfs = [s for s in sents if s.get("label") == "CFS"]
    c["nfs_sents"] += len(nfs)
    c["ufs_sents"] += len(ufs)
    c["cfs_sents"] += len(cfs)
    paragraph_passes = len(cfs) > 0
    rec = {"par_id": par_id,
           "_docty": r.get("_docty"),
           "_doc_title": r.get("_doc_title"),
           "_doc_id": r.get("_doc_id"),
           "_paragraph": par_text,
           "haiku_axes_touched": r.get("axes_touched"),
           "haiku_reason": r.get("reason"),
           "sentences": sents,
           "contains_cfs": paragraph_passes,
           "cfs_sentences_verbatim": [s.get("sentence_verbatim","") for s in cfs]}
    append(OUT, rec)
    if paragraph_passes:
        c["cfs_pass"] += 1
    else:
        c["cfs_drop"] += 1
    print(f"[{i:>3d}/{len(passed)}] {par_id}  "
          f"NFS={len(nfs)} UFS={len(ufs)} CFS={len(cfs)}  "
          f"{'PASS' if paragraph_passes else 'DROP'}")

dt = time.time() - t_start
n = max(1, c["total"])
total_sents = c["nfs_sents"] + c["ufs_sents"] + c["cfs_sents"]
print(f"\n=== STAGE A2 FUNNEL (on Haiku-passed paragraphs) ===")
print(f"  paragraphs in:        {c['total']}  (wall: {dt/60:.1f} min)")
print(f"  contain >=1 CFS:      {c['cfs_pass']}  ({100*c['cfs_pass']/n:.1f}%)")
print(f"  no CFS (all NFS/UFS): {c['cfs_drop']}  ({100*c['cfs_drop']/n:.1f}%)")
print(f"  errors:               {c['error']}")
print()
print(f"  per-sentence label distribution (across all paragraphs):")
print(f"    NFS (non-factual):    {c['nfs_sents']:>4d}  ({100*c['nfs_sents']/max(1,total_sents):.1f}%)")
print(f"    UFS (unimportant):    {c['ufs_sents']:>4d}  ({100*c['ufs_sents']/max(1,total_sents):.1f}%)")
print(f"    CFS (check-worthy):   {c['cfs_sents']:>4d}  ({100*c['cfs_sents']/max(1,total_sents):.1f}%)")
print(f"\n  Output: {OUT}")
