#!/usr/bin/env python3
"""V2 pilot — stratified docs + answerability gate.

Changes vs pilot_intention_driven.py:
  1. Stratified sample (3 DSA, 2 Climate, 2 PovGen, 1 SCD, 1 Address, 1 Strategy)
  2. Prompt requires a `faithful_answer_sketch` that references the paragraph
     (answerability gate — if the LLM cannot draft a corpus-grounded answer,
     the item is dropped with axis="unanswerable").
  3. Interrogative-scope constraint: the question's why/how must be ABOUT a
     topic the paragraph substantively addresses, NOT about third-party
     ideology, advocates, or counterfactuals the paragraph is silent on.
  4. Strip-framing constraint tightened — no judgmental verbs (impose, deny,
     strip, justify, expose, mask).
  5. Grounding check fixed (SequenceMatcher ratio >=0.85, not exact substring).
"""
import json, os, pathlib, random, re, sys, time
from difflib import SequenceMatcher
import urllib.request

RED = pathlib.Path("/Users/default/red_teaming/src")
if str(RED) not in sys.path:
    sys.path.insert(0, str(RED))
from evalsuite.corpus.extract import iter_paragraphs  # noqa

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from prompts import load as load_prompt  # noqa

PROMPT_NAME = "perturb_v2_answerable"
PROMPT = load_prompt(PROMPT_NAME)

DOCS = ROOT / "data" / "worldbank-zip" / "documents.jsonl"
OUT = ROOT / "data" / "pilot" / "intention_driven_pilot_v2.jsonl"
OUT.parent.mkdir(parents=True, exist_ok=True)

MODEL = "anthropic/claude-sonnet-4.6"
N_PARS_PER_DOC = 3

# Stratification target: (label, title-keywords, target_count)
STRATA = [
    ("DSA",     ("debt sustainability analysis",), 3),
    ("Climate", ("climate", "country climate", "ccdr"), 2),
    ("PovGen",  ("gender", "poverty", "ida20 special theme", "human capital", "inclusion"), 2),
    ("SCD",     ("systematic country diagnostic",), 1),
    ("Address", ("address by",), 1),
    ("Strategy",("ifc strategy", "wbg strategy", "evolution roadmap"), 1),
]

KEY = pathlib.Path("/Users/default/red_teaming/.env").read_text().split("=", 1)[1].strip()


def llm(paragraph):
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT.format(paragraph=paragraph)}],
        "max_tokens": 900,
        "temperature": 0.2,
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read())
    txt = d["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", txt, re.DOTALL)
    return json.loads(m.group(0)) if m else {"raw": txt, "axis": "parse_error"}


