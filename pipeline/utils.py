#!/usr/bin/env python3
"""Shared utilities for the generation pipeline.

Provides the pieces reused across the run_*.py step scripts: the LLM caller,
the prompt templates, deterministic (Python) checks, corpus sampling, a JSONL
appender, and config/constants. The step logic itself lives in each run_*.py.
"""
import json, os, pathlib, random, re, sys
from difflib import SequenceMatcher
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from prompts import load_pair, load_shared  # noqa

# ── Prompt templates ──────────────────────────────────────────────────
AXES_DEF = load_shared("shared_axes")
SCREEN_SYS_T,   SCREEN_USR_T    = load_pair("screen")
CLAIMFL_SYS_T,  CLAIMFL_USR_T   = load_pair("claimfilter")
PERTURB_SYS_T,  PERTURB_USR_T   = load_pair("perturb")
COMPOSE_SYS_T,  COMPOSE_USR_T   = load_pair("compose")
REAL_AXIS_SYS_T,   REAL_AXIS_USR_T    = load_pair("realism_axis")
REAL_NEUT_SYS_T,   REAL_NEUT_USR_T    = load_pair("realism_neutral")

SCREEN_SYS       = SCREEN_SYS_T.format(axes_definitions=AXES_DEF)
CLAIMFL_SYS      = CLAIMFL_SYS_T
PERTURB_SYS      = PERTURB_SYS_T.format(axes_definitions=AXES_DEF)
COMPOSE_SYS      = COMPOSE_SYS_T.format(axes_definitions=AXES_DEF)
REAL_AXIS_SYS    = REAL_AXIS_SYS_T.format(axes_definitions=AXES_DEF)
REAL_NEUT_SYS    = REAL_NEUT_SYS_T

# ── Paths ─────────────────────────────────────────────────────────────
DOCS = ROOT / "data" / "worldbank-api" / "documents.jsonl"
DERIVED = ROOT / "data" / "derived"
DATASET = ROOT / "data" / "dataset"
DERIVED.mkdir(parents=True, exist_ok=True)
DATASET.mkdir(parents=True, exist_ok=True)

# ── Corpus sampling config ────────────────────────────────────────────
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

# ── Credentials ───────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv  # noqa
    load_dotenv(ROOT / ".env")
except ImportError:
    pass
KEY = os.environ.get("OPENROUTER_API_KEY", "")  # checked in call(), not at import

# ── Political-axis taxonomy (MARPOR) ──────────────────────────────────
# Lexicons are intentionally NOT defined — the realism step's independent
# rating verifies pole-rhetoric semantically rather than via author-curated
# lexicon presence.
VALID_POLES = {
    "A1": ("free_market", "market_regulation"),
    "A2": ("economic_orthodoxy", "keynesian_demand_management"),
    "A3": ("welfare_state_limitation", "welfare_state_expansion"),
    "A4": ("free_trade", "protectionism"),
    "A5": ("internationalism_negative", "internationalism_positive"),
    "A6": ("labour_groups_negative", "labour_groups_positive"),
}

# Kept for back-compat with the Python-check structure; empty so checks no-op.
POLE_LEXICONS = {(a, p): [] for a, poles in VALID_POLES.items() for p in poles}

BANNED_PLAIN = ["impose","deny","strip","justify","expose","mask","embolden","capture",
                "undermine","supposedly","allegedly","legitimately","hoard","squeeze",
                "conveniently","arbitrarily","austerity advocate","debt-discipline orthodoxy",
                "ifi hawk","climate-justice activist","hollowness","punishing","predatory",
                "neocolonial","validating","blueprint"]


# ── LLM caller ────────────────────────────────────────────────────────
def call(model, system, user, max_tokens=1500, temperature=0.2):
    if not KEY:
        raise SystemExit("OPENROUTER_API_KEY not set (put it in .env or the environment).")
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
    """All deterministic checks after the perturb + compose steps."""
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
        lex_a = POLE_LEXICONS.get((axis, ax_pa), [])
        lex_b = POLE_LEXICONS.get((axis, ax_pb), [])
        a_hits = [t for t in lex_a if t in la]
        b_hits = [t for t in lex_b if t in lb]
        if lex_a and not a_hits: pa_all = False
        if lex_b and not b_hits: pb_all = False
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
    from pipeline.preprocess import iter_paragraphs  # lazy: avoids import cycle
    pars = [p for p in iter_paragraphs(text)
            if p["kind"] == "prose" and p["score"] >= 2
            and 250 <= len(p["text"]) <= 1400
            and not re.match(r"^[A-Z][a-zA-Z]+,?\s+[A-Z]\.", p["text"][:80])
            and p["text"].count(". 20") + p["text"].count(". 19") < 3]
    rng = random.Random(SEED)
    rng.shuffle(pars)
    return pars[:N_PARS_PER_DOC]


# ── JSONL IO ──────────────────────────────────────────────────────────
def read_jsonl(path):
    p = pathlib.Path(path)
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def append_jsonl(record, path):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def save_jsonl(rows, path):
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
