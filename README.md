# Political Sycophancy — Ideologically-Framed False-Premise Correction

Does a model correct a **false premise** embedded in a question — and does the
**political framing** of that premise change whether it corrects? We build
document-grounded false-premise items from World Bank analytical reports, each
in four framings, and measure premise-correction across models.

Each item explodes into four prompts sharing one invariant question:

| variant | premise | framing | measures |
|---|---|---|---|
| `clean`  | true  | neutral | calibration (does the model know the answer?) |
| `plain`  | false | neutral | premise-sycophancy |
| `load_a` | false | pole-A (right-of-center) | political loading |
| `load_b` | false | pole-B (left-of-center) | political loading + pole asymmetry |

See [`docs/PIPELINE.md`](docs/PIPELINE.md) for the full method, axes
([`docs/IDEOLOGY_AXES.md`](docs/IDEOLOGY_AXES.md)), and scope
([`docs/SCOPE.md`](docs/SCOPE.md)).

## Repository layout

```
src/evalsuite/      Runtime (2c slice): corpus extract, run_layer, sycophancy scorer, loaders
pipeline/perturb/   v8 generation pipeline (Stages A–D)
prompts/            Stage prompts (screen, perturb, compose, realism, claimfilter)
scripts/            score_political_sycophancy.py (headline metrics) + fetch_corpus.sh
data/               Derived funnel artifacts + the 110-item benchmark (corpus excluded)
results/            Shipped Layer-4 run (responses, scores, summaries) + analyze.py
docs/               PIPELINE / SCOPE / IDEOLOGY_AXES / DATASET / FINDINGS
paper/              LaTeX source
```

## Provenance — this repo consolidates three sources

| Source | Contributed |
|---|---|
| `koreankiwi99/political-sycophancy` | generation pipeline + one run's outputs |
| `koreankiwi99/political-sycophancy-data` | derived funnel artifacts (`data/derived`, `data/dataset`) |
| `Red_Teaming` evalsuite (uploaded) | the 2c runtime — `src/evalsuite/` + the scorer |

Only the **2c (political-sycophancy) slice** of the evalsuite was vendored; the
jailbreak / scope-QA layers were dropped. The raw **World Bank corpus (~5.6 GB)**
is *not* here — it lives in `koreankiwi99/wb-corpus-cache` and is needed only to
regenerate items from scratch (`scripts/fetch_corpus.sh`).

## Quickstart

```bash
pip install -e .                 # installs evalsuite from src/ + deps
cp .env.example .env             # add OPENROUTER_API_KEY + JUDGE_API_KEY
```

**Score the shipped run** (no corpus needed):
```bash
python scripts/score_political_sycophancy.py         # judges responses → metrics
python results/layer4_political_sycophancy/analyze.py # McNemar / Wilson CIs
```

**Regenerate the dataset** (needs the corpus — run `scripts/fetch_corpus.sh` first):
```bash
python pipeline/perturb/run_stage_a_full_sonnet.py     # Stage A: screen paragraphs
python pipeline/perturb/run_production_bc_parallel.py  # Stage B+C: perturb + compose
python pipeline/perturb/run_stage_d_analysis.py        # Stage D: realism filter
python pipeline/perturb/build_red_teaming_dataset.py   # → data/political-sycophancy-final.jsonl
```

## The production funnel (reproduced by `data/`)

```
1,278  paragraphs screened (Stage A, Sonnet)   → data/derived/stage_a_full_scale_sonnet.jsonl
  718  axes-touched                            → data/derived/stage_a_passed_sonnet.jsonl
  581  Stage B+C generated (Opus)              → data/dataset/v8_prod_bc_opus_items.jsonl
  216  trimmed                                 → data/dataset/v8_items_216_trimmed.jsonl
  110  pass D filters (final)                  → data/dataset/v8_items_clean_110.jsonl
  440  prompts shipped (110 × 4 variants)      → data/political-sycophancy-final.jsonl
```

## Status of results

See [`docs/FINDINGS.md`](docs/FINDINGS.md). The current committed run compares
Apertus vs GPT-5-RAG on the 110 items: GPT-5-RAG corrects premises more often;
no significant pole asymmetry. Calibration pass rates are low (14–22%), so
sycophancy denominators are thin — see the caveat in `docs/FINDINGS.md`.
`docs/FINDINGS.md` also describes an earlier CRS-era RAG-retrieval experiment
that predates this WB-only design; treat it as historical context.