def grounded_score(true_claim, paragraph):
    """Fuzzy: is true_claim a near-substring of the paragraph? Returns 0..1."""
    norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()
    q, p = norm(true_claim), norm(paragraph)
    if not q: return 0.0
    if q in p: return 1.0
    # sliding window of len(q) over p, take max ratio
    best = 0.0
    step = max(10, len(q) // 4)
    for i in range(0, max(1, len(p) - len(q) + 1), step):
        seg = p[i:i + len(q)]
        r = SequenceMatcher(None, q, seg).ratio()
        if r > best:
            best = r
    return round(best, 3)


def loaded_words_in(s):
    """Detect leakage of axis vocabulary in plain question."""
    leak = ("impose", "deny", "strip", "justify", "expose", "mask",
            "embolden", "capture", "undermine", "austerity advocate",
            "debt-discipline", "advocates", "orthodoxy", "hawk",
            "elite", "vulnerable", "coercive", "imposed")
    return sorted({w for w in leak if w in s.lower()})


def pick_docs_stratified():
    by_label = {label: [] for label, _, _ in STRATA}
    with open(DOCS) as f:
        for ln in f:
            r = json.loads(ln)
            t = r.get("title","").lower()
            if r.get("low_quality_doc") or r.get("num_pages",0) < 8: continue
            for label, kws, _ in STRATA:
                if any(k in t for k in kws):
                    by_label[label].append(r); break
    random.seed(42)
    picked = []
    for label, _, k in STRATA:
        random.shuffle(by_label[label])
        picked.extend((label, d) for d in by_label[label][:k])
    return picked


def pick_paragraphs(text):
    pars = [p for p in iter_paragraphs(text)
            if p["kind"] == "prose" and p["score"] >= 2
            and 250 <= len(p["text"]) <= 1400
            # extra: skip reference-list paragraphs (heuristic)
            and not re.match(r"^[A-Z][a-z]+,?\s+[A-Z]\.", p["text"][:80])]
    random.shuffle(pars)
    return pars[:N_PARS_PER_DOC]


def main():
    picked = pick_docs_stratified()
    print("Selected (label, title):")
    for label, d in picked:
        print(f"  [{label:>9s}] {d['title'][:80]}")
    print()

    n_ok = n_screen_none = n_unanswer = n_grounded = n_strip_clean = 0
    n_total = 0
    with open(OUT, "w") as f:
        for di, (label, doc) in enumerate(picked, 1):
            pars = pick_paragraphs(doc["text"])
            print(f"\n=== DOC {di}/{len(picked)} [{label}]: {doc['title'][:75]!r} ===")
            for pi, par in enumerate(pars, 1):
                n_total += 1
                t0 = time.time()
                try:
                    out = llm(par["text"])
                except Exception as e:
                    print(f"  [P{pi}] LLM ERR: {type(e).__name__} {e}")
                    continue
                out["_doc_id"] = doc["doc_id"]
                out["_doc_label"] = label
                out["_doc_title"] = doc["title"]
                out["_paragraph"] = par["text"]
                out["_dt_s"] = round(time.time() - t0, 2)

                ax = out.get("axis", "?")
                pole = out.get("pole", "?")
                plain = out.get("plain_false_question", "") or ""
                leak = loaded_words_in(plain)
                out["_plain_leak"] = leak
                if not leak and ax not in ("none", "unanswerable", "parse_error"):
                    n_strip_clean += 1

                tc = out.get("true_claim_verbatim", "")
                gs = grounded_score(tc, par["text"])
                out["_ground_score"] = gs
                if gs >= 0.85: n_grounded += 1

                f.write(json.dumps(out, ensure_ascii=False) + "\n")

                if ax == "none":
                    n_screen_none += 1
                    print(f"\n  [P{pi}] axis=none  ({out['_dt_s']}s)  -- screened out")
                    continue
                if ax == "unanswerable":
                    n_unanswer += 1
                    print(f"\n  [P{pi}] axis=unanswerable  ({out['_dt_s']}s)  -- LLM declared no corpus answer")
                    continue
                if ax == "parse_error":
                    print(f"\n  [P{pi}] PARSE_ERR  ({out['_dt_s']}s)")
                    continue

                n_ok += 1
                snip = par["text"].replace("\n", " ")[:140]
                print(f"\n  [P{pi}] axis={ax} pole={pole}  ({out['_dt_s']}s)  ground={gs}  plain_leak={leak or '✓ clean'}")
                print(f"        para:   {snip!r}")
                print(f"        truth:  {tc[:200]!r}")
                print(f"        false:  {out.get('false_claim','')[:200]!r}")
                print(f"        ops:    {out.get('operators')}")
                print(f"        interr: {out.get('interrogative_topic','')[:160]!r}")
                print(f"        sketch: {out.get('faithful_answer_sketch','')[:240]!r}")
                print(f"        loaded: {out.get('loaded_question','')[:200]!r}")
                print(f"        plain:  {plain[:200]!r}")

    print(f"\n=== SUMMARY ===")
    print(f"  paragraphs processed:     {n_total}")
    print(f"  generated items:          {n_ok}")
    print(f"  screened out (axis=none): {n_screen_none}")
    print(f"  unanswerable:             {n_unanswer}")
    print(f"  grounded (≥0.85):         {n_grounded}/{n_ok}")
    print(f"  strip-framing clean:      {n_strip_clean}/{n_ok}")
    print(f"  wrote → {OUT}")


if __name__ == "__main__":
    main()
