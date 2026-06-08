#!/usr/bin/env python3
"""Compare two Stage A axis-classification runs (e.g., Haiku vs Opus).

Reads two JSONL files with the same paragraph IDs, reports:
  - Per-paragraph axis-set agreement (full / partial / disjoint)
  - Per-axis hit counts and intersection-over-union
  - Top disagreement examples
"""
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DERIVED = ROOT / "data" / "derived"

H_FILE = DERIVED / "stage_a_full_scale.jsonl"
O_FILE = DERIVED / "stage_a_full_scale_opus.jsonl"

def load(path):
    out = {}
    with open(path) as f:
        for ln in f:
            r = json.loads(ln)
            if r.get("_error"):
                continue
            out[r["par_id"]] = r
    return out


def main():
    if not H_FILE.exists() or not O_FILE.exists():
        sys.exit(f"missing input: need both {H_FILE.name} and {O_FILE.name}")
    h = load(H_FILE)
    o = load(O_FILE)
    common = sorted(set(h) & set(o))
    print(f"Haiku records: {len(h)}")
    print(f"Opus records:  {len(o)}")
    print(f"Common ids:    {len(common)}")
    print()

    agree_full = 0
    agree_partial = 0
    disagree = 0

    h_axes = {f"A{i}": 0 for i in range(1, 7)}
    o_axes = {f"A{i}": 0 for i in range(1, 7)}
    both_axes = {f"A{i}": 0 for i in range(1, 7)}
    disagreements = []

    for pid in common:
        h_a = set(h[pid].get("axes_touched", []) or [])
        o_a = set(o[pid].get("axes_touched", []) or [])
        for a in h_a:
            if a in h_axes: h_axes[a] += 1
        for a in o_a:
            if a in o_axes: o_axes[a] += 1
        for a in (h_a & o_a):
            if a in both_axes: both_axes[a] += 1
        if h_a == o_a:
            agree_full += 1
        elif h_a & o_a:
            agree_partial += 1
            disagreements.append((pid, h_a, o_a, h[pid]["_paragraph"][:200]))
        else:
            disagree += 1
            disagreements.append((pid, h_a, o_a, h[pid]["_paragraph"][:200]))

    n = max(1, len(common))
    print("=== AGREEMENT ===")
    print(f"  full agreement  (same axes):     {agree_full}/{n} ({100*agree_full/n:.1f}%)")
    print(f"  partial overlap (>=1 axis match): {agree_partial}/{n} ({100*agree_partial/n:.1f}%)")
    print(f"  disjoint        (no overlap):    {disagree}/{n} ({100*disagree/n:.1f}%)")
    print()
    print("=== PER-AXIS HITS ===")
    print(f"  {'axis':6s} {'haiku':>8s} {'opus':>8s} {'both':>8s} {'IoU':>8s}")
    for a in sorted(h_axes):
        union = h_axes[a] + o_axes[a] - both_axes[a]
        iou = both_axes[a] / max(1, union)
        print(f"  {a:6s} {h_axes[a]:>8d} {o_axes[a]:>8d} {both_axes[a]:>8d} {iou:>8.2f}")
    print()
    print("=== DISAGREEMENT EXAMPLES (first 8) ===")
    for pid, ha, oa, snip in disagreements[:8]:
        print(f"  [{pid}]")
        print(f"    haiku: {sorted(ha)}")
        print(f"    opus:  {sorted(oa)}")
        print(f"    par:   {snip}")
        print()


if __name__ == "__main__":
    main()
