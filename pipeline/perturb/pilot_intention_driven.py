#!/usr/bin/env python3
"""Pilot the intention-driven perturbation design on 10 WB docs.

For each doc -> sample up to 3 prose paragraphs -> call Sonnet with the
intention-driven prompt (controversy-screen + axis/pole + congenial false
premise + framing-strip). Print results so we can see whether the triples
are meaningful before committing to the design.

Run:
  PYTHONPATH=/Users/default/red_teaming/src \\
  /Users/default/red_teaming/.venv/bin/python \\
  pipeline/perturb/pilot_intention_driven.py
"""
import json, os, pathlib, random, re, sys, time
import urllib.request, urllib.error

# Make the corpus helpers importable
RED = pathlib.Path("/Users/default/red_teaming/src")
if str(RED) not in sys.path:
    sys.path.insert(0, str(RED))
from evalsuite.corpus.extract import iter_paragraphs  # noqa

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from prompts import load as load_prompt  # noqa

PROMPT_NAME = "perturb_v1_intention_driven"
PROMPT = load_prompt(PROMPT_NAME)

DOCS = ROOT / "data" / "worldbank-zip" / "documents.jsonl"
OUT = ROOT / "data" / "pilot" / "intention_driven_pilot.jsonl"
OUT.parent.mkdir(parents=True, exist_ok=True)

# Skip admin/governance docs; want substantive analytical / country content
SKIP_KW = ("annual meetings", "summary proceedings", "compensation",
           "awards alloc", "boards of governors", "audit committee",
           "budget committee", "human resources committee", "staff",
           "replenishment", "board of governors resolution",
           "minutes of", "membership term", "standing committees")
WANT_KW = ("country", "econom", "poverty", "debt", "fiscal", "growth",
           "trade", "development", "gdp", "inequality", "expenditure",
           "tax", "climate", "structural", "subsidy", "conditionality",
           "structural", "diagnostic", "partnership framework")

MODEL = "anthropic/claude-sonnet-4.6"
N_DOCS = 10
N_PARS_PER_DOC = 3

KEY = pathlib.Path("/Users/default/red_teaming/.env").read_text().split("=", 1)[1].strip()


def llm(paragraph):
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT.format(paragraph=paragraph)}],
        "max_tokens": 700,
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


def grounded(true_claim, paragraph):
    """Does true_claim_verbatim actually appear in the paragraph (modulo whitespace)?"""
    norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()
    return norm(true_claim) in norm(paragraph)


def pick_docs():
    docs = []
    with open(DOCS) as f:
        for line in f:
            r = json.loads(line)
            t = r.get("title", "").lower()
            if any(s in t for s in SKIP_KW):
                continue
            if not any(w in t for w in WANT_KW):
                continue
            if r.get("low_quality_doc"):
                continue
            if r.get("num_pages", 0) < 8:
                continue
            docs.append(r)
    random.seed(42)
    random.shuffle(docs)
    return docs[:N_DOCS]


def pick_paragraphs(text):
    pars = [p for p in iter_paragraphs(text) if p["kind"] == "prose" and p["score"] >= 2 and 200 <= len(p["text"]) <= 1400]
    random.shuffle(pars)
    return pars[:N_PARS_PER_DOC]


def main():
    docs = pick_docs()
    print(f"Selected {len(docs)} substantive docs:\n")
    for d in docs:
        print(f"  - {d['title'][:80]}")
    print()

    n_ok = n_screen_none = n_grounded = 0
    with open(OUT, "w") as f:
        for di, doc in enumerate(docs, 1):
            pars = pick_paragraphs(doc["text"])
            print(f"\n=== DOC {di}/{len(docs)}: {doc['title'][:80]!r} ({len(pars)} paragraphs sampled) ===")
            for pi, par in enumerate(pars, 1):
                t0 = time.time()
                try:
                    out = llm(par["text"])
                except Exception as e:
                    print(f"  [P{pi}] LLM ERR: {type(e).__name__} {e}")
                    continue
                out["_doc_id"] = doc["doc_id"]
                out["_doc_title"] = doc["title"]
                out["_paragraph"] = par["text"]
                out["_para_score"] = par["score"]
                out["_dt_s"] = round(time.time() - t0, 2)
                if grounded(out.get("true_claim_verbatim", ""), par["text"]):
                    out["_grounded"] = True
                    n_grounded += 1
                else:
                    out["_grounded"] = False
                if out.get("axis") == "none":
                    n_screen_none += 1
                else:
                    n_ok += 1
                f.write(json.dumps(out, ensure_ascii=False) + "\n")

                # Pretty-print for the user
                ax = out.get("axis", "?")
                pole = out.get("pole", "?")
                print(f"\n  [P{pi}] axis={ax} pole={pole}  ({out['_dt_s']}s)  grounded={out.get('_grounded')}")
                if ax == "none":
                    print(f"        (screened out — paragraph not on any axis)")
                    continue
                snip = par["text"].replace("\n", " ")[:140]
                print(f"        para:    {snip!r}")
                print(f"        truth:   {out.get('true_claim_verbatim', '')[:200]!r}")
                print(f"        false:   {out.get('false_claim', '')[:200]!r}")
                print(f"        ops:     {out.get('operators')}")
                print(f"        loaded:  {out.get('loaded_question', '')[:200]!r}")
                print(f"        plain:   {out.get('plain_false_question', '')[:200]!r}")
                print(f"        topic:   {out.get('topic_phrase', '')}")

    print(f"\n\n=== SUMMARY ===")
    print(f"  generated:    {n_ok}")
    print(f"  screened out: {n_screen_none}")
    print(f"  grounded:     {n_grounded}/{n_ok}")
    print(f"  wrote → {OUT}")


if __name__ == "__main__":
    main()
