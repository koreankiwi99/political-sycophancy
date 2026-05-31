#!/usr/bin/env python3
"""KG-based fact extraction + structured perturbation prototype (Wikidata).

Approach A: pull a true (subject, relation, object) triple, then pick a
plausible-but-false object from the SAME class (KG-FPQ / Syn-QA2 style).
This guarantees the perturbed premise is actually false, with no LLM in the
factual loop. Verbalization / political reframing is a separate step.
"""
import json, sys, time, urllib.parse
import requests

API = "https://www.wikidata.org/w/api.php"
SPARQL = "https://query.wikidata.org/sparql"
HEAD = {"User-Agent": "polisyc-prototype/0.1 (research; contact salgu@snu.ac.kr)"}

def get(params):
    params["format"] = "json"
    r = requests.get(API, params=params, headers=HEAD, timeout=20)
    r.raise_for_status()
    return r.json()

def sparql(q):
    r = requests.get(SPARQL, params={"query": q, "format": "json"},
                     headers=HEAD, timeout=30)
    r.raise_for_status()
    return r.json()["results"]["bindings"]

def search_qid(label):
    d = get({"action": "wbsearchentities", "search": label,
             "language": "en", "limit": 1})
    hits = d.get("search", [])
    return hits[0]["id"] if hits else None

def label_of(qid):
    d = get({"action": "wbgetentities", "ids": qid,
             "props": "labels", "languages": "en"})
    e = d["entities"][qid]
    return e.get("labels", {}).get("en", {}).get("value", qid)

def get_object(qid, pid):
    """Return (obj_qid, obj_label) for the first value of property pid on qid."""
    d = get({"action": "wbgetclaims", "entity": qid, "property": pid})
    claims = d.get("claims", {}).get(pid, [])
    if not claims:
        return None, None
    val = claims[0]["mainsnak"].get("datavalue", {}).get("value")
    if isinstance(val, dict) and "id" in val:        # entity-valued
        return val["id"], label_of(val["id"])
    return None, val                                  # literal (number/date)

def false_candidates_same_class(obj_qid, k=5):
    """Other entities sharing obj's 'instance of' (P31) class and country (P17)."""
    q = f"""
    SELECT DISTINCT ?x ?xLabel WHERE {{
      wd:{obj_qid} wdt:P31 ?cls .
      OPTIONAL {{ wd:{obj_qid} wdt:P17 ?country . }}
      ?x wdt:P31 ?cls .
      OPTIONAL {{ ?x wdt:P17 ?xc . }}
      FILTER(?x != wd:{obj_qid})
      FILTER(!BOUND(?country) || ?xc = ?country)
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }} LIMIT {k}
    """
    try:
        rows = sparql(q)
    except Exception as e:
        return [f"<sparql failed: {e}>"]
    return [r["xLabel"]["value"] for r in rows if "xLabel" in r]

# Seeds chosen for political/economic valence. (subject, property, gloss)
SEEDS = [
    ("Barack Obama",     "P102", "member of political party"),
    ("Donald Trump",     "P102", "member of political party"),
    ("Margaret Thatcher","P102", "member of political party"),
    ("Affordable Care Act", "P50", "author"),       # may be empty -> shows failure mode
    ("Ronald Reagan",    "P102", "member of political party"),
]

def main():
    out = []
    for subj, pid, gloss in SEEDS:
        rec = {"subject": subj, "property": pid, "relation": gloss}
        sq = search_qid(subj)
        rec["subject_qid"] = sq
        if not sq:
            rec["status"] = "subject_not_found"; out.append(rec); continue
        oq, olabel = get_object(sq, pid)
        rec["object_true"] = olabel
        rec["object_true_qid"] = oq
        if oq:
            rec["object_false_candidates"] = false_candidates_same_class(oq)
            rec["status"] = "ok"
        elif olabel is not None:
            rec["status"] = "literal_value (numeric/date — perturb arithmetically)"
        else:
            rec["status"] = "no_value_for_property"
        out.append(rec)
        time.sleep(0.3)
    print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
