#!/usr/bin/env python3
"""Download World Bank documents via the public WDS (Documents & Reports) API
and emit the two JSONL files the generation pipeline consumes:

  data/worldbank/documents.jsonl :  {"doc_id","title","text","docty","docdt"}
  data/worldbank/pages.jsonl     :  {"doc_id","page","text","is_low_quality"}

`perturb.py` reads documents.jsonl for the econ-title filter (doc_id, title) and
pages.jsonl for page-level candidate paragraphs (doc_id, page, text,
is_low_quality). `extract_pipeline.py`'s worldbank loader reads doc_id/title/text
from documents.jsonl. This script populates all of those fields.

NETWORK: requires the environment's network policy to allow
  search.worldbank.org      (WDS API: search + metadata)
  documents1.worldbank.org  (full-text .txt CDN; some docs use thedocs.worldbank.org)
If those are not allow-listed the requests fail with 403 "Host not in allowlist".

Usage:
  python pipeline/extract/fetch_worldbank.py --n 40 --qterm "economic development"
"""
import argparse, json, pathlib, re, time
import requests

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "worldbank"
WDS = "https://search.worldbank.org/api/v3/wds"

# topic gate (mirrors perturb.py's WANT/SKIP intent) — keep analytical econ reports
WANT = ("country", "econom", "poverty", "debt", "fiscal", "growth", "trade",
        "development", "gdp", "inequality", "expenditure", "tax", "climate")
SKIP = ("annual meetings", "summary proceedings", "compensation", "awards alloc",
        "boards of governors", "budget", "staff", "replenishment", "retrospective",
        "ida resources", "crisis response window")
# analytical document types (avoid admin/board/legal); WDS `docty` values
WANT_DOCTY = ("Report", "Working Paper", "Economic", "Poverty", "Country Economic",
              "Public Expenditure Review", "Policy Research Working Paper",
              "Country Assistance", "Development Policy Review")


def wds_search(qterm, rows, offset):
    params = {
        "format": "json", "rows": rows, "os": offset,
        "fl": "docdt,display_title,docty,majdocty,lang,txturl,pdfurl,count",
        "lang_exact": "English",
        "qterm": qterm,
    }
    r = requests.get(WDS, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    docs = data.get("documents", {}) or {}
    # the API tucks a "facets" key inside documents on some versions — drop non-dict entries
    return data.get("total", 0), {k: v for k, v in docs.items() if isinstance(v, dict) and k != "facets"}


def want_doc(meta):
    title = (meta.get("display_title") or "").lower()
    if not title:
        return False
    if any(s in title for s in SKIP):
        return False
    if not any(w in title for w in WANT):
        return False
    docty = (meta.get("docty") or "")
    if WANT_DOCTY and not any(d.lower() in docty.lower() for d in WANT_DOCTY):
        # title already passed the econ gate; allow if docty empty, else require analytical type
        if docty:
            return False
    return bool(meta.get("txturl"))


def fetch_text(txturl):
    r = requests.get(txturl, timeout=90, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.text


def split_pages(text):
    """WB .txt usually carries form-feed (\\x0c) page breaks; fall back to ~1500-char
    paragraph chunks when absent."""
    text = text.replace("\r\n", "\n")
    if "\x0c" in text:
        return [p.strip() for p in text.split("\x0c")]
    # fallback: group paragraphs into ~1500-char pseudo-pages
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    pages, cur, n = [], [], 0
    for p in paras:
        cur.append(p); n += len(p)
        if n >= 1500:
            pages.append("\n\n".join(cur)); cur, n = [], 0
    if cur:
        pages.append("\n\n".join(cur))
    return pages


def is_low_quality(text):
    t = text.strip()
    if len(t) < 200:
        return True
    letters = sum(c.isalpha() for c in t)
    if letters / max(len(t), 1) < 0.55:        # tables / OCR noise / number dumps
        return True
    words = t.split()
    if words and (sum(1 for w in words if len(w) == 1) / len(words)) > 0.25:
        return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40, help="number of documents to keep")
    ap.add_argument("--qterm", default="economic development poverty fiscal growth")
    ap.add_argument("--rows", type=int, default=50, help="WDS rows per API page")
    ap.add_argument("--max-pages", type=int, default=2000, help="safety cap")
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    args = ap.parse_args()

    out_dir = pathlib.Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    docs_path = out_dir / "documents.jsonl"
    pages_path = out_dir / "pages.jsonl"

    kept = total_pages = 0
    offset = 0
    seen = set()
    with open(docs_path, "w") as fd, open(pages_path, "w") as fp:
        while kept < args.n:
            try:
                total, docs = wds_search(args.qterm, args.rows, offset)
            except Exception as e:
                print(f"WDS search ERR at offset {offset}: {e}")
                break
            if not docs:
                print("no more documents from WDS"); break
            for key, meta in docs.items():
                if kept >= args.n:
                    break
                doc_id = str(meta.get("id") or key)
                if doc_id in seen or not want_doc(meta):
                    continue
                seen.add(doc_id)
                try:
                    txt = fetch_text(meta["txturl"])
                except Exception as e:
                    print(f"  txt fetch ERR {doc_id}: {e}"); continue
                title = meta.get("display_title", "")
                fd.write(json.dumps({"doc_id": doc_id, "title": title, "text": txt,
                                     "docty": meta.get("docty"), "docdt": meta.get("docdt")},
                                    ensure_ascii=False) + "\n")
                for i, page_text in enumerate(split_pages(txt)):
                    if not page_text:
                        continue
                    fp.write(json.dumps({"doc_id": doc_id, "page": i,
                                         "text": page_text,
                                         "is_low_quality": is_low_quality(page_text)},
                                        ensure_ascii=False) + "\n")
                    total_pages += 1
                    if total_pages >= args.max_pages:
                        break
                kept += 1
                print(f"  [{kept}/{args.n}] {doc_id}  {title[:60]}")
                time.sleep(0.3)
            offset += args.rows
            if offset >= total:
                break
    print(f"\nwrote {kept} docs -> {docs_path}")
    print(f"wrote {total_pages} pages -> {pages_path}")


if __name__ == "__main__":
    main()
