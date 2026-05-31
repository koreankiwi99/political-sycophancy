# Project Scope & Plan — Ideologically-Framed False-Premise Correction in RAG

Single source of truth (supersedes the May-21 plan in `~/.claude/plans/i-was-trying-to-whimsical-squirrel.md`, which is stale: it predates the document-grounded pipeline, the ideological-framing axis, the PCR/FP/DA metrics, and the FEVER→FactCC→FalseSum anchor).

- **Venue:** EMNLP / AACL 2026 via an ARR cycle. Short paper (4 pp + unlimited refs + mandatory Limitations).

---

## 1. Research question

**Primary RQ:** When a query embeds a false premise that the retrieval corpus *contradicts*, does a RAG system retrieve the refuting evidence and **correct** the premise — and does **ideological framing** of that premise suppress correction?

**Hypotheses (deliverables):**
- **H1 — Framing penalty (FP>0) [PRIMARY]:** holding the factual error fixed, *ideologically-loaded* wording lowers correction vs *neutral* wording of the **same** false premise. Needs only a loaded-vs-neutral contrast — **no left/right label.**
- **H2 — Retrieval localizes failure:** premise-confirming retrieval (RSR) precedes/explains generation-side non-correction.
- **H3 — Hop amplification (HAF):** multi-hop iteration amplifies FP; agentic may recover.
- **H4 — Directional asymmetry (DA):** does correction differ by the *constructed* ideological direction? The L/R valence is **manufactured by the perturbation/framing on a neutral source fact** (not inherited from the source); where feasible we build **both** a left- and a right-loaded version of the *same* fact → a within-fact (paired) DA test. Each constructed direction is **validated** (reads as intended side, κ) and **anchored to a documented misperception** (LIAR/CARDS) — designed-and-validated, not assigned-and-assumed.

**Positioning (one line):** *FEVER-style document-grounded false-premise generation, in matched neutral/ideological framings, with premise-correction measured across single-hop / multi-hop / agentic RAG — a triple intersection (query-side falsehood × ideological framing × architecture sweep) no prior method occupies.*

**The construct, stated precisely:** facts are not left/right biased — facts are true, and the source documents are **nonpartisan** (CRS/Wikipedia/WB carry no valence). The left/right valence is **manufactured by our perturbation/framing on a neutral source fact** — it is *constructed*, not *inherited from the source*. Because it is manufactured, it must be **validated**, not assumed: human annotation that each constructed item reads as the intended side (report κ), plus **anchoring to a documented real-world misperception** (LIAR speaker-party / CARDS) so the direction is ecologically real. Whether congenial falsehoods are symmetrically *constructible/available* across sides is itself an empirical outcome (cf. directionally-motivated reasoning: Flynn/Nyhan/Reifler 2017, Kahan, Taber & Lodge 2006).

---

## 2. Dataset

### 2a. Sources — three distinct roles (do not conflate)

| Role | Datasets | Used for |
|---|---|---|
| **Retrieval corpus** (indexed; refutation lives here) | **CRS, GAO** (+ OWID/WB); Wikipedia/FEVER = optional distractors | what the RAG system retrieves over |
| **Extraction source** (raw docs; extract→perturb runs here) | **CRS, GAO** (+ OWID/WB complementary) | generating the political items — the core dataset |
| **Claim/direction layer** (not retrieval) | **LIAR, MultiFC, CARDS** | anchor congeniality direction + L/R balance + sanity eval |

### 2b. Generation pipeline (single, document-grounded)

From a raw **CRS/GAO** document (Branch B / FEVER-as-items is **dropped** — see note):
  1. **Extract** atomic claims (`claude-sonnet-4.6`) and **ground** each to a source sentence (FEVER-style evidence pointer) → `pipeline/extract/extract_pipeline.py`.
  2. **Classify** by type {statistic, dated_event, attribution, comparison, causal, projection, recommendation, opinion} + `factual_usable`; keep verifiable, grounded facts.
  3. **Perturb** kept fact → `neutral-false` (type-keyed minimal op: magnitude/direction/temporal/entity/causal/comparative); `clean` = true fact, matched stem → `pipeline/perturb/perturb_load.py`.
  4. **Load** → `loaded-false` (left and/or right), the slant **manufactured** by us (the neutral source fact carries none) via Card/Gross frame + Entman functions + lexicon (`pipeline/framing/`); validated (κ) + misperception-anchored (LIAR/CARDS). Within-fact paired (both directions) where the fact admits it.

> **Branch B dropped (RQ-driven):** the research question — *public RAG deployment supplies current/contested info → political false premises* — is document-grounded and political. FEVER/Climate-FEVER are no longer dataset items; FEVER's Wikipedia is retained only as an **optional retrieval-distractor pool**.

### 2c. Validation & human-annotation criteria (each protects a metric)

- **Factuality** — keep verifiable past/present facts only (ClaimBuster check-worthiness); drop forecasts/opinions. *Protects: the premise is genuinely false.*
- **Refutation-retrievable** — NLI/FEVER check that the corpus REFUTES the false premise & SUPPORTS the clean one. *Protects: non-correction = sycophancy, not missing evidence (fair test).*
- **Minimal-pair** — `neutral-false` ≡ `ideological-false` in factual content. *Protects: FP attributable to framing.*
- **Framing-direction** — slant is the intended L/R and congenial direction is misperception-anchored. *Protects: DA is signal.*
- **Human annotation** — 150–200 items, 2 annotators, report **Cohen's κ** on all four. *Protects: LLM-generated-benchmark credibility.*

