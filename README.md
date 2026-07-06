# Political Sycophancy — Dataset Generation

Generates document-grounded **false-premise** items from World Bank analytical
reports, each in four political framings, to test whether a model corrects a
false premise — and whether the framing changes that.

Each item produces four prompts that share one invariant question:

| variant | premise | framing | measures |
|---|---|---|---|
| `clean`  | true  | neutral | calibration (does the model know the answer?) |
| `plain`  | false | neutral | premise-sycophancy |
| `load_a` | false | pole-A (right-of-center) | political loading |
| `load_b` | false | pole-B (left-of-center) | political loading + pole asymmetry |

Method: [`docs/PIPELINE.md`](docs/PIPELINE.md) · axes: [`docs/IDEOLOGY_AXES.md`](docs/IDEOLOGY_AXES.md).

## Layout

```
pipeline/           generation: one runner per stage + shared stage library
  stages.py           core: all stage functions (screen/claimfilter/perturb/compose/realism)
  run_stage_a_screen.py            Stage A  — screen paragraphs for political axes
  run_stage_a2_claimfilter.py      Stage A2 — per-sentence claim classification
  run_stage_bc_perturb_compose.py  Stage B+C — perturb the fact, compose 4 variants
  run_stage_d_realism.py           Stage D  — realism / pole-alignment filter
  build_dataset.py                 assemble the 4-variant benchmark JSONL
  build_annotation.py              human-annotation export
  corpus/             WB PDF → text/paragraph extractor (Stage A input)
prompts/            stage prompts (screen, perturb, compose, realism, claimfilter)
data/               derived funnel artifacts + the 110-item dataset (corpus excluded)
docs/               PIPELINE / IDEOLOGY_AXES / DATASET / SCOPE / FINDINGS
results/            a model-response run + analyze.py (statistical analysis)
scripts/            fetch_corpus.sh
paper/              LaTeX source
```

The raw **World Bank corpus (~5.6 GB)** is not in git — it lives in
`koreankiwi99/wb-corpus-cache` and is needed only to regenerate from scratch
(`scripts/fetch_corpus.sh`). Re-inspecting the shipped `data/` needs no corpus.

## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env          # add OPENROUTER_API_KEY
export PYTHONPATH=.           # scripts import `pipeline.*` and `prompts`
```

Regenerate the dataset (needs the corpus — run `scripts/fetch_corpus.sh` first):

```bash
python pipeline/run_stage_a_screen.py            # Stage A:  screen paragraphs
python pipeline/run_stage_bc_perturb_compose.py  # Stage B+C: perturb + compose
python pipeline/run_stage_d_realism.py           # Stage D:  realism filter
python pipeline/build_dataset.py                 # → data/political-sycophancy-final.jsonl
```

## The production funnel (reproduced by `data/`)

```
1,278  paragraphs screened (Stage A, Sonnet)   → data/derived/stage_a_full_scale_sonnet.jsonl
  718  axes-touched                            → data/derived/stage_a_passed_sonnet.jsonl
  581  Stage B+C generated (Opus)              → data/dataset/v8_prod_bc_opus_items.jsonl
  216  trimmed                                 → data/dataset/v8_items_216_trimmed.jsonl
  110  pass D filters (final)                  → data/dataset/v8_items_clean_110.jsonl
  440  prompts (110 × 4 variants)              → data/political-sycophancy-final.jsonl
```
