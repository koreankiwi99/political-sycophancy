#!/usr/bin/env python3
"""V4 pilot — system+user separation, shared axes, anchor-paper-grounded.

Changes vs v3:
  - Each stage now uses Anthropic-style system+user messages, not user-only.
  - The 5-axis definitions live in prompts/shared_axes.txt (single source
    of truth) and are interpolated into every stage's system block.
  - The (axis, pole_A, pole_B) tuple table is hardcoded — fixes the
    pole-label mismatch bug from v3 (e.g., A1 returned with A5's poles).
  - JSON-only instruction is at the TOP of every system prompt — fixes
    v3's prose-narration parse failures (items #4 #6 #15).
  - max_tokens raised to 1500.
  - Prompt-caching annotation on system blocks (free on OpenRouter for
    Claude models; ~5× cost reduction at scale since the system block
    is identical across all calls of each stage).

Same 10 stratified docs / same seed as v2 / v3 — direct comparison.
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
from prompts import load_pair, load_shared  # noqa

# ── Load prompts once ────────────────────────────────────────────────
AXES_DEF = load_shared("shared_axes")
SCREEN_SYS_TMPL, SCREEN_USR_TMPL   = load_pair("v4a_screen")
GEN_SYS_TMPL,    GEN_USR_TMPL      = load_pair("v4b_generate")
VERIFY_SYS_TMPL, VERIFY_USR_TMPL   = load_pair("v4c_verify")

SCREEN_SYS = SCREEN_SYS_TMPL.format(axes_definitions=AXES_DEF)
GEN_SYS    = GEN_SYS_TMPL.format(axes_definitions=AXES_DEF)
VERIFY_SYS = VERIFY_SYS_TMPL.format(axes_definitions=AXES_DEF)

DOCS = ROOT / "data" / "worldbank-zip" / "documents.jsonl"

MODEL_HAIKU  = "anthropic/claude-haiku-4.5"
MODEL_SONNET = "anthropic/claude-sonnet-4.6"
N_PARS_PER_DOC = 3

# Override via env var: GEN_MODEL=openai/gpt-5  python pilot_v4_systemuser.py
import os as _os
GEN_MODEL = _os.environ.get("GEN_MODEL", MODEL_SONNET)
# Output filename keys on the generator model so swaps don't collide
_model_slug = GEN_MODEL.replace("/", "_").replace(".", "")
OUT = ROOT / "data" / "pilot" / f"intention_driven_pilot_v4_{_model_slug}.jsonl"
OUT.parent.mkdir(parents=True, exist_ok=True)

STRATA = [
    ("DSA",     ("debt sustainability analysis",), 3),
    ("Climate", ("climate", "country climate", "ccdr"), 2),
    ("PovGen",  ("gender", "poverty", "ida20 special theme", "human capital", "inclusion"), 2),
    ("SCD",     ("systematic country diagnostic",), 1),
    ("Address", ("address by",), 1),
    ("Strategy",("ifc strategy", "wbg strategy", "evolution roadmap"), 1),
]

KEY = pathlib.Path("/Users/default/red_teaming/.env").read_text().split("=", 1)[1].strip()


def call(model, system, user, max_tokens=1500, temperature=0.2):
    """Send a system+user pair; system block is cache-flagged so identical
    repeated system content is billed at the cache-hit rate (≈10% of full)."""
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system",
             "content": [{"type": "text", "text": system,
                          "cache_control": {"type": "ephemeral"}}]},
            {"role": "user", "content": user},
        ],
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
    return call(MODEL_HAIKU, SCREEN_SYS,
                SCREEN_USR_TMPL.format(paragraph=paragraph),
                max_tokens=300, temperature=0)


def stage_b_generate(paragraph, axes_touched):
    user = GEN_USR_TMPL.format(paragraph=paragraph, axes_touched=axes_touched)
    return call(GEN_MODEL, GEN_SYS, user, max_tokens=1500, temperature=0.2)


def stage_c_verify(item):
    user = VERIFY_USR_TMPL.format(
        axis=item.get("axis", ""),
        pole_A_label=item.get("pole_A_label", ""),
        pole_B_label=item.get("pole_B_label", ""),
        false_claim=item.get("false_claim", ""),
        plain_question=item.get("plain_question", ""),
        loaded_pole_A_question=item.get("loaded_pole_A_question", ""),
        loaded_pole_B_question=item.get("loaded_pole_B_question", ""),
    )
    return call(MODEL_HAIKU, VERIFY_SYS, user, max_tokens=400, temperature=0)


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


VALID_POLES = {
    "A1": ("orthodox", "heterodox"),
    "A2": ("north", "south"),
    "A3": ("growth", "equity"),
    "A4": ("climate-orthodox", "climate-justice"),
    "A5": ("debt-discipline", "fiscal-space"),
}


def check_pole_consistency(item):
    """Verify that pole labels match the chosen axis (the v3 bug)."""
    ax = item.get("axis","")
    if ax not in VALID_POLES: return True
    expected = set(VALID_POLES[ax])
    actual = {item.get("pole_A_label"), item.get("pole_B_label")}
    return expected == actual


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
            and not re.match(r"^[A-Z][a-zA-Z]+,?\s+[A-Z]\.", p["text"][:80])
            and p["text"].count(". 20") + p["text"].count(". 19") < 3]
    random.seed(42)
    random.shuffle(pars)
    return pars[:N_PARS_PER_DOC]


def main():
    picked = pick_docs_stratified()
    print(f"v4 pilot — system+user separation, shared axes")
    print(f"Selected (label, title):")
    for label, d in picked:
        print(f"  [{label:>9s}] {d['title'][:75]}")
    print()

    c = {k: 0 for k in (
        "n_total","n_screened","n_unanswer","n_not_twin","n_generated",
        "n_grounded","n_pole_consistent","n_C1","n_C2","n_C3","n_C4","n_all_pass",
        "n_parse_fail",
    )}

    with open(OUT, "w") as f:
        for di, (label, doc) in enumerate(picked, 1):
            pars = pick_paragraphs(doc["text"])
            print(f"\n=== DOC {di}/{len(picked)} [{label}]: {doc['title'][:70]!r} ===")
            for pi, par in enumerate(pars, 1):
                c["n_total"] += 1
                t0 = time.time()
                # Stage A
                try:
                    screen = stage_a_screen(par["text"])
                except Exception as e:
                    print(f"  [P{pi}] stage A error: {e}"); continue
                axes = screen.get("axes_touched", [])
                if not axes:
                    c["n_screened"] += 1
                    print(f"\n  [P{pi}] SCREEN: none  reason={screen.get('reason','')[:90]!r}")
                    continue
                # Stage B
                try:
                    gen = stage_b_generate(par["text"], json.dumps(axes))
                except Exception as e:
                    print(f"  [P{pi}] stage B error: {e}"); continue
                if "_raw" in gen:
                    c["n_parse_fail"] += 1
                    print(f"\n  [P{pi}] axes_touched={axes} → PARSE FAIL")
                    continue
                ax = gen.get("axis","?")
                if ax == "unanswerable":
                    c["n_unanswer"] += 1; print(f"\n  [P{pi}] → unanswerable"); continue
                if ax == "not_twin_framable":
                    c["n_not_twin"] += 1; print(f"\n  [P{pi}] → not_twin_framable"); continue
                c["n_generated"] += 1
                # Quality checks
                tc = gen.get("true_claim_verbatim","")
                gs = grounded_score(tc, par["text"]); gen["_ground_score"] = gs
                if gs >= 0.85: c["n_grounded"] += 1
                pole_ok = check_pole_consistency(gen)
                gen["_pole_consistent"] = pole_ok
                if pole_ok: c["n_pole_consistent"] += 1
                # Stage C
                try:
                    ver = stage_c_verify(gen)
                except Exception as e:
                    ver = {"_error": str(e)}
                gen["_verify"] = ver
                if ver.get("C1_verbatim_share"): c["n_C1"] += 1
                if ver.get("C2_plain_clean"):    c["n_C2"] += 1
                if ver.get("C3_poleA_loaded"):   c["n_C3"] += 1
                if ver.get("C4_poleB_loaded_and_distinct"): c["n_C4"] += 1
                all_pass = all(ver.get(k) for k in
                    ("C1_verbatim_share","C2_plain_clean","C3_poleA_loaded","C4_poleB_loaded_and_distinct"))
                if all_pass and pole_ok: c["n_all_pass"] += 1
                gen.update({"_doc_id": doc["doc_id"], "_doc_label": label,
                            "_doc_title": doc["title"], "_paragraph": par["text"],
                            "_dt_s": round(time.time() - t0, 2)})
                f.write(json.dumps(gen, ensure_ascii=False) + "\n")

                pA, pB = gen.get("pole_A_label","?"), gen.get("pole_B_label","?")
                print(f"\n  [P{pi}] axis={ax}  poles={pA}↔{pB}  ({gen['_dt_s']}s)  "
                      f"ground={gs}  pole_OK={pole_ok}  "
                      f"C1{int(bool(ver.get('C1_verbatim_share')))}"
                      f"C2{int(bool(ver.get('C2_plain_clean')))}"
                      f"C3{int(bool(ver.get('C3_poleA_loaded')))}"
                      f"C4{int(bool(ver.get('C4_poleB_loaded_and_distinct')))}"
                      f"{' [PASS]' if all_pass and pole_ok else ''}")
                snip = par["text"].replace("\n"," ")[:120]
                print(f"        para:   {snip!r}")
                print(f"        truth:  {tc[:180]!r}")
                print(f"        false:  {gen.get('false_claim','')[:180]!r}")
                print(f"        ops:    {gen.get('operators')}")
                print(f"        plain:  {gen.get('plain_question','')[:200]!r}")
                print(f"        load_A: {gen.get('loaded_pole_A_question','')[:200]!r}")
                print(f"        load_B: {gen.get('loaded_pole_B_question','')[:200]!r}")

    n_gen = max(1, c['n_generated'])
    print(f"\n\n=== SUMMARY ===")
    print(f"  paragraphs processed:           {c['n_total']}")
    print(f"  screened out (no axis):         {c['n_screened']}")
    print(f"  parse fail (Stage B):           {c['n_parse_fail']}")
    print(f"  unanswerable:                   {c['n_unanswer']}")
    print(f"  not twin-framable:              {c['n_not_twin']}")
    print(f"  generated items:                {c['n_generated']}")
    print(f"  grounded (>=0.85):              {c['n_grounded']}/{n_gen}")
    print(f"  pole-label consistent:          {c['n_pole_consistent']}/{n_gen}")
    print(f"  verify C1 verbatim:             {c['n_C1']}/{n_gen}")
    print(f"  verify C2 plain-clean:          {c['n_C2']}/{n_gen}")
    print(f"  verify C3 poleA-loaded:         {c['n_C3']}/{n_gen}")
    print(f"  verify C4 poleB-distinct:       {c['n_C4']}/{n_gen}")
    print(f"  ALL checks + pole-consistent:   {c['n_all_pass']}/{n_gen}")
    print(f"  wrote -> {OUT}")


if __name__ == "__main__":
    main()
