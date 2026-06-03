#!/usr/bin/env python3
"""V3 pilot — 3 stages, twin-pole loaded, control generated WITH (not from) loaded.

Stages (one LLM call each):
  A. Screen (Haiku):  axis-touch yes/no.  Drops ~50% of paragraphs.
  B. Generate (Sonnet): intention-bound atomic; produces PLAIN + LOADED_pole_A + LOADED_pole_B
                        as TWIN outputs sharing the same false_claim verbatim and same interrogative.
  C. Verify (Haiku):  C1 verbatim-share · C2 plain-clean · C3 poleA-rhetoric · C4 poleB-rhetoric-and-distinct.

Same 10 stratified docs as v2 → direct v2 vs v3 comparison.
"""
import json, pathlib, random, re, sys, time
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

PROMPT_SCREEN   = load_prompt("v3_screen_axis_touch")
PROMPT_GENERATE = load_prompt("v3_generate_intention_bound")
PROMPT_VERIFY   = load_prompt("v3_verify_item")

DOCS = ROOT / "data" / "worldbank-zip" / "documents.jsonl"
OUT  = ROOT / "data" / "pilot" / "intention_driven_pilot_v3.jsonl"
OUT.parent.mkdir(parents=True, exist_ok=True)

MODEL_HAIKU  = "anthropic/claude-haiku-4.5"
MODEL_SONNET = "anthropic/claude-sonnet-4.6"
N_PARS_PER_DOC = 3

STRATA = [
    ("DSA",     ("debt sustainability analysis",), 3),
    ("Climate", ("climate", "country climate", "ccdr"), 2),
    ("PovGen",  ("gender", "poverty", "ida20 special theme", "human capital", "inclusion"), 2),
    ("SCD",     ("systematic country diagnostic",), 1),
    ("Address", ("address by",), 1),
    ("Strategy",("ifc strategy", "wbg strategy", "evolution roadmap"), 1),
]

KEY = pathlib.Path("/Users/default/red_teaming/.env").read_text().split("=", 1)[1].strip()


def call(model, user_msg, max_tokens=900, temperature=0.2):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": user_msg}],
        "max_tokens": max_tokens,
        "temperature": temperature,
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
    return json.loads(m.group(0)) if m else {"_raw": txt}


def stage_a_screen(paragraph):
    return call(MODEL_HAIKU, PROMPT_SCREEN.format(paragraph=paragraph),
                max_tokens=200, temperature=0)


def stage_b_generate(paragraph, axes_touched):
    msg = PROMPT_GENERATE.format(paragraph=paragraph, axes_touched=axes_touched)
    return call(MODEL_SONNET, msg, max_tokens=1100, temperature=0.2)


def stage_c_verify(item):
    msg = PROMPT_VERIFY.format(
        axis=item.get("axis", ""),
        pole_A_label=item.get("pole_A_label", ""),
        pole_B_label=item.get("pole_B_label", ""),
        false_claim=item.get("false_claim", ""),
        plain_question=item.get("plain_question", ""),
        loaded_pole_A_question=item.get("loaded_pole_A_question", ""),
        loaded_pole_B_question=item.get("loaded_pole_B_question", ""),
    )
    return call(MODEL_HAIKU, msg, max_tokens=300, temperature=0)


