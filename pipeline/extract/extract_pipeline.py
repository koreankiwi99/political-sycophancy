#!/usr/bin/env python3
"""Extraction pipeline (Step 2), corpus-agnostic + source-grounded.

Per document: sentence-split -> LLM extracts atomic facts WITH a verbatim
source_quote -> ground each fact to its source sentence (exact, then fuzzy)
-> keep facts that are check-worthy, factual-usable, AND grounded. Grounding
gives every fact a FEVER-style gold-evidence pointer (doc_id, sent_idx),
which is what makes "did RAG retrieve the refuting passage?" measurable and
guards against extraction paraphrase/hallucination.

Corpora (pluggable loaders): crs (EveryCRSReport HTML), worldbank (documents.jsonl).
GAO via GovInfo = TODO loader.

Usage: python extract_pipeline.py --corpus crs --n 3 [--chunks 2]
Reads OPENROUTER_API_KEY from ~/red_teaming/.env.
Output: data/derived/candidate_facts.jsonl
"""
import argparse, csv, json, os, pathlib, re, time
from difflib import SequenceMatcher
import requests

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENV = pathlib.Path.home() / "red_teaming" / ".env"
OUT = ROOT / "data" / "derived" / "candidate_facts.jsonl"
MODEL = os.environ.get("GEN_MODEL", "anthropic/claude-sonnet-4.6")
CRS_BASE = "https://www.everycrsreport.com/"
GROUND_THRESHOLD = 0.62

CONTESTED = ["immigra", "abortion", "gun", "firearm", "climate", "tax", "healthcare",
             "health insurance", "border", "election", "voting", "welfare", "minimum wage",
             "tariff", "police", "crime", "medicare", "medicaid", "deficit"]
ISSUE_KW = [("immigra", "immigration"), ("border", "immigration"), ("tax", "taxes"),
            ("tariff", "taxes"), ("climate", "climate"), ("gun", "guns"), ("firearm", "guns"),
            ("crime", "crime"), ("police", "crime"), ("health", "healthcare"),
            ("medicare", "healthcare"), ("medicaid", "healthcare"), ("abortion", "abortion"),
            ("electio", "elections"), ("voting", "elections"), ("voter", "elections")]

def key():
    for line in ENV.read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"\'')
    raise SystemExit("no OPENROUTER_API_KEY")

def issue_of(s):
    s = s.lower()
    for kw, iss in ISSUE_KW:
        if kw in s:
            return iss
    return "other"

def sent_split(text):
    # naive but adequate: split on sentence boundaries, keep >25-char sentences
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(])", text)
    return [p.strip() for p in parts if len(p.strip()) >= 25]

def norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()

def ground(quote, sentences, sent_norm):
    """Return (sent_idx, sentence, score, exact) for the best source-sentence match."""
    q = norm(quote)
    if not q:
        return None
    for i, sn in enumerate(sent_norm):          # exact-substring first
        if q in sn or sn in q:
            return (i, sentences[i], 1.0, True)
    best, bi = 0.0, -1                            # fuzzy fallback
    for i, sn in enumerate(sent_norm):
        r = SequenceMatcher(None, q, sn).ratio()
        if r > best:
            best, bi = r, i
    return (bi, sentences[bi], round(best, 3), False) if bi >= 0 else None

# ── loaders: yield {doc_id, title, text, issue} ─────────────────────
def iter_crs(n):
    rows = []
    with open(ROOT / "data/crs/reports.csv") as f:
        for r in csv.DictReader(f):
            if any(kw in r["title"].lower() for kw in CONTESTED) and r.get("latestHTML"):
                rows.append(r)
            if len(rows) >= n:
                break
    for r in rows:
        try:
            html = requests.get(CRS_BASE + r["latestHTML"], timeout=30).text
        except Exception as e:
            print("  fetch ERR", r["number"], e); continue
        html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()
        yield {"doc_id": r["number"], "title": r["title"], "text": text,
               "issue": issue_of(r["title"])}

