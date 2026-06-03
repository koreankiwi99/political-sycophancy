# Ideology Axes for the World-Bank-Primary Track

Companion to `SCOPE.md` / `PIPELINE.md`. Defines the **multi-axis** ideological framework that replaces the single "market/orthodox vs state/heterodox" axis in earlier drafts (PIPELINE.md §3a, footnote in §3c about *climate-finance paragraphs reading as a mismatch* for the fiscal-policy lexicon).

## Why multiple axes

The WB corpus is **heterogeneous** — board minutes, country chair summaries, Joint WB-IMF DSAs, Country Economic Memoranda, Poverty Assessments, climate-finance docs. A single fiscal-policy lexicon (Washington-Consensus vs developmental-state) lights up cleanly on CEM/PER/SCD but **misfires** on climate-finance and gender/inclusion docs. Inspection of the 1,628-PDF zip confirms this: ~40% of titles are board governance / chair summaries / replenishment / debt-sustainability / climate-finance / gender-and-inclusion content where the fiscal axis doesn't naturally apply.

A small set of axes — each with its own literature anchor and lexicon — lets the LOAD step pick a topic-appropriate frame **per paragraph**, the same way PERTURB now picks the operator per paragraph. This is the WB-specific generalization of PIPELINE.md §3c-bis ("topic-conditional lexicon").

## The five axes

Each axis is **paired** (a left/right or pole-A/pole-B contrast on the *same* false fact), each pole has a literature-anchored lexicon, and each axis comes with **misperception anchors** (the WB-track substitute for LIAR; not all are quantitative — some are framing tropes documented in the secondary literature).

### Axis 1 — Orthodox macro vs Heterodox macro [PRIMARY]

| Pole | Frame | Lexicon (excerpt) | Literature anchor |
|---|---|---|---|
| **Orthodox** (market, fiscal-discipline) | *Washington Consensus*; *macro-stability-first* | `fiscal discipline`, `crowd out`, `market signals`, `private-sector-led`, `structural reform`, `getting prices right`, `tightening`, `rules-based`, `prudent` | Williamson 1990; Krueger 1990; IMF Art. IV orthodoxy |
| **Heterodox** (developmental-state, industrial policy) | *Developmental state*; *industrial-policy-first* | `state-led`, `industrial policy`, `public investment`, `capital controls`, `strategic sectors`, `developmental finance`, `policy space`, `decommodify` | Stiglitz 2002 *Globalization & Its Discontents*; Chang 2002 *Kicking Away the Ladder*; Mazzucato 2013 *Entrepreneurial State*; Rodrik 2007 |
| **Content fit** | CEM, PER, SCD, DSA, Development Policy Financing (DPF) | | |
| **Misperception anchor** | "austerity restored growth in X" / "industrial policy is always wasteful" — both empirically contested in the post-2008 Eurozone & East-Asia literatures | | |

### Axis 2 — Donor-North / IFI-discipline vs Recipient-South / Sovereignty (Dependency)

| Pole | Frame | Lexicon (excerpt) | Literature anchor |
|---|---|---|---|
| **Donor-North** (conditionality-as-discipline) | *Conditionality-legitimates*; *technical-assistance* | `conditionality`, `safeguards`, `governance reform`, `country systems`, `partner country ownership` (technocratic), `policy dialogue`, `results framework`, `disbursement triggers` | World Bank legitimacy literature; Krueger; IDA replenishment discourse |
| **Recipient-South** (sovereignty / dependency) | *Neocolonial-conditionality*; *dependency* | `imposed`, `extractive`, `policy capture`, `IFI overreach`, `loss of policy autonomy`, `dollar dominance`, `Bretton Woods cartel`, `donor capture` | Prebisch 1950; Wallerstein 1974; Easterly 2006 *White Man's Burden*; Hickel 2017 *The Divide* |
| **Content fit** | IDA replenishment, board statements, DSA, governance docs, debt-restructuring docs | | |
| **Misperception anchor** | "IDA conditionality drove the X recovery" / "WB loans always reduce sovereignty" — both directional framings of contested causal claims | | |

### Axis 3 — Growth-first vs Equity-first