### 2d. Scale and why

~300 base facts × variants ≈ **900–1,200 queries**, filtered from ~1–2k candidates. **Direction IS a designed axis, constructed by perturbation:** where a fact admits it, build both a left- and a right-loaded `loaded-false` from the same `neutral-false` (within-fact paired). Each constructed direction is human-validated + misperception-anchored; whether both sides are equally *constructible* is itself a finding. Minimum-viable: 150 facts.

**Why ~300 (power):** **FP** (neutral-false vs loaded-false, same item, paired **McNemar**) is the primary — ~250–300 paired items give 80% power at α=.05 for a ~0.10–0.15 correction drop. **DA** is also **paired** where both directions come from one fact (left-loaded vs right-loaded of the *same* fact) → much stronger than an unpaired ~150/side design; its validity rests on the direction-validation κ, not sample size alone.

---

## 3. RAG system plan — strip FlashRAG

**Base repo:** `RUC-NLPIR/FlashRAG` (WWW 2025) — modular retriever/generator/pipeline; ships Self-RAG, FLARE, **IRCoT**; 38 preprocessed datasets. Reuse its structure; swap generator backend to **OpenRouter**.
- **Retriever:** BM25 ∪ BGE-dense hybrid (built-in); index over our corpora; validate gold-evidence recall on the FEVER subset.
- **single-hop:** retrieve top-k → answer.
- **multi-hop:** IRCoT, 3 hops, query reformulated each hop.
- **agentic preview:** ReAct + search tool, 1 model × ~50 items (custom, small).
- **Models under test:** `gpt-5` + `claude-sonnet-4.6` + `llama-3.3-70b` (closed/closed/open). Generator (`claude`) and judge (`gpt-5`) **held out from each other** to avoid self-preference. Keys: `~/red_teaming/.env` (OpenRouter).

---

## 4. Baselines / ablations / metrics

**Baselines (ladder):** No-RAG (closed-book) → standard RAG → **CRAG / Astute RAG** (strong adaptive rivals) → **oracle gold-passage** (ceiling). Full ladder on single-hop; headline models on multi-hop.

**Ablations (each maps to a claim):** retrieval on/off · corpus noise ratio (gold:distractor:misinfo) · prompt (default vs "verify the premise") · retriever swap (BM25/dense/hybrid).

**Metrics:** **PCR** (headline correction rate; RGB negative-rejection + (QA)²) · **RSR** (retrieval-side; FVA-RAG analogue) · **Δ-correction** (clean−neutral-false; Sharma-2023 answer-sycophancy) · **FP** (neutral-false−ideological-false) · **DA** (left−right) · **HAF** (multi/single). Retrieval-side and generation-side reported separately to localize failure.

---

## 5. Related works — by research-question similarity

(All notes in `related_papers/`.)
- **Framing sycophancy:** Sharma 2023, Perez 2022, ELEPHANT, SycEval, Törnberg 2026, **FVA-RAG** (closest concurrent — cite & differentiate).
- **RAG robustness / false-info:** RGB, CRAG, Self-RAG, Astute, RAGuard, PoisonedRAG, ClashEval, FaithEval, RAMDocs, RAGTruth.
- **False-premise / presupposition QA:** CREPE, (QA)², FalseQA, KG-FPQ, MultiHoax, Syn-QA², FreshQA, ELOQ.
- **Political bias / opinion:** OpinionQA, GlobalOpinionQA, BBQ, PoliTune, GermanPartiesQA, Can-LLMs-Ground.
- **Framing / loaded language:** Entman 1993, Media Frames Corpus (Card 2015), FrameAxis, Social Bias Frames, CARDS (Coan 2021).
- **Construction lineage (method anchor):** FEVER → FactCC → FalseSum.
- **Theory:** Kahan (identity-protective cognition), Taber & Lodge 2006, Flynn/Nyhan/Reifler 2017.

---

## 6. Execution order with go/no-go gates

1. **Acquire** Wikipedia/FEVER dump (1.71 GB) + CRS/GAO political subset. **Gate:** retrieve a FEVER gold sentence end-to-end.
2. **Generate** Branch A on ~30 facts. **Gate:** human κ ≥ 0.6 on minimal-pair + direction before scaling.
3. **Scale** to ~300 facts; full validation pass.
4. **FlashRAG** single+multi-hop stood up. **Gate:** oracle-RAG PCR ≫ No-RAG (sanity).
5. **Run grid** (3 models × 2 arch) + baselines/ablations on subsets.
6. **Analyze** FP / DA / HAF with CIs. **Gate:** effects survive.
7. **Write** (4 pp + Limitations).

---

## 7. Risks / Limitations (disclose in paper)

1. **LLM-generated benchmark** → mitigated by document-grounding, FEVER lineage, human κ, prompt release.
2. **Single-source-of-truth** for non-FEVER facts → corroborate against WDI/IMF/UN; never treat institutional policy stance as fact.
3. **US-centric L/R axis**; cross-side **symmetry is empirical, not assumed**.
4. **Contamination**: FEVER is old/trained-on (use for machinery only); CRS/GAO recent → fairer genuine-correction test.
5. **Compute**: ~15–25k LLM calls; ~$300–600 eval + ~$100–150 generation.
6. **Short-paper scope**: agentic is a preview; World Bank international track is future work.
