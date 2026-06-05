#!/usr/bin/env python3
"""Build a human-annotation CSV from the v7 dataset jsonl.

One row per item. Includes the four variant questions, the claim,
plausibility note, faithful answer sketch, and EMPTY columns for
annotator scores (realism / minpair / pole_A_reads / pole_B_reads /
answerable / notes). Open in Excel, Numbers, or Google Sheets.

Run:
  python pipeline/perturb/build_annotation_file.py
  → data/annotation/v7_items_for_annotation.csv
  → data/annotation/v7_items_for_annotation.md   (preview markdown)
"""
import csv, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
IN  = ROOT / "data" / "dataset" / "v7_items.jsonl"
OUT_DIR = ROOT / "data" / "annotation"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = OUT_DIR / "v7_items_for_annotation.csv"
OUT_MD  = OUT_DIR / "v7_items_for_annotation.md"

# Columns for the human annotator
CONTENT_COLS = [
    "item_id", "axis", "pole_A", "pole_B", "docty", "doc_title",
    "operator_tier", "operators",
    "true_claim_verbatim", "false_claim",
    "interrogative_clause",
    "plausibility_note", "faithful_answer_sketch", "twin_framability_note",
    "clean_question", "plain_question",
    "loaded_pole_A_question", "loaded_pole_B_question",
    "topic_phrase",
    "paragraph",
    # auto-check flags (already computed by pipeline)
    "py_C1_invariant", "py_C2_premise_verbatim",
    "llm_C3_plain_clean", "llm_C4_poleA_loaded", "llm_C5_poleB_distinct",
    "fully_clean_auto",
]

ANNOTATOR_COLS = [
    "annot_realism_1to5",          # is the false claim a misbelief a real reader could hold? 1=trivial/no one would believe, 5=well-anchored documented misperception
    "annot_minpair_yes_no",        # false claim differs ONLY at the perturbation site (no other drift)?
    "annot_pole_A_reads_yes_no",   # does loaded_A actually read as pole-A worldview to you?
    "annot_pole_B_reads_yes_no",   # does loaded_B actually read as pole-B worldview to you?
    "annot_answerable_yes_no",     # is the interrogative answerable from the paragraph after correcting the premise?
    "annot_overall_keep_drop",     # keep / drop / borderline
    "annot_notes",
]


def main():
    rows = [json.loads(l) for l in open(IN)]
    print(f"Loading {len(rows)} items from {IN}")

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(CONTENT_COLS + ANNOTATOR_COLS)
        for i, r in enumerate(rows, 1):
            ver = r.get("_verify_llm", {}) or {}
            pyc = r.get("_verify_py", {}) or {}
            row = [
                f"v7_{i:03d}",
                r.get("axis", ""),
                r.get("pole_A_label", ""),
                r.get("pole_B_label", ""),
                r.get("_docty", ""),
                (r.get("_doc_title", "") or "")[:120],
                r.get("operator_tier", ""),
                ", ".join(r.get("operators", [])),
                r.get("true_claim_verbatim", ""),
                r.get("false_claim", ""),
                r.get("interrogative_clause", ""),
                r.get("plausibility_note", ""),
                r.get("faithful_answer_sketch", ""),
                r.get("twin_framability_note", ""),
                r.get("clean_question", ""),
                r.get("plain_question", ""),
                r.get("loaded_pole_A_question", ""),
                r.get("loaded_pole_B_question", ""),
                r.get("topic_phrase", ""),
                (r.get("_paragraph", "") or "").replace("\n", " "),
                pyc.get("py_C1", ""),
                pyc.get("py_C2", ""),
                ver.get("C3_plain_clean", ""),
                ver.get("C4_poleA_loaded", ""),
                ver.get("C5_poleB_loaded_and_distinct", ""),
                r.get("_fully_clean", ""),
            ] + [""] * len(ANNOTATOR_COLS)
            w.writerow(row)
    print(f"Wrote CSV → {OUT_CSV}  ({len(rows)} rows · {len(CONTENT_COLS) + len(ANNOTATOR_COLS)} cols)")

    # Markdown preview: first 10 items, content fields only
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("# v7 dataset — annotation preview (first 10 items)\n\n")
        f.write(f"Full set: {len(rows)} items in `{OUT_CSV.name}`. Open in Excel / Numbers / Sheets.\n\n")
        f.write("## Annotator instructions\n\n")
        f.write("For each item rate (last 7 columns of CSV):\n\n")
        f.write("- **annot_realism_1to5** — Is the false claim a misbelief a real reader could plausibly hold?\n"
                "  - 1 = trivial/technical edit nobody would notice\n  - 3 = plausible reader confusion\n"
                "  - 5 = well-anchored documented public misperception\n")
        f.write("- **annot_minpair_yes_no** — Does the false claim differ from the true claim ONLY at the perturbation site?\n")
        f.write("- **annot_pole_A_reads_yes_no** — Does loaded_pole_A actually read as the pole-A worldview?\n")
        f.write("- **annot_pole_B_reads_yes_no** — Does loaded_pole_B actually read as the pole-B worldview AND differ from pole-A?\n")
        f.write("- **annot_answerable_yes_no** — Is the interrogative answerable from the paragraph after premise correction?\n")
        f.write("- **annot_overall_keep_drop** — keep / drop / borderline\n")
        f.write("- **annot_notes** — free text\n\n")
        f.write("---\n\n")
        for i, r in enumerate(rows[:10], 1):
            f.write(f"## #{i}  `{r.get('axis')}` — {r.get('pole_A_label')} ↔ {r.get('pole_B_label')}  "
                    f"(tier {r.get('operator_tier')}, ops: {', '.join(r.get('operators',[]))})\n\n")
            f.write(f"**Doc:** *{r.get('_doc_title','')[:100]}* ({r.get('_docty','')})\n\n")
            f.write(f"**Truth:** {r.get('true_claim_verbatim','')}\n\n")
            f.write(f"**False:** {r.get('false_claim','')}\n\n")
            f.write(f"**Plausibility:** {r.get('plausibility_note','')}\n\n")
            f.write(f"**Shared Q:** *{r.get('interrogative_clause','')}*\n\n")
            f.write("| Variant | Question |\n|---|---|\n")
            for label, k in [("CLEAN","clean_question"),("PLAIN","plain_question"),
                             ("LOAD_A","loaded_pole_A_question"),("LOAD_B","loaded_pole_B_question")]:
                q = (r.get(k,"") or "").replace("|", "\\|")
                f.write(f"| **{label}** | {q} |\n")
            f.write("\n**Faithful sketch:** " + r.get("faithful_answer_sketch","") + "\n\n")
            f.write("---\n\n")
    print(f"Wrote markdown preview → {OUT_MD}")


if __name__ == "__main__":
    main()
