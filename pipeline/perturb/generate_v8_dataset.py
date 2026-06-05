#!/usr/bin/env python3
"""v8 — 4-stage restructured pipeline.

  Stage A — Screen (Haiku)              → data/derived/v8_stage1_screened.jsonl
  Stage B — Extract + Perturb (Sonnet)  → data/derived/v8_stage2_perturbed.jsonl
  Stage C — Compose + Frame  (Sonnet)   → data/derived/v8_stage3_composed.jsonl
  Stage D — Realism (Sonnet, indep)     → data/derived/v8_stage4_realism.jsonl

Final assembled items: data/dataset/v8_items.jsonl

Each stage persists ALL its outputs (including stop_reasons, errors) so
re-runs can resume per stage and debugging is easy.

Run:
  N_DOCS_PER_DOCTYPE=8  python generate_v8_dataset.py    # pilot 48 docs
  N_DOCS_PER_DOCTYPE=50 python generate_v8_dataset.py    # production 300 docs
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
from prompts import load_pair, load_shared  # noqa

AXES_DEF = load_shared("shared_axes")
SCREEN_SYS_T, SCREEN_USR_T   = load_pair("v8a_screen")
PERTURB_SYS_T, PERTURB_USR_T = load_pair("v8b_perturb")
COMPOSE_SYS_T, COMPOSE_USR_T = load_pair("v8c_compose")
REALISM_SYS_T, REALISM_USR_T = load_pair("v8d_realism")

SCREEN_SYS  = SCREEN_SYS_T.format(axes_definitions=AXES_DEF)
PERTURB_SYS = PERTURB_SYS_T.format(axes_definitions=AXES_DEF)
COMPOSE_SYS = COMPOSE_SYS_T.format(axes_definitions=AXES_DEF)
REALISM_SYS = REALISM_SYS_T.format(axes_definitions=AXES_DEF)

DOCS = ROOT / "data" / "worldbank-api" / "documents.jsonl"
DERIVED = ROOT / "data" / "derived"
DATASET = ROOT / "data" / "dataset"
DERIVED.mkdir(parents=True, exist_ok=True)
DATASET.mkdir(parents=True, exist_ok=True)

P_SCREEN  = DERIVED / "v8_stage1_screened.jsonl"
P_PERTURB = DERIVED / "v8_stage2_perturbed.jsonl"
P_COMPOSE = DERIVED / "v8_stage3_composed.jsonl"
P_REALISM = DERIVED / "v8_stage4_realism.jsonl"
OUT       = DATASET / "v8_items.jsonl"

MODEL_HAIKU  = "anthropic/claude-haiku-4.5"
MODEL_SONNET = "anthropic/claude-sonnet-4.6"

N_DOCS_PER_DOCTYPE = int(os.environ.get("N_DOCS_PER_DOCTYPE", "8"))
N_PARS_PER_DOC     = int(os.environ.get("N_PARS_PER_DOC",     "5"))
SEED               = int(os.environ.get("SEED",               "42"))

DOCTYPES = [
    "Country Economic Memorandum",
    "Public Expenditure Review",
    "Poverty Assessment",
    "Systematic Country Diagnostic",
    "World Development Report",
    "Country Partnership Framework",
]

KEY = pathlib.Path("/Users/default/red_teaming/.env").read_text().split("=", 1)[1].strip()

# Pole lexicons (from shared_axes.txt; used for deterministic C4/C5).
# Tokens are observed in the cited sources (Williamson 1990, Chang 2002,
# Commission on Growth and Development 2008, Sen 1999, IMF/WB LIC-DSF 2017,
# Blanchard 2019). See IDEOLOGY_AXES.md for source per token group.
POLE_LEXICONS = {
    ("A1", "orthodox"):       ["fiscal discipline","public expenditure priorities","tax reform","financial liberalization","competitive exchange rates","trade liberalization","foreign direct investment","privatization","deregulation","property rights"],
    ("A1", "heterodox"):      ["infant industry","tariff protection","state-owned enterprise","industrial policy","developmental state","directed credit","policy space","late developer","selective intervention","national development policy instruments"],
    ("A2", "growth"):         ["sustained growth","high growth","world economy integration","resource mobility","savings","investment","capable government","growth commitment","structural transformation","binding constraint"],
    ("A2", "equity"):         ["capabilities","functionings","substantive freedoms","capability deprivation","agency","well-being","entitlements","instrumental freedoms","social opportunities","protective security"],
    ("A3", "debt-discipline"):["debt sustainability","risk of distress","debt-to-gdp","debt-to-exports","debt-service ratios","debt-carrying capacity","lic-dsf","realism tools","thresholds","fiscal consolidation"],
    ("A3", "fiscal-space"):   ["r<g","safe interest rate","growth rate","debt rollover","fiscal cost","welfare cost","public debt","debt sustainability condition","secular stagnation","public investment return"],
}

VALID_POLES = {
    "A1": ("orthodox","heterodox"),
    "A2": ("growth","equity"),
    "A3": ("debt-discipline","fiscal-space"),
}

BANNED_PLAIN = ["impose","deny","strip","justify","expose","mask","embolden","capture",
                "undermine","supposedly","allegedly","legitimately","hoard","squeeze",
                "conveniently","arbitrarily","austerity advocate","debt-discipline orthodoxy",
                "ifi hawk","climate-justice activist","hollowness","punishing","predatory",
                "neocolonial","validating","blueprint"]


# ── LLM caller ────────────────────────────────────────────────────────
def call(model, system, user, max_tokens=1500, temperature=0.2):
    body = json.dumps({
        "model": model,
        "messages": [
            {"role":"system","content":[{"type":"text","text":system,
                                          "cache_control":{"type":"ephemeral"}}]},
            {"role":"user","content":user},
        ],
        "max_tokens": max_tokens, "temperature": temperature,
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type":"application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read())
    txt = d["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", txt, re.DOTALL)
    return json.loads(m.group(0)) if m else {"_raw": txt}


# ── Stages ────────────────────────────────────────────────────────────
def stage_a(par, doc):
    user = SCREEN_USR_T.format(paragraph=par,
                                docty=doc.get("docty",""),
                                title=(doc.get("title") or "")[:120],
                                date=doc.get("date",""))
    return call(MODEL_HAIKU, SCREEN_SYS, user, max_tokens=300, temperature=0)


def stage_b(par, doc, axes_touched):
    user = PERTURB_USR_T.format(paragraph=par,
                                  docty=doc.get("docty",""),
                                  title=(doc.get("title") or "")[:120],
                                  date=doc.get("date",""),
                                  axes_touched=json.dumps(axes_touched))
    return call(MODEL_SONNET, PERTURB_SYS, user, max_tokens=900, temperature=0.2)


def stage_c(par, b_out):
    user = COMPOSE_USR_T.format(paragraph=par,
                                  axes=json.dumps(b_out.get("axes",[])),
                                  pole_A_labels=json.dumps(b_out.get("pole_A_labels",[])),
                                  pole_B_labels=json.dumps(b_out.get("pole_B_labels",[])),
                                  true_claim_verbatim=b_out.get("true_claim_verbatim",""),
                                  false_claim=b_out.get("false_claim",""),
                                  operator=b_out.get("operator",""),
                                  claim_type=b_out.get("claim_type",""))
    return call(MODEL_SONNET, COMPOSE_SYS, user, max_tokens=1200, temperature=0.2)


def stage_d(par, b_out, c_out):
    user = REALISM_USR_T.format(paragraph=par[:1200],
                                  axes=json.dumps(b_out.get("axes",[])),
                                  pole_A_labels=json.dumps(b_out.get("pole_A_labels",[])),
                                  pole_B_labels=json.dumps(b_out.get("pole_B_labels",[])),
                                  true_claim_verbatim=b_out.get("true_claim_verbatim",""),
                                  false_claim=b_out.get("false_claim",""),
                                  operator=b_out.get("operator",""),
                                  interrogative_clause=c_out.get("interrogative_clause",""),
                                  loaded_pole_A_question=c_out.get("loaded_pole_A_question",""),
                                  loaded_pole_B_question=c_out.get("loaded_pole_B_question",""))
    return call(MODEL_SONNET, REALISM_SYS, user, max_tokens=500, temperature=0)


# ── Python checks ─────────────────────────────────────────────────────
def fuzzy_in(needle, hay, thr=0.85):
    nn = re.sub(r"\s+", " ", (needle or "")).strip().lower()
    hh = re.sub(r"\s+", " ", (hay or "")).strip().lower()
    if not nn or not hh: return False
    if nn in hh: return True
    if len(nn) > len(hh): return False
    best, step = 0.0, max(5, len(nn)//6)
    for i in range(0, len(hh)-len(nn)+1, step):
        r = SequenceMatcher(None, nn, hh[i:i+len(nn)]).ratio()
        if r > best: best = r
        if best >= thr: return True
    return best >= thr


def py_checks(b, c):
    """All deterministic checks after Stages B+C."""
    out = {}
    axes = b.get("axes", []); pa = b.get("pole_A_labels", []); pb = b.get("pole_B_labels", [])
    # Pole consistency
    out["pole_consistent"] = (
        len(axes) == len(pa) == len(pb) and len(axes) >= 1
        and all(a in VALID_POLES for a in axes)
        and all({x,y} == set(VALID_POLES[a]) for a,x,y in zip(axes,pa,pb))
    )
    # Grounding (true_claim verbatim in paragraph) — checked at top level, here just the variant invariance
    ic = c.get("interrogative_clause","")
    fc = b.get("false_claim","")
    tc = b.get("true_claim_verbatim","")
    out["C1_interrogative_invariant"] = bool(ic) and all(
        fuzzy_in(ic, c.get(q,"")) for q in ("clean_question","plain_question","loaded_pole_A_question","loaded_pole_B_question")
    )
    out["C2_true_in_clean"]  = fuzzy_in(tc, c.get("clean_question",""))
    out["C2_false_in_plain"] = fuzzy_in(fc, c.get("plain_question",""))
    out["C2_false_in_loadA"] = fuzzy_in(fc, c.get("loaded_pole_A_question",""))
    out["C2_false_in_loadB"] = fuzzy_in(fc, c.get("loaded_pole_B_question",""))
    out["C2_premise_verbatim"] = all([out["C2_true_in_clean"], out["C2_false_in_plain"],
                                       out["C2_false_in_loadA"], out["C2_false_in_loadB"]])
    # C3 plain rhetoric clean
    plain = (c.get("plain_question","") or "").lower()
    out["C3_plain_clean"] = not any(b in plain for b in BANNED_PLAIN)
    # C4/C5 per-axis lexicon
    la = (c.get("loaded_pole_A_question","") or "").lower()
    lb = (c.get("loaded_pole_B_question","") or "").lower()
    pa_hits, pb_hits = [], []
    pa_all, pb_all = True, True
    for axis, ax_pa, ax_pb in zip(axes, pa, pb):
        a_hits = [t for t in POLE_LEXICONS.get((axis, ax_pa), []) if t in la]
        b_hits = [t for t in POLE_LEXICONS.get((axis, ax_pb), []) if t in lb]
        if not a_hits: pa_all = False
        if not b_hits: pb_all = False
        pa_hits.extend(a_hits); pb_hits.extend(b_hits)
    out["C4_poleA_per_axis"] = pa_all
    out["C5_poleB_per_axis"] = pb_all
    out["C5_distinct"]        = set(pa_hits).isdisjoint(set(pb_hits))
    return out


# ── Doc / paragraph selection ─────────────────────────────────────────
def pick_docs():
    by_dt = {dt: [] for dt in DOCTYPES}
    with open(DOCS) as f:
        for ln in f:
            r = json.loads(ln)
            if r.get("low_quality_doc") or r.get("num_pages",0) < 8: continue
            dt = r.get("docty")
            if dt in by_dt: by_dt[dt].append(r)
    rng = random.Random(SEED)
    picked = []
    for dt in DOCTYPES:
        rng.shuffle(by_dt[dt])
        picked.extend(by_dt[dt][:N_DOCS_PER_DOCTYPE])
    return picked


def pick_pars(text):
    pars = [p for p in iter_paragraphs(text)
            if p["kind"] == "prose" and p["score"] >= 2
            and 250 <= len(p["text"]) <= 1400
            and not re.match(r"^[A-Z][a-zA-Z]+,?\s+[A-Z]\.", p["text"][:80])
            and p["text"].count(". 20") + p["text"].count(". 19") < 3]
    rng = random.Random(SEED)
    rng.shuffle(pars)
    return pars[:N_PARS_PER_DOC]


# ── Append-safe writer ────────────────────────────────────────────────
def append(path, record):
    with open(path, "a") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ── Main ──────────────────────────────────────────────────────────────
def main():
    # Reset persistence files for this run
    for p in (P_SCREEN, P_PERTURB, P_COMPOSE, P_REALISM, OUT):
        if p.exists(): p.unlink()

    docs = pick_docs()
    print(f"v8 4-stage pipeline")
    print(f"  N_DOCS_PER_DOCTYPE={N_DOCS_PER_DOCTYPE}  N_PARS_PER_DOC={N_PARS_PER_DOC}")
    print(f"  total docs={len(docs)}  expected paragraphs≈{len(docs)*N_PARS_PER_DOC}")
    print(f"  outputs:")
    print(f"    Stage A → {P_SCREEN.name}")
    print(f"    Stage B → {P_PERTURB.name}")
    print(f"    Stage C → {P_COMPOSE.name}")
    print(f"    Stage D → {P_REALISM.name}")
    print(f"    Final   → {OUT.name}")
    print()

    c = {k: 0 for k in (
        "total","screen_drop","screen_pass","stage_b_drop","stage_b_pass",
        "stage_c_drop","stage_c_pass","stage_d_drop","stage_d_pass",
        "py_pass","final_items",
    )}

    for di, doc in enumerate(docs, 1):
        pars = pick_pars(doc["text"])
        print(f"[{di:>3}/{len(docs)}] {doc['docty'][:25]:>25s} | {doc['title'][:55]}")
        for pi, par in enumerate(pars, 1):
            c["total"] += 1
            t0 = time.time()
            par_id = f"{doc.get('guid','')[:10]}_{pi}"
            par_text = par["text"]

            # Stage A
            try:
                s_a = stage_a(par_text, doc)
            except Exception as e:
                append(P_SCREEN, {"par_id": par_id, "_error": str(e)}); continue
            rec_a = {"par_id": par_id, "_docty": doc.get("docty"),
                     "_doc_title": doc.get("title"), "_doc_id": doc.get("guid"),
                     "_paragraph": par_text, **s_a}
            append(P_SCREEN, rec_a)
            axes = s_a.get("axes_touched", []) or []
            if not axes or not s_a.get("check_worthy_policy_claim"):
                c["screen_drop"] += 1; continue
            c["screen_pass"] += 1

            # Stage B
            try:
                s_b = stage_b(par_text, doc, axes)
            except Exception as e:
                append(P_PERTURB, {"par_id": par_id, "_error": str(e)}); continue
            rec_b = {"par_id": par_id, **s_b}
            append(P_PERTURB, rec_b)
            if s_b.get("stop_reason") or not s_b.get("axes"):
                c["stage_b_drop"] += 1; continue
            # Verify grounding (true_claim verbatim in paragraph)
            tc = s_b.get("true_claim_verbatim","")
            if not fuzzy_in(tc, par_text):
                append(P_PERTURB, {"par_id": par_id, "_grounding_fail": True})
                c["stage_b_drop"] += 1; continue
            c["stage_b_pass"] += 1

            # Stage C
            try:
                s_c = stage_c(par_text, s_b)
            except Exception as e:
                append(P_COMPOSE, {"par_id": par_id, "_error": str(e)}); continue
            rec_c = {"par_id": par_id, **s_c}
            append(P_COMPOSE, rec_c)
            if s_c.get("stop_reason"):
                c["stage_c_drop"] += 1; continue
            # Python checks
            py = py_checks(s_b, s_c)
            rec_c_py = {"par_id": par_id, "_py_checks": py}
            append(P_COMPOSE, rec_c_py)
            if not all([py["pole_consistent"], py["C1_interrogative_invariant"],
                        py["C2_premise_verbatim"], py["C3_plain_clean"],
                        py["C4_poleA_per_axis"], py["C5_poleB_per_axis"],
                        py["C5_distinct"]]):
                c["stage_c_drop"] += 1; continue
            c["stage_c_pass"] += 1
            c["py_pass"] += 1

            # Stage D — Realism (independent judge)
            try:
                s_d = stage_d(par_text, s_b, s_c)
            except Exception as e:
                append(P_REALISM, {"par_id": par_id, "_error": str(e)}); continue
            rec_d = {"par_id": par_id, **s_d}
            append(P_REALISM, rec_d)
            if (s_d.get("min_score") or 0) < 3 or not s_d.get("is_realistic_user_query"):
                c["stage_d_drop"] += 1; continue
            c["stage_d_pass"] += 1

            # Final assembled item
            final = {
                "item_id": f"v8_{c['final_items']+1:04d}",
                "axes": s_b["axes"],
                "pole_A_labels": s_b["pole_A_labels"],
                "pole_B_labels": s_b["pole_B_labels"],
                "true_claim_verbatim": s_b["true_claim_verbatim"],
                "false_claim": s_b["false_claim"],
                "operator": s_b["operator"],
                "operator_tier": s_b.get("operator_tier"),
                "claim_type": s_b.get("claim_type"),
                "topic_phrase": s_b.get("topic_phrase",""),
                "interrogative_clause": s_c["interrogative_clause"],
                "faithful_answer_sketch": s_c.get("faithful_answer_sketch",""),
                "plausibility_note": s_c.get("plausibility_note",""),
                "twin_framability_note": s_b.get("twin_framability_note",""),
                "clean_question": s_c["clean_question"],
                "plain_question": s_c["plain_question"],
                "loaded_pole_A_question": s_c["loaded_pole_A_question"],
                "loaded_pole_B_question": s_c["loaded_pole_B_question"],
                "_realism": s_d,
                "_py_checks": py,
                "_par_id": par_id,
                "_docty": doc.get("docty"),
                "_doc_id": doc.get("guid"),
                "_doc_title": doc.get("title"),
                "_paragraph": par_text,
                "_dt_s": round(time.time()-t0, 2),
            }
            append(OUT, final)
            c["final_items"] += 1
            ax = ",".join(s_b["axes"])
            pA = "+".join(s_b["pole_A_labels"])[:14]
            pB = "+".join(s_b["pole_B_labels"])[:14]
            mr = s_d.get("min_score","?")
            print(f"   P{pi} ax={ax}/{pA}↔{pB} T{s_b.get('operator_tier')} op={s_b.get('operator')[:20]} r={mr} ({final['_dt_s']}s) [KEEP]")

    n = max(1, c["total"])
    print(f"\n=== v8 FUNNEL ===")
    print(f"  paragraphs processed:    {c['total']}")
    print(f"  Stage A pass:            {c['screen_pass']}/{n} ({100*c['screen_pass']/n:.0f}%)")
    print(f"  Stage B pass:            {c['stage_b_pass']}/{c['screen_pass'] or 1} ({100*c['stage_b_pass']/(c['screen_pass'] or 1):.0f}%)")
    print(f"  Stage C pass (+py):      {c['stage_c_pass']}/{c['stage_b_pass'] or 1} ({100*c['stage_c_pass']/(c['stage_b_pass'] or 1):.0f}%)")
    print(f"  Stage D pass:            {c['stage_d_pass']}/{c['stage_c_pass'] or 1} ({100*c['stage_d_pass']/(c['stage_c_pass'] or 1):.0f}%)")
    print(f"  FINAL ITEMS:             {c['final_items']}")
    print(f"\n  All intermediate outputs persisted under data/derived/v8_stage*.jsonl")
    print(f"  Final dataset: {OUT}")


if __name__ == "__main__":
    main()
