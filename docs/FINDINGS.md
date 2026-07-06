# Findings (preliminary) — Framing & False-Premise Correction in RAG

**RQ.** When a RAG corpus contradicts a false premise in the query, does the system correct it — and does *ideological framing* of that premise suppress correction?

**Setup.** Document-grounded items from CRS (extract→ground→perturb→load), each in 4 variants: clean / neutral-false / loaded-right / loaded-left (same false fact, framing-only differences; MFT-derived frames, LIAR-anchored direction). Single-hop RAG over a ~30k-sentence / 117-doc CRS index; dense (BGE) + BM25; readers Sonnet-4.6 & Llama-3.3-70B; held-out GPT-5 PCR judge. Fair design: retrieval-side and generation-side measured **separately**. n=23 items (preliminary).

**Key result — the framing effect is retrieval-side and dense-specific, not generation sycophancy:**
- **Generation (fixed/oracle context):** Framing Penalty = **+0.00** for both readers — given the refuting passage, models correct the false premise ~100% regardless of framing. *No generation-side sycophancy.*
- **Retrieval:** ideological loading drops **dense** recall@5 from **0.65 → 0.30 (−0.35)**, while **BM25 is flat (−0.02)**. Loaded rhetoric pulls the embedding away from the terse refutation; lexical retrieval ignores it.
- **End-to-end** correction loss tracks **retrieval, not framing** (PCR 1.0 when gold retrieved vs 0.85 when missed).

**Interpretation.** Any end-to-end "framing penalty" here is a **dense-retrieval artifact**, not the generator swallowing the premise. This *localizes* the failure to retrieval and is a cleaner, more novel headline than "framing suppresses correction."

**Open confounds (must resolve before claiming it):**
1. **Verbosity vs ideology** — loaded queries are longer/denser; left and right drop *equally* (both →0.30), consistent with verbosity hurting dense recall rather than ideology. Need a **verbose-neutral control**.
2. **Scale** — n=23, 2 issues, 2 gold docs; −0.35 is suggestive, not precise.
3. Single-hop only; single judge; generation at ceiling (little headroom).

**Decisive next experiment (cheap — retrieval-only, no reader/judge):** regenerate a larger item set with a 5th **verbose-neutral** variant; run dense + BM25 recall at scale. If verbose-neutral also drops dense recall → effect is verbosity; if only ideological loading drops it → genuine retrieval sycophancy.

**Paper status.** Full draft compiles (intro, related work, method, figure, tables); Results still to be filled with the confirmed numbers; needs trim to 4pp. Pivot the headline toward retrieval-side localization pending the control above.
