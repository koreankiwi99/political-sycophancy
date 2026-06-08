# Ideology Axes — MARPOR Political-Bias Framework

Six paired political-bias axes in `prompts/shared_axes.txt`, drawn from the Comparative Manifesto Project (MARPOR / CMP) coding scheme. This document holds the citations and rationale.

---

## Why this framework

Earlier iterations used two unsuitable bases.

Development-economics axes (Williamson vs Chang; Sen vs Spence Commission; LIC-DSF vs Blanchard) were academic-economics policy positions, not labels of political-identity groups used in political-bias research.

Cultural Cognition (Kahan) is a validated motivated-reasoning framework, but its categories (hierarchical/egalitarian, individualist/communitarian) are *cultural-worldview* labels, not *political-bias* labels. Cultural Cognition predicts political bias; it is not itself a taxonomy of paired political-bias positions.

MARPOR is. It is the standard taxonomy in political science for coding political-bias positions in policy text, with five decades of cross-national use and paired left/right category structure.

---

## Source

Pole descriptions in `prompts/shared_axes.txt` are taken from the v5 codebook, paraphrased close to the published wording:

**Werner, Annika; Lacewell, Onawa; Volkens, Andrea; Matthieß, Theres; Zehnter, Lisa; van Rinsum, Leila** (2021). *Manifesto Coding Instructions (5th fully revised edition).* Manifesto Project's Handbook Series. Wissenschaftszentrum Berlin für Sozialforschung (WZB), May 2021.

PDF → [handbook_2021_version_5.pdf](https://manifestoproject.wzb.eu/down/papers/handbook_2021_version_5.pdf)
Codebook landing → [manifesto-project.wzb.eu](https://manifesto-project.wzb.eu/)

The Manifesto Project (MRG / CMP / MARPOR) codes political-bias positions in party-manifesto text along ~56 categories. Many categories are organized in matched pairs (e.g., 401 ↔ 403), reflecting opposing political positions on the same policy domain. The v5 codebook (May 2021) is the current standard edition.

The MARPOR scheme underlies large-scale political-position scaling (Laver-Budge left-right scale; Lowe-Benoit-Mikhaylov-Laver logit scale; Bakker-Hobolt salience-position model) and has been adopted in NLP for fine-grained political-bias annotation (Subramanian et al. 2018, ACL; Glavaš et al. 2019; others).

---

## Selection of axes for this benchmark

Six paired axes were selected from MARPOR on three criteria:

1. **Paired** — both poles have explicit MARPOR codes representing opposing positions, not one-sided categories.
2. **Policy-substance** — the axis concerns substantive policy content of the kind World Bank documents discuss (economic, social, trade, multilateral), not domestic-cultural or domestic-political-procedural content rarely present in WB analytical reports.
3. **Identity-laden** — the pair maps to recognizable political-identity coalitions (left-of-center / right-of-center) that hold the position as part of their political identity, not merely as a technocratic judgment.

The MARPOR pairs that satisfy all three for WB content:

| # | Pole A (v5 cat.) | Pole B (v5 cat.) | Policy domain |
|---|---|---|---|
| A1 | Free Market Economy (401) | Market Regulation (403) | Economic ideology |
| A2 | Economic Orthodoxy (414) | Keynesian Demand Management (409) | Macroeconomic policy |
| A3 | Welfare State Limitation (505) | Welfare State Expansion (504) | Social policy |
| A4 | Protectionism Negative — i.e. Free Trade (407) | Protectionism Positive (406) | Trade policy |
| A5 | Internationalism Negative (109) | Internationalism Positive (107) | Multilateralism |
| A6 | Labour Groups Negative (702) | Labour Groups Positive (701) | Labor relations |

Pole descriptions in `prompts/shared_axes.txt` are paraphrased directly from the v5 codebook category definitions (Werner et al. 2021).

---

## Mapping to corpus

World Bank documents engage these axes regularly.

- **A1 (free-market / market-regulation)** is engaged by paragraphs on privatization, deregulation, state-owned enterprise reform, competition policy, public-private partnerships, antitrust.
- **A2 (economic-orthodoxy / keynesian-demand-management)** is engaged by paragraphs on fiscal consolidation, deficit reduction, counter-cyclical spending, monetary policy stance, debt sustainability.
- **A3 (welfare-limitation / welfare-expansion)** is engaged by paragraphs on social protection, targeting versus universal provision, conditional cash transfers, pension reform, health-system financing.
- **A4 (free-trade / protectionism)** is engaged by paragraphs on tariff policy, trade liberalization, regional trade agreements, infant-industry protection, export promotion.
- **A5 (internationalism-negative / internationalism-positive)** is engaged by paragraphs on conditionality, donor coordination, multilateral institutions, sovereignty in policy reform, global governance. Pole_A (negative) is the sovereigntist position; pole_B (positive) is the pro-multilateral position. Pole alignment chosen so pole_A is right-of-center consistent with the other five axes.
- **A6 (labour-groups-negative / labour-groups-positive)** is engaged by paragraphs on labor-market flexibility, minimum wage, collective bargaining, informal-sector formalization, union rights.

A single paragraph can touch one or two axes. Multi-axis items effectively cue a recognizable political-identity profile (right-of-center economic coalition; left-of-center economic coalition; etc.).

---

## Considered and dropped

**Cultural Cognition (Kahan).** Validated framework but cultural-worldview, not political-bias. Predicts political positions rather than being a taxonomy of them.

**Development-economics axes** (Williamson, Sen, debt-discipline). Academic-economics positions, not political-bias positions held by identity groups.

**Boydstun Media Frames Corpus** (Card et al. 2015). Fifteen generic policy frames (Economic, Capacity, Morality, Fairness, etc.), but frames are not paired political-bias positions.

**Moral Foundations Theory** (Haidt; MFD). Validated political-psychology framework, but its foundations (care, fairness, loyalty, authority, sanctity, liberty) are moral-cognitive categories, not policy-position taxonomy. Could complement MARPOR in future work.

**OpinionsQA / GlobalOpinionQA** (Santurkar 2023; Durmus 2023). LLM-specific opinion datasets, but single-issue items rather than paired worldview labels suited to a pole-A / pole-B benchmark design.

**MARPOR axes not selected.** Traditional Morality (v5 cat. 603 / 604), National Way of Life (601 / 602), Law and Order (605), Multiculturalism (607 / 608), Military (104 / 105). These v5 codes are paired but rarely appear in WB analytical-report content. They can be added if the corpus is expanded beyond core development-policy text.

---

## Limitations

MARPOR coding was developed for party-manifesto text, not technocratic policy reports. World Bank documents are formally non-partisan, written in analytic register, and rarely take an overt political-bias position. The axes here are framings *evoked by* WB content (e.g., a paragraph on tariff reduction engages the free-trade / protectionism axis even when written neutrally), not positions the documents themselves explicitly adopt.

For the benchmark's purpose — generating premise-loaded user queries to test reader-model sycophancy — what matters is whether the loaded variants are *recognizable* as a political-bias posture to a reader, not whether the source paragraph endorses one pole. Stage D realism rating verifies that recognition empirically.
