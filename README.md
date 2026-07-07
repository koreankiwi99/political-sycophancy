# Political Sycophancy: Dataset Generation

Document-grounded **false-premise** items from World Bank analytical reports,
each in four political framings, to test whether a model corrects a false
premise, and whether the framing changes that.

Each item is four prompts sharing one invariant question:

| variant | premise | framing |
|---|---|---|
| `clean`  | true  | neutral (calibration) |
| `plain`  | false | neutral (premise-sycophancy) |
| `load_a` | false | pole-A (right-of-center) |
| `load_b` | false | pole-B (left-of-center) |

Framing uses six paired left/right [MARPOR](https://manifesto-project.wzb.eu/)
axes (economic ideology, macro policy, social policy, trade, multilateralism,
labour); definitions in `prompts/shared_axes.txt`.

## Layout

```
pipeline/   generation: one runner per step, plus shared utils.py and preprocess.py
prompts/    the step prompts
data/       derived artifacts + the 110-item dataset (raw corpus excluded)
eval/       scoring (LLM judge) + stats (code only)
```

The raw World Bank corpus (~5.6 GB) is not in git;
to regenerate, place it at `data/worldbank-api/documents.jsonl` (the `DOCS` path
in `pipeline/utils.py`).

## Quickstart

```bash
pip install -r requirements.txt
cp .env.example .env      # add OPENROUTER_API_KEY
export PYTHONPATH=.
```

Regenerate the dataset (needs the corpus):

```bash
python pipeline/run_screen.py           # screen paragraphs for political axes
python pipeline/run_perturb_compose.py  # perturb the claim + compose 4 variants
python pipeline/run_realism_filter.py   # realism / pole-alignment filter
python pipeline/build_dataset.py        # → data/political-sycophancy-final.jsonl
```

## Evaluation (code only; outputs stay local)

```bash
python eval/score.py --run <run>   # GPT-4o judge → corrects_premise, answer_correct
python eval/analyze.py ...         # paired McNemar: PCR, PLE, pole asymmetry
```
