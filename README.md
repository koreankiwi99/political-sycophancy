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
pipeline/           generation: one runner per step + shared step library
  steps.py               core: the step functions (screen/classify/perturb/compose/realism)
  run_screen.py          screen paragraphs for political axes
  run_claim_filter.py    per-sentence claim classification
  run_perturb_compose.py perturb the fact, then compose the 4 variants
  run_realism_filter.py  realism / pole-alignment filter
  build_dataset.py       assemble the 4-variant benchmark JSONL
  build_annotation.py    human-annotation export
  corpus/                WB PDF → text/paragraph extractor (screen input)
prompts/            step prompts (screen, perturb, compose, realism, claimfilter)
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
python pipeline/run_screen.py           # screen paragraphs
python pipeline/run_perturb_compose.py  # perturb + compose the 4 variants
python pipeline/run_realism_filter.py   # realism filter
python pipeline/build_dataset.py        # → data/political-sycophancy-final.jsonl
```

## The production funnel (reproduced by `data/`)

```
1,278  paragraphs screened            → data/derived/screened.jsonl
  718  axes-touched                   → data/derived/axes_passed.jsonl
  581  perturbed + composed           → data/dataset/items_all.jsonl
  216  trimmed                        → data/dataset/items_trimmed.jsonl
  110  pass realism filter (final)    → data/dataset/items_final.jsonl
  440  prompts (110 × 4 variants)     → data/political-sycophancy-final.jsonl
```

Intermediate outputs, in order: `data/derived/screened → axes_passed →
claims → perturbed → composed → realism_scored`.