| Pole | Frame | Lexicon (excerpt) | Literature anchor |
|---|---|---|---|
| **Growth-first** | *Growth-as-engine*; *trickle-down* | `growth-led poverty reduction`, `dynamism`, `productivity`, `competitiveness`, `pro-business`, `enabling environment`, `human-capital accumulation` (instrumental) | Lucas 1988; Easterly; Solow growth-accounting tradition |
| **Equity-first** | *Inclusive-growth*; *distribution-matters* | `inclusive`, `redistribution`, `social protection`, `gender gap`, `pro-poor`, `multidimensional poverty`, `human-development first`, `inequality of opportunity` | Sen 1999 *Development as Freedom*; Piketty 2014; Stiglitz 2012; Deaton |
| **Content fit** | Poverty Assessments, IDA Special Theme (gender, inclusion), SCD, WDR, social-protection docs | | |
| **Misperception anchor** | "redistribution kills growth" / "growth alone has not reduced poverty" — Pinker/Rosling vs Hickel/Sumner debate | | |

### Axis 4 — Climate-orthodox vs Climate-justice

| Pole | Frame | Lexicon (excerpt) | Literature anchor |
|---|---|---|---|
| **Climate-orthodox** | *Green-growth*; *market-mechanism* | `green growth`, `carbon pricing`, `blended finance`, `mobilizing private capital`, `climate-smart`, `nature-based solutions`, `co-benefits`, `transition finance`, `risk-adjusted` | Stern Review 2006 (market-form); World Bank *Achieving Climate & Development Goals*; IFC climate-finance literature |
| **Climate-justice** | *Historical-responsibility*; *loss-and-damage* | `historical emissions`, `climate reparations`, `loss and damage`, `polluter pays`, `extractive transition`, `green colonialism`, `just transition`, `decommodify carbon` | Klein 2014 *This Changes Everything*; Hickel 2020 *Less Is More*; Táíwò 2022 *Reconsidering Reparations*; Aboriginal/Indigenous climate literature |
| **Content fit** | Country Climate and Development Reports, CRW climate, IFC climate-finance docs, IDA climate special theme | | |
| **Misperception anchor** | "carbon pricing is regressive" / "climate adaptation is a Global-South problem" — directional framings of empirically mixed claims | | |

### Axis 5 — Debt-discipline vs Fiscal-space (heterodox macro)

| Pole | Frame | Lexicon (excerpt) | Literature anchor |
|---|---|---|---|
| **Debt-discipline** | *Sustainability-first*; *DSF-orthodoxy* | `debt sustainability`, `fiscal consolidation`, `breach of threshold`, `debt-to-GDP`, `prudent`, `front-loaded adjustment`, `LIC-DSF`, `risk of distress` | IMF/WB Debt Sustainability Framework; Reinhart-Rogoff 2010 (and the contested 90% threshold) |
| **Fiscal-space** | *Counter-cyclical*; *political-choice* | `fiscal space`, `growth-friendly consolidation`, `counter-cyclical`, `r-g`, `productive borrowing`, `austerity is political`, `developmental finance`, `public-investment multiplier` | Blanchard 2019 (low-r world); Mazzucato; Wren-Lewis; post-Keynesian fiscal-space literature |
| **Content fit** | DSAs (Joint WB-IMF), DPF, debt-restructuring docs, IDA-IBRD financing docs | | |
| **Misperception anchor** | "country X has unsustainable debt at Y% of GDP" — direction-flippable on the *same* numeric fact (Reinhart-Rogoff debate gives a documented misperception lineage) | | |

## Doctype × axis matrix (which axis is naturally instantiable where)

|  | A1 Macro | A2 N/S | A3 Growth/Equity | A4 Climate | A5 Debt |
|---|:-:|:-:|:-:|:-:|:-:|
| Country Economic Memorandum (CEM) | ●● | ● | ● | ○ | ● |
| Public Expenditure Review (PER) | ●● | ○ | ● | ○ | ●● |
| Systematic Country Diagnostic (SCD) | ● | ○ | ●● | ● | ● |
| Country Partnership Framework (CPF) | ● | ●● | ● | ● | ● |
| Poverty Assessment | ○ | ○ | ●● | ○ | ○ |
| Joint WB-IMF DSA | ●● | ●● | ○ | ○ | ●● |
| World Development Report (WDR) | ● | ○ | ●● | ●● | ○ |
| Country Climate & Development Report | ○ | ● | ● | ●● | ● |
| IDA replenishment / Board statements | ○ | ●● | ● | ● | ● |
| Climate-finance docs (CRW, climate-blended) | ○ | ● | ○ | ●● | ○ |
| Gender / Inclusion IDA Special Themes | ○ | ○ | ●● | ○ | ○ |
| Board Standing Committee / Audit / minutes | ○ | ● | ○ | ○ | ○ |
| Country chair summaries | ○ | ● | ● | ○ | ● |

