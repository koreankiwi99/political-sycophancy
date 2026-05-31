#!/usr/bin/env python3
"""Probe: does the query lexically echo its refutation? Compare BM25 rank of the
gold sentence for (a) our extract-from-sentence query vs (b) a natural-misconception
paraphrase that does NOT share the evidence's tokens. Shows why retrieval is trivial.
"""
import csv, re, pathlib, requests
from rank_bm25 import BM25Okapi

ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE = "https://www.everycrsreport.com/"
GOLD = "IF13233"
GOLD_MARK = "consolidated with hospital systems"

def fetch(html_path):
    h = requests.get(BASE + html_path, timeout=30).text
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S | re.I)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).strip()

def sents(t):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z(])", t) if len(s.strip()) >= 25]

# build a small index: gold doc + ~10 contested distractors
docs = []
with open(ROOT / "data/crs/reports.csv") as f:
    rows = list(csv.DictReader(f))
gold_row = next(r for r in rows if r["number"] == GOLD)
picks = [gold_row] + [r for r in rows if r.get("latestHTML") and r["number"] != GOLD][:12]
corpus = []
for r in picks:
    try:
        for s in sents(fetch(r["latestHTML"])):
            corpus.append((r["number"], s))
    except Exception as e:
        print("skip", r["number"], e)
print(f"corpus: {len(corpus)} sentences from {len(picks)} docs")
bm25 = BM25Okapi([c[1].lower().split() for c in corpus])

def gold_rank(query):
    scores = bm25.get_scores(query.lower().split())
    order = sorted(range(len(corpus)), key=lambda i: -scores[i])
    for rank, i in enumerate(order, 1):
        if GOLD_MARK in corpus[i][1]:
            return rank, corpus[i][1][:90]
    return None, None

q_echo = ("Given that at least 75% of physicians were consolidated with hospital systems in 2024 "
          "according to the Government Accountability Office, what implications does this have?")
q_para = ("Given that the vast majority of doctors now work for big hospital chains instead of running "
          "their own practices, what does this corporate takeover mean for small-town medicine?")

for label, q in [("ECHO (our current query)", q_echo), ("PARAPHRASE (natural misconception)", q_para)]:
    rank, sent = gold_rank(q)
    print(f"\n[{label}]\n  query: {q[:95]}...\n  gold-sentence BM25 rank: {rank}  (top-5? {'YES' if rank and rank<=5 else 'NO'})")
