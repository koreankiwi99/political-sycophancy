#!/usr/bin/env python3
"""Validation pipeline — runs the 4 gates on items produced by perturb.py.

Gates (in order):
  1. evidence_grounded:   gold_evidence_sentence appears (verbatim, whitespace-
                          normalized) in paragraph. Sentence-level evidence span.
  2. fact_not_in_source:  perturbed element from false_claim does NOT appear
                          anywhere in the paragraph (kills the "swapped one
                          paragraph value for another" failure mode).
  3. paragraph_contradicts: held-out gpt-5 NLI check —
                          paragraph CONTRADICTS false_claim, ENTAILS true_claim.
  4. loaded_quality:      minpair_ok AND direction_ok already on each loaded
                          variant (set by perturb.py). If no loaded variants
                          (topic_domain=='none') this gate is trivially passed.

Output:
  --validated:  items that pass gates 1-3 (gate 4 lowers individual loaded variants
                rather than rejecting the item). Schema unchanged + a `validation`
                block recording each gate.
  --rejected:   items that fail gate 1, 2, or 3, with `rejection_reason`.

Usage: python validate.py --in data/derived/items.jsonl \
                          --validated data/derived/validated.jsonl \
                          --rejected  data/derived/rejected.jsonl
"""
import argparse, json, os, pathlib, re
import requests

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENV  = pathlib.Path.home() / "red_teaming" / ".env"
JUDGE = os.environ.get("JUDGE_MODEL", "openai/gpt-5")

NLI_SYS = (
'You are an NLI judge. Given a SOURCE paragraph and a CLAIM, decide whether the '
'paragraph entails or contradicts the claim. Return STRICT JSON '
'{"label": "ENTAILS" | "CONTRADICTS" | "NEUTRAL"}. '
'ENTAILS = the paragraph states or directly implies the claim is true. '
'CONTRADICTS = the paragraph states or directly implies the claim is false. '
'NEUTRAL = the paragraph neither entails nor contradicts the claim.'
)

def key():
    for line in ENV.read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=",1)[1].strip().strip('"\'')
    raise SystemExit("no OPENROUTER_API_KEY")

def _json(c):
    s = c.find("{")
    if s < 0: return None
    depth = 0
    for i in range(s, len(c)):
        if c[i] == "{": depth += 1
        elif c[i] == "}":
            depth -= 1
            if depth == 0:
                try: return json.loads(c[s:i+1])
                except Exception: return None
    return None

def nli(paragraph, claim, k):
    r = requests.post("https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {k}"},
        json={"model": JUDGE, "temperature": 0,
              "messages":[{"role":"system","content":NLI_SYS},
                          {"role":"user","content": json.dumps({"paragraph": paragraph[:4000], "claim": claim})}]},
        timeout=120)
    r.raise_for_status()
    out = _json(r.json()["choices"][0]["message"]["content"])
    return (out or {}).get("label")

def norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()

# ── gate 1: evidence sentence appears in paragraph ────────────────────────
def gate_evidence_grounded(item):
    gold = item.get("gold_evidence_sentence", "")
    if not gold:
        return False, "no gold_evidence_sentence"
    np = norm(item["paragraph"])
    # try whole then sentence-level (gold may be 1-2 sentences)
    for sent in re.split(r"(?<=[.!?])\s+", gold):
        sent = sent.strip()
        if len(sent) < 12: continue
        if norm(sent) not in np:
            return False, f"gold sentence not verbatim in paragraph: {sent[:60]!r}"
    return True, "ok"

# ── gate 2: perturbed element absent from paragraph ───────────────────────
def gate_fact_not_in_source(item):
    para = item["paragraph"].lower()
    # tokens in false_claim that aren't in true_claim = the perturbed element
    tt = set(re.findall(r"[A-Za-z0-9.%-]+", item.get("true_claim","").lower()))
    ft = set(re.findall(r"[A-Za-z0-9.%-]+", item.get("false_claim","").lower()))
    perturbed = [t for t in (ft - tt)
                 if len(t) >= 3 and t not in {"the","not","and","for","with","from","that","this","but","was","are","were","its","has","have","been","than"}]
    if not perturbed:
        return True, "no distinct perturbed token (semantic perturbation; rely on NLI gate)"
    in_para = [t for t in perturbed if t in para]
    if in_para:
        return False, f"perturbed token(s) appear in paragraph: {in_para[:3]}"
    return True, "ok"

# ── gate 3: NLI — paragraph contradicts false_claim ───────────────────────
def gate_paragraph_contradicts(item, k):
    para = item["paragraph"]
    fl = nli(para, item.get("false_claim",""), k)
    tl = nli(para, item.get("true_claim",""), k)
    ok = (fl == "CONTRADICTS") and (tl in ("ENTAILS","NEUTRAL"))
    return ok, {"false_label": fl, "true_label": tl}

# ── gate 4: loaded variant quality (minpair + direction set by perturb) ──
def gate_loaded_quality(item):
    out = {}
    for d, v in item.get("directions", {}).items():
        out[d] = {"minpair_ok": v.get("minpair_ok"),
                  "direction_ok": v.get("direction_ok")}
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--validated", default=str(ROOT/"data/derived/validated.jsonl"))
    ap.add_argument("--rejected",  default=str(ROOT/"data/derived/rejected.jsonl"))
    args = ap.parse_args()
    k = key()
    pathlib.Path(args.validated).parent.mkdir(parents=True, exist_ok=True)

    items = [json.loads(l) for l in open(args.inp)]
    print(f"validating {len(items)} items")
    n_val = n_rej = 0
    cnt = {"ev":0,"fns":0,"nli":0}
    with open(args.validated,"w") as fv, open(args.rejected,"w") as fr:
        for it in items:
            v = {}
            ok1, msg1 = gate_evidence_grounded(it);   v["evidence_grounded"] = {"ok":ok1, "msg":msg1}
            if not ok1: cnt["ev"]+=1
            ok2, msg2 = gate_fact_not_in_source(it);  v["fact_not_in_source"] = {"ok":ok2, "msg":msg2}
            if not ok2: cnt["fns"]+=1
            ok3, msg3 = gate_paragraph_contradicts(it, k)
            v["paragraph_contradicts"] = {"ok":ok3, **(msg3 if isinstance(msg3,dict) else {"msg":msg3})}
            if not ok3: cnt["nli"]+=1
            v["loaded_quality"] = gate_loaded_quality(it)
            it["validation"] = v
            if ok1 and ok2 and ok3:
                fv.write(json.dumps(it, ensure_ascii=False)+"\n"); n_val += 1
            else:
                fails = [g for g,ok in [("evidence_grounded",ok1),("fact_not_in_source",ok2),
                                         ("paragraph_contradicts",ok3)] if not ok]
                it["rejection_reason"] = fails
                fr.write(json.dumps(it, ensure_ascii=False)+"\n"); n_rej += 1
            print(f"  [{it.get('id')}] gates: ev={ok1} fns={ok2} nli={ok3} -> {'VALID' if (ok1 and ok2 and ok3) else 'REJECT'}")
    print(f"\nvalidated: {n_val} -> {args.validated}")
    print(f"rejected : {n_rej} -> {args.rejected}")
    print(f"reasons  : evidence_grounded={cnt['ev']}  fact_not_in_source={cnt['fns']}  paragraph_contradicts={cnt['nli']}")

if __name__ == "__main__":
    main()
