# RAG systems · models · baselines · ablations (build scheme)

## Index / embedding corpus — INTEGRATED (with per-source ablation)
**Decision: one integrated index for the main eval**, not a per-corpus index.
Rationale: realistic RAG never tells the system which corpus holds the answer; the
refuting passage must win retrieval against distractors from all corpora. A per-corpus
index would make correction artificially easy and is *less* faithful to deployment.
- **Main index:** Wikipedia (FEVER, ~5.4M passages, 218 shards) ∪ CRS ∪ GAO ∪ World Bank.
- **Retriever:** BM25 (sparse) ∪ BGE dense — hybrid. deps present: faiss, sentence-transformers 5.4.1, torch 2.9.
- **Per-item gold evidence** retained (from Step-2 grounding: `doc_id`,`sent_idx`) → measures
  retrieval recall (did the refuting passage get retrieved?) = the retrieval-side metric.
- **Per-source index = an ablation** (does isolating the corpus change correction?). Corpus
  composition (gold:distractor:misinfo ratio) is also an ablation.
- **Compute note:** embedding 5.4M passages on CPU is slow → use FlashRAG's *prebuilt* Wikipedia
  index, or build a scoped index (gold pages + sampled distractors) for the first runs.

## Three RAG architectures (FlashRAG pipelines)
1. **single-hop** — `SequentialPipeline`: retrieve top-k → generate.
2. **multi-hop** — **IRCoT**: interleave CoT step ↔ retrieve, 3 hops.
3. **agentic** — ReAct / ReaRAG loop with a search tool (`reasoning_pipeline`); preview: 1 model × ~50 items.

## Models under test (generators via OpenRouter)
- `gpt-5`, `anthropic/claude-sonnet-4.6`, `meta-llama/llama-3.3-70b-instruct` (closed/closed/open).
- **Compatibility:** all three are chat models → fine for single/multi-hop. Agentic needs
  tool-use/ReAct parsing — all three support function-calling or text-ReAct. Generator backend =
  a thin OpenRouter client swapped into FlashRAG's `generator`. **Judge = gpt-5, held out from generation (claude).**

## Baselines (ladder; full set on single-hop, headline models on multi-hop)
| Baseline | role |
|---|---|
| No-RAG (closed-book) | parametric floor |
| Standard RAG (hybrid top-k) | naive anchor |
| CRAG / Astute RAG (FlashRAG impl) | strong adaptive rivals |
| Oracle gold-passage | correction ceiling |

## Ablations (each maps to a hypothesis)
- retrieval on/off · corpus composition / noise ratio (gold:distractor:misinfo) ·
  prompt (default vs "verify the premise") · retriever (BM25/dense/hybrid) · top-k · per-source index.

## Metrics
- **PCR** (adapt `red_teaming/evalsuite/scorers/eloq_defuse.py` → premise-correction judge),
  **RSR** (gold-evidence retrieval recall + premise-affirming passage rate), **FP**, **DA** (paired), **HAF**.

## Reuse map (don't rebuild)
- `red_teaming/evalsuite`: corpus loaders, ELOQ generators, llm_judge, **eloq_defuse→PCR**, runners.
- FlashRAG (`external/FlashRAG`): retriever + the 3 pipelines + CRAG/Self-RAG impls.

## Status
- ✅ deps: torch 2.9, faiss, sentence-transformers 5.4.1. ❌ `flashrag` pkg not pip-installed yet.
- ⏳ NEXT (heavy, needs go-ahead): pip install FlashRAG; get prebuilt wiki index OR build scoped index;
  wire OpenRouter generator; run single-hop slice end-to-end (generate→retrieve→PCR).
