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

Political framing runs along **6 MARPOR axes**, each with a right/left pole:
A1 economic ideology (free-market / regulation), A2 macro policy (orthodoxy /
Keynesian), A3 social policy (welfare limit / expand), A4 trade (free trade /
protectionism), A5 multilateralism (−/+), A6 labour (−/+).

## Layout

```
pipeline/           generation: one runner per step; utilities are shared
  utils.py               shared utilities (LLM caller, prompts, checks, sampling, IO)
  run_screen.py          screen paragraphs for political axes
  run_claim_filter.py    per-sentence claim classification
  run_perturb_compose.py perturb the fact, then compose the 4 variants
  run_realism_filter.py  realism / pole-alignment filter
  build_dataset.py       assemble the 4-variant benchmark JSONL
  build_annotation.py    human-annotation export
  ingest/                WB PDF → text/paragraph extractor (screen input)
prompts/            step prompts (screen, perturb, compose, realism, claimfilter)
data/               derived funnel artifacts + the 110-item dataset (corpus excluded)
results/            a model-response run + analyze.py (statistical analysis)
```

The raw **World Bank corpus (~5.6 GB)** is not in git (it lives in
`koreankiwi99/wb-corpus-cache`) and is needed only to regenerate from scratch.
To regenerate, place it at **`data/worldbank-api/documents.jsonl`** — that path
(the `DOCS` constant in `pipeline/utils.py`) is what `run_screen.py` reads.
Re-inspecting the shipped `data/` needs no corpus.

## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env          # add OPENROUTER_API_KEY
export PYTHONPATH=.           # scripts import `pipeline.*` and `prompts`
```

Regenerate the dataset (needs the corpus at `data/worldbank-api/documents.jsonl`):

```bash
python pipeline/run_screen.py           # screen paragraphs
python pipeline/run_perturb_compose.py  # perturb + compose the 4 variants
python pipeline/run_realism_filter.py   # realism filter
python pipeline/build_dataset.py        # → data/political-sycophancy-final.jsonl
```

## The production funnel (reproduced by `data/`)

```
1,278  paragraphs screened            → data/derived/screened.jsonl
  718  axes-touched (of those)        → (filtered in-memory by the next step)
  581  perturbed + composed           → data/dataset/items_all.jsonl
  216  trimmed                        → data/dataset/items_trimmed.jsonl
  110  pass realism filter (final)    → data/dataset/items_final.jsonl
  440  prompts (110 × 4 variants)     → data/political-sycophancy-final.jsonl
```

Intermediate outputs, in order: `data/derived/screened → claims →
perturbed → composed → realism_scored`.
