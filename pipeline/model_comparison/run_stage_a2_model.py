#!/usr/bin/env python3
"""Run Stage A2 (per-sentence NFS/UFS/CFS) with any model on the same set of
Haiku-passed paragraphs. Output file derived from model name.

Usage:
  MODEL=anthropic/claude-sonnet-4.6 python run_stage_a2_model.py
  MODEL=anthropic/claude-opus-4.7   python run_stage_a2_model.py
"""
import json, os, pathlib, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.perturb.generate_v8_dataset import (
    call, CLAIMFL_SYS, CLAIMFL_USR_T, append, DERIVED,
)

MODEL = os.environ.get("MODEL", "anthropic/claude-haiku-4.5")
TAG = MODEL.split("/")[-1].replace(".", "_")
IN  = DERIVED / "stage_a2_on_haiku_passed.jsonl"
OUT = DERIVED / f"stage_a2_compare_{TAG}.jsonl"
if OUT.exists():
    OUT.unlink()

records = []
with open(IN) as f:
    for ln in f:
        r = json.loads(ln)
        if r.get("_error"): continue
        records.append(r)

print(f"Stage A2 model comparison run")
print(f"  model:      {MODEL}")
print(f"  output:     {OUT.name}")
print(f"  paragraphs: {len(records)}")
print()

c = {"total": 0, "with_cfs": 0, "without_cfs": 0, "error": 0,
     "nfs_sents": 0, "ufs_sents": 0, "cfs_sents": 0}
t_start = time.time()

for i, r in enumerate(records, 1):
    par_text = r["_paragraph"]
    par_id = r["par_id"]
    c["total"] += 1
    try:
        user = CLAIMFL_USR_T.format(paragraph=par_text)
        s = call(MODEL, CLAIMFL_SYS, user, max_tokens=800, temperature=0)
    except Exception as e:
        append(OUT, {"par_id": par_id, "_error": str(e)})
        c["error"] += 1
        continue
    sents = s.get("sentences", []) or []
    nfs = [x for x in sents if x.get("label") == "NFS"]
    ufs = [x for x in sents if x.get("label") == "UFS"]
    cfs = [x for x in sents if x.get("label") == "CFS"]
    c["nfs_sents"] += len(nfs)
    c["ufs_sents"] += len(ufs)
    c["cfs_sents"] += len(cfs)
    rec = {"par_id": par_id,
           "model": MODEL,
           "sentences": sents,
           "contains_cfs": len(cfs) > 0,
           "cfs_sentences_verbatim": [x.get("sentence_verbatim","") for x in cfs]}
    append(OUT, rec)
    if len(cfs) > 0:
        c["with_cfs"] += 1
    else:
        c["without_cfs"] += 1
    print(f"[{i:>3d}/{len(records)}] {par_id}  NFS={len(nfs)} UFS={len(ufs)} CFS={len(cfs)}")

dt = time.time() - t_start
total_sents = c["nfs_sents"] + c["ufs_sents"] + c["cfs_sents"]
print(f"\n=== STAGE A2 FUNNEL ({MODEL}) ===")
print(f"  paragraphs in:        {c['total']}  (wall: {dt/60:.1f} min)")
print(f"  contain >=1 CFS:      {c['with_cfs']}  ({100*c['with_cfs']/max(1,c['total']):.0f}%)")
print(f"  no CFS:               {c['without_cfs']}")
print(f"  errors:               {c['error']}")
print(f"  per-sentence:")
print(f"    NFS: {c['nfs_sents']:>4d}  ({100*c['nfs_sents']/max(1,total_sents):.1f}%)")
print(f"    UFS: {c['ufs_sents']:>4d}  ({100*c['ufs_sents']/max(1,total_sents):.1f}%)")
print(f"    CFS: {c['cfs_sents']:>4d}  ({100*c['cfs_sents']/max(1,total_sents):.1f}%)")
print(f"\n  Output: {OUT}")