`●●` axis instantiates strongly · `●` instantiable · `○` mismatch — skip

A paragraph in a CEM with a fiscal-deficit claim → **A1** (orthodox/heterodox) and **A5** (discipline/fiscal-space) are both available. A paragraph in a Country Climate & Development Report with a financing-gap claim → **A4** (orthodox/justice). The LLM picks the axis per paragraph at LOAD time, the same way it picks the perturbation operator at PERTURB time (PIPELINE.md §3c).

## Schema additions

Each loaded variant in the item record (PIPELINE.md §3e) carries the axis it was generated under:

```json
"opinion_clauses": {
  "plain":            "...",
  "loaded_A_orthodox":   "...",   // Axis 1, pole orthodox
  "loaded_A_heterodox":  "...",   // Axis 1, pole heterodox
  "loaded_C_growth":     "...",   // Axis 3, pole growth
  "loaded_C_equity":     "..."    // Axis 3, pole equity
},
"directions": {
  "axis": "A1_macro" | "A2_north_south" | "A3_growth_equity" | "A4_climate" | "A5_debt",
  "pole_pos": "orthodox|heterodox|north|south|growth|equity|orthodox|justice|discipline|space",
  "pole_neg": "...",
  "frame": "Washington-Consensus|developmental-state|...",
  "lexicon_id": "A1_orthodox_v1"
}
```

Within-fact pairing (the DA design from SCOPE.md §1, H4) is now **per-axis**: build both poles of the same axis from the same `neutral_false`. Within-axis comparisons stay paired (McNemar). Cross-axis comparisons are stratified, not paired.

## What this changes vs PIPELINE.md §3a / §3c

1. **Two parallel tracks → one primary track, five axes.** The US-partisan CRS+GAO track is demoted to a replication study (or dropped — see SCOPE.md update). WB becomes the main dataset.
2. **The "topic-conditional lexicon" note in §3c-bis is now spec.** Each axis ships its own frame/lexicon and is selected per paragraph at LOAD time.
3. **LIAR misperception anchor is replaced** with axis-specific misperception anchors drawn from the framing-literature column above. These are *framing tropes documented in secondary literature*, not survey-measured public misperceptions. This is a weaker form of anchoring than LIAR — we'll need to flag this honestly in the Limitations.
4. **DA (H4) becomes "axis-DA":** correction asymmetry between the two poles of an axis on the same fact. We report axis-DA per axis, not a single L/R DA.
5. **Power calculation unchanged:** FP is still the headline (paired McNemar on neutral_false vs loaded), now averaged across axes. ~250–300 paired items per axis-arm; with 5 axes and within-fact pairing, ~600 base facts gives ~250 paired items per axis after coverage thinning.

## Operational plan (axis instantiation order)

1. **Pilot one axis end-to-end first.** Recommend **A1 (orthodox/heterodox)** on CEM+PER+SCD — strongest literature anchor, cleanest content fit, mirrors the existing fiscal-policy lexicon so we re-use prior tooling.
2. **Validate gate (PIPELINE.md §3f): minpair ≥ 85%, direction ≥ 90% on A1 before adding the next axis.** Don't fan out until one axis hits validation.
3. **Add A3 (growth/equity)** on Poverty Assessment + WDR + SCD — second-strongest fit, distinct lexicon, important for non-fiscal content.
4. **Add A5 (debt-discipline/fiscal-space)** on DSAs — uses the same fact, easy direction-flip (Reinhart-Rogoff lineage).
5. **A4 (climate-orthodox/justice)** on Country Climate & Development Reports — important for paper novelty (climate framing in RAG is unexplored) but riskier validation.
6. **A2 (donor-North/recipient-South)** last — most ideologically charged, most likely to trip judge bias; only run if A1/A3/A5 establish detectable FP first.

## Open questions for the paper headline

- **One axis as headline or all five reported?** If A1 shows a clean FP signal but A2 doesn't, lead with A1 + report A2 in the appendix as a boundary result.
- **Cross-axis FP comparison.** Is the framing penalty *bigger* for some axes than others (e.g., does climate-justice loading suppress correction more than orthodox-macro loading)? This is a second-order finding but novel.
- **Direction-validation κ per axis.** Each axis needs its own annotator κ. Budget for this in human-annotation pass.

---

*Pending edits:* `SCOPE.md` §2a-c (sources → WB-primary), `PIPELINE.md` §3a (tracks → 1 WB track + 5 axes), `DATASET.md` (item schema → axis fields). Will land in a follow-up commit after this framework is reviewed.