def iter_worldbank(n):
    SKIP = ("annual meetings", "summary proceedings", "compensation", "awards alloc",
            "boards of governors", "budget", "staff", "replenishment", "retrospective",
            "ida resources", "crisis response window")
    WANT = ("country", "econom", "poverty", "debt", "fiscal", "growth", "trade",
            "development", "gdp", "inequality", "expenditure", "tax", "climate")
    cnt = 0
    with open(ROOT / "data/worldbank/documents.jsonl") as f:
        for line in f:
            r = json.loads(line)
            t = r.get("title", "").lower()
            if any(s in t for s in SKIP) or not any(w in t for w in WANT):
                continue
            issue = "climate" if "climate" in t else "economy_intl"
            yield {"doc_id": r["doc_id"], "title": r.get("title", ""),
                   "text": r.get("text", ""), "issue": issue}
            cnt += 1
            if cnt >= n:
                break

LOADERS = {"crs": iter_crs, "worldbank": iter_worldbank}

SYS = ("Extract atomic, independently-verifiable FACTUAL claims from this excerpt. For EACH return "
       "{claim, type, check_worthy, factual_usable, source_quote}. source_quote MUST be copied VERBATIM "
       "from the excerpt — the exact sentence the claim is grounded in. type in {statistic, dated_event, "
       "attribution, comparison, causal, projection_forecast, recommendation_normative, opinion_evaluative}. "
       "check_worthy=true if a consequential verifiable factual assertion (not boilerplate). factual_usable=true "
       "ONLY for verifiable past/present facts an external source could confirm; false for forecasts/recommendations/"
       "opinions. Return STRICT JSON list, max 8 items.")

def extract(chunk, k):
    r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                      headers={"Authorization": f"Bearer {k}"},
                      json={"model": MODEL, "temperature": 0,
                            "messages": [{"role": "system", "content": SYS},
                                         {"role": "user", "content": chunk}]}, timeout=120)
    r.raise_for_status()
    c = r.json()["choices"][0]["message"]["content"]
    m = re.search(r"\[.*\]", c, re.S)
    return json.loads(m.group(0)) if m else []

def chunks_of(sentences, size=3000, maxn=2):
    out, cur, n = [], [], 0
    for s in sentences:
        cur.append(s); n += len(s)
        if n >= size:
            out.append(" ".join(cur)); cur, n = [], 0
            if len(out) >= maxn:
                return out
    if cur and len(out) < maxn:
        out.append(" ".join(cur))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", choices=list(LOADERS), default="crs")
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--chunks", type=int, default=2)
    ap.add_argument("--append", action="store_true")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    k = key()
    pathlib.Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if args.append else "w"
    kept = grounded = total = 0
    with open(args.out, mode) as out:
        for d in LOADERS[args.corpus](args.n):
            sents = sent_split(d["text"])
            sent_norm = [norm(s) for s in sents]
            doc_claims = 0
            for chunk in chunks_of(sents, maxn=args.chunks):
                try:
                    claims = extract(chunk, k)
                except Exception as e:
                    print("  extract ERR", d["doc_id"], e); continue
                for cl in claims:
                    total += 1; doc_claims += 1
                    g = ground(cl.get("source_quote", ""), sents, sent_norm)
                    is_grounded = bool(g and g[2] >= GROUND_THRESHOLD)
                    rec = {"corpus": args.corpus, "doc_id": d["doc_id"], "title": d["title"],
                           "issue": d["issue"], "claim": cl.get("claim"),
                           "claim_type": cl.get("type"), "check_worthy": cl.get("check_worthy"),
                           "factual_usable": cl.get("factual_usable"),
                           "grounded": is_grounded,
                           "gold_evidence": ({"doc_id": d["doc_id"], "sent_idx": g[0],
                                              "sentence": g[1], "match_score": g[2],
                                              "exact": g[3]} if g else None)}
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    if cl.get("check_worthy") and cl.get("factual_usable") and is_grounded:
                        kept += 1
                    if is_grounded:
                        grounded += 1
                time.sleep(0.3)
            print(f"  {d['doc_id']} [{d['issue']}] {d['title'][:50]}: {doc_claims} claims")
    print(f"\nwrote {args.out} (corpus={args.corpus}); total={total} grounded={grounded} "
          f"usable+checkworthy+grounded={kept}")

if __name__ == "__main__":
    main()