def grounded_score(true_claim, paragraph):
    norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()
    q, p = norm(true_claim), norm(paragraph)
    if not q: return 0.0
    if q in p: return 1.0
    best, step = 0.0, max(10, len(q) // 4)
    for i in range(0, max(1, len(p) - len(q) + 1), step):
        seg = p[i:i + len(q)]
        r = SequenceMatcher(None, q, seg).ratio()
        if r > best: best = r
    return round(best, 3)


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
    random.seed(42)  # same seed as v2 → same docs
    picked = []
    for label, _, k in STRATA:
        random.shuffle(by_label[label])
        picked.extend((label, d) for d in by_label[label][:k])
    return picked


def pick_paragraphs(text):
    pars = [p for p in iter_paragraphs(text)
            if p["kind"] == "prose" and p["score"] >= 2
            and 250 <= len(p["text"]) <= 1400
            # skip citation/reference-list paragraphs (heuristic)
            and not re.match(r"^[A-Z][a-zA-Z]+,?\s+[A-Z]\.", p["text"][:80])
            and p["text"].count(". 20") + p["text"].count(". 19") < 3]  # multiple year-period patterns = ref list
    random.seed(42)  # same seed for paragraph pick too
    random.shuffle(pars)
    return pars[:N_PARS_PER_DOC]


def main():
    picked = pick_docs_stratified()
    print("Selected (label, title):")
    for label, d in picked:
        print(f"  [{label:>9s}] {d['title'][:75]}")
    print()

    counters = {
        "n_total": 0, "n_screened": 0, "n_unanswer": 0, "n_not_twin": 0,
        "n_generated": 0, "n_grounded": 0, "n_C1": 0, "n_C2": 0, "n_C3": 0, "n_C4": 0,
        "n_all_pass": 0,
    }

    with open(OUT, "w") as f:
        for di, (label, doc) in enumerate(picked, 1):
            pars = pick_paragraphs(doc["text"])
            print(f"\n=== DOC {di}/{len(picked)} [{label}]: {doc['title'][:70]!r} ===")
            for pi, par in enumerate(pars, 1):
                counters["n_total"] += 1
                t0 = time.time()

                # Stage A
                try:
                    screen = stage_a_screen(par["text"])
                except Exception as e:
                    print(f"  [P{pi}] stage A error: {e}"); continue
                axes = screen.get("axes_touched", [])
                if not axes:
                    counters["n_screened"] += 1
                    print(f"\n  [P{pi}] SCREEN: none  reason={screen.get('reason','')[:90]!r}")
                    continue

                # Stage B
                try:
                    gen = stage_b_generate(par["text"], json.dumps(axes))
                except Exception as e:
                    print(f"  [P{pi}] stage B error: {e}"); continue
                ax = gen.get("axis","?")
                if ax == "unanswerable":
                    counters["n_unanswer"] += 1
                    print(f"\n  [P{pi}] axes_touched={axes} → unanswerable")
                    continue
                if ax == "not_twin_framable":
                    counters["n_not_twin"] += 1
                    print(f"\n  [P{pi}] axes_touched={axes} → not twin-framable")
                    continue
                counters["n_generated"] += 1

                # Grounding check
                tc = gen.get("true_claim_verbatim","")
                gs = grounded_score(tc, par["text"])
                gen["_ground_score"] = gs
                if gs >= 0.85: counters["n_grounded"] += 1

                # Stage C
                try:
                    ver = stage_c_verify(gen)
                except Exception as e:
                    ver = {"_error": str(e)}
                gen["_verify"] = ver
                if ver.get("C1_verbatim_share"): counters["n_C1"] += 1
                if ver.get("C2_plain_clean"):    counters["n_C2"] += 1
                if ver.get("C3_poleA_loaded"):   counters["n_C3"] += 1
                if ver.get("C4_poleB_loaded_and_distinct"): counters["n_C4"] += 1
                all_pass = all([ver.get(k) for k in ("C1_verbatim_share","C2_plain_clean","C3_poleA_loaded","C4_poleB_loaded_and_distinct")])
                if all_pass: counters["n_all_pass"] += 1

                gen["_doc_id"] = doc["doc_id"]
                gen["_doc_label"] = label
                gen["_doc_title"] = doc["title"]
                gen["_paragraph"] = par["text"]
                gen["_dt_s"] = round(time.time() - t0, 2)
                f.write(json.dumps(gen, ensure_ascii=False) + "\n")

                pA = gen.get("pole_A_label","?"); pB = gen.get("pole_B_label","?")
                print(f"\n  [P{pi}] axis={ax}  poles={pA}/{pB}  ({gen['_dt_s']}s)  ground={gs}  "
                      f"verify=C1{int(bool(ver.get('C1_verbatim_share')))}"
                      f"C2{int(bool(ver.get('C2_plain_clean')))}"
                      f"C3{int(bool(ver.get('C3_poleA_loaded')))}"
                      f"C4{int(bool(ver.get('C4_poleB_loaded_and_distinct')))}"
                      f"{' [PASS]' if all_pass else ''}")
                snip = par["text"].replace("\n"," ")[:120]
                print(f"        para:   {snip!r}")
                print(f"        truth:  {tc[:180]!r}")
                print(f"        false:  {gen.get('false_claim','')[:180]!r}")
                print(f"        ops:    {gen.get('operators')}")
                print(f"        sketch: {gen.get('faithful_answer_sketch','')[:200]!r}")
                print(f"        plain:  {gen.get('plain_question','')[:200]!r}")
                print(f"        load_A: {gen.get('loaded_pole_A_question','')[:200]!r}")
                print(f"        load_B: {gen.get('loaded_pole_B_question','')[:200]!r}")

    print(f"\n\n=== SUMMARY ===")
    print(f"  paragraphs processed:    {counters['n_total']}")
    print(f"  screened out:            {counters['n_screened']}")
    print(f"  unanswerable:            {counters['n_unanswer']}")
    print(f"  not twin-framable:       {counters['n_not_twin']}")
    print(f"  generated items:         {counters['n_generated']}")
    print(f"  grounded (>=0.85):       {counters['n_grounded']}/{counters['n_generated']}")
    print(f"  verify C1 verbatim:      {counters['n_C1']}/{counters['n_generated']}")
    print(f"  verify C2 plain-clean:   {counters['n_C2']}/{counters['n_generated']}")
    print(f"  verify C3 poleA-loaded:  {counters['n_C3']}/{counters['n_generated']}")
    print(f"  verify C4 poleB-distinct:{counters['n_C4']}/{counters['n_generated']}")
    print(f"  all-checks PASS:         {counters['n_all_pass']}/{counters['n_generated']}")
    print(f"  wrote -> {OUT}")


if __name__ == "__main__":
    main()
