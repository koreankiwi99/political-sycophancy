# Ideology Axes — three-axis framework

Companion to `SCOPE.md` / `PIPELINE.md`. Defines the three ideological axes used to construct paired loaded variants in the political-sycophancy benchmark. The active prompt is `prompts/shared_axes.txt`; this document holds the literature grounding and design rationale.

## Why three axes (and why we cut from five)

An earlier draft of this framework defined five axes. Auditing it for sourcing fidelity exposed real problems on two:

- **A2 (donor-North / recipient-South).** The "south" pole anchored on dependency theory (Prebisch 1950, Wallerstein 1974) is a real intellectual tradition. The "north" pole had no honest academic anchor — there is no canonical "IFI conditionality is good actually" academic paper. The position lives in WB/IMF operational documents, not in a paired literature. Burnside & Dollar (2000) is about aid effectiveness conditional on policy environment, not about whether conditionality is legitimate. Attributing the "legitimacy" framing to Burnside-Dollar was a stretch.
- **A4 (climate-orthodox / climate-justice).** The Stern Review (2006) and Klein (2014) both exist and articulate real positions. But they are not in dialogue: Stern is mainstream environmental economics; Klein is critical theory / movement journalism. They do not share methodology. Framing them as an "axis" implies a paired debate that is not actually happening at the academic level.

Beyond fidelity, the corpus support for A2 and A4 in v7.1 was thin: 9 items and 2 items respectively out of 62. The axes were already empirically weak.

We retain the three axes where (a) the pole positions are genuinely paired in published debate, (b) the literature anchors hold up to checking, and (c) the WB API corpus contains sufficient substrate.

The dropped axes are not "left for future work" decoratively — they are dropped because the grounding does not support them, and re-introducing them would require finding honest anchors that do not currently exist in our literature.

---

## A1 — Macroeconomic Policy: Market-led vs State-led

The most well-established paired debate in development economics. Both poles have decades of citation history and are taught in textbook development-economics courses as opposing positions.

### Pole "orthodox" — Washington Consensus tradition

**Position.** Markets allocate efficiently when prices are undistorted. The state's role is to set rules and protect property rights, not to direct investment. Growth requires fiscal discipline, deregulation, trade and capital-account openness, and privatization. Government interventions in markets create distortions, generate rent-seeking, and crowd out private activity.

**Anchor.** Williamson, John (1990). *"What Washington Means by Policy Reform."* In *Latin American Adjustment: How Much Has Happened?* (J. Williamson, ed.), Institute for International Economics, Washington DC. This is the paper that coined "Washington Consensus" and listed the ten reforms.

**Lexicon.** fiscal discipline, structural reform, getting prices right, market signals, deregulation, privatization, property rights, crowd out, prudent, openness.

### Pole "heterodox" — Developmental-state critique

**Position.** Markets alone do not produce industrialization. Historically successful late-developers (Britain, USA, Germany, Japan, South Korea) used tariffs, infant-industry protection, state-owned enterprises, and directed credit during their own industrialization. The orthodox prescription now blocks the same tools for current late-developers. The state must lead investment in strategic sectors.

**Anchor.** Chang, Ha-Joon (2002). *Kicking Away the Ladder: Development Strategy in Historical Perspective.* Anthem Press, London.

**Lexicon.** industrial policy, infant industry, state-owned enterprise, capital controls, directed credit, developmental state, policy space, strategic sectors, coordination, late developer.

### Grounding quality

**Strong.** Both poles are textbook canonical, the anchors are direct, the pole positions are recognizably opposed.

### Corpus fit

| Doctype | A1 fit |
|---|---|
| Country Economic Memorandum (CEM) | strong — macroeconomic analysis is core content |
| Public Expenditure Review (PER) | strong — fiscal-policy stance is central |
| Systematic Country Diagnostic (SCD) | moderate — sometimes touches macro positions |
| World Development Report (WDR) | variable by year theme |
| Country Partnership Framework (CPF) | moderate — operational document but reflects WB diagnostic stance |

---

## A3 — Development Objectives: Growth-first vs Equity-first

A paired debate in *policy discourse* about what development should optimize for. The two poles are not opposing positions within a single academic methodology — the growth pole is anchored in positive theory of how economies grow plus a normative claim from policy institutions; the equity pole is anchored in a normative framework about what development means. They are, however, in genuine debate in development-policy circles, and the World Bank itself has published policy reports on both sides.

### Pole "growth" — Sustained growth as foundation

**Position.** Sustained per-capita income growth is the foundational development objective. Welfare improvements — poverty reduction, longevity, schooling — historically follow from growth, so policies should target growth's preconditions: productivity, investment, structural transformation. Inequality may worsen during growth episodes but absolute conditions improve.

**Anchor.** Commission on Growth and Development (2008). *The Growth Report: Strategies for Sustained Growth and Inclusive Development.* World Bank, Washington DC. Chaired by Michael Spence (Nobel laureate). This is the World Bank's institutional articulation of the growth-first position; it explicitly defends sustained 7%+ growth as the largest historical driver of poverty reduction.

**Theoretical foundation.** Endogenous-growth theory (Lucas 1988; Romer 1990) explains *how* growth works; the Spence Commission supplies the normative claim that growth is *therefore* the development priority. The two together constitute the growth-first position.

**Lexicon.** sustained growth, productivity, human capital, accumulation, structural transformation, dynamism, enabling environment, competitiveness, investment, total-factor productivity.

### Pole "equity" — Capability approach

**Position.** Development is the expansion of substantive freedoms — capabilities that people can exercise: political participation, education, health, longevity. GDP growth alone does not capture well-being. Inequality, exclusion, and capability deprivation are development failures regardless of aggregate income. Redistribution and social protection are legitimate ends, not just instruments to growth.

**Anchor.** Sen, Amartya (1999). *Development as Freedom.* Oxford University Press. Sen received the Nobel Prize in 1998 partly for this framework. The capability approach is the canonical statement of the equity-first position.

**Institutional articulation.** World Development Report 2006: *Equity and Development* applied the capability framework to WB policy guidance.

**Lexicon.** capabilities, multidimensional poverty, social protection, inclusive growth, redistribution, gender gap, pro-poor, entitlements, well-being, distribution.

### Grounding quality

**Moderate-to-strong.** The poles are not opposing within a single academic methodology, but they are paired in development-policy debate. The Spence Commission and Sen are both canonical institutional anchors. Reviewer-defensible.

### Corpus fit

| Doctype | A3 fit |
|---|---|
| Poverty Assessment | strong — equity-relevant content directly addressed |
| Systematic Country Diagnostic (SCD) | strong — both growth and equity diagnostics |
| World Development Report (WDR) | variable, often strong (WDR 2006, 2024 specifically thematic) |
| Country Economic Memorandum (CEM) | moderate — primarily growth-side |
| Country Partnership Framework (CPF) | moderate — operational policy mix |

---

## A5 — Fiscal Policy: Debt-discipline vs Fiscal-space

A live current debate in policy economics, with named adherents on both sides and active disputes about what the empirical evidence shows. This is the most contemporary of the three axes.

### Pole "debt-discipline" — Sustainability orthodoxy

**Position.** Public debt has thresholds beyond which it constrains growth and creates macro vulnerability. Sustainability thresholds — debt-to-GDP, debt-service-to-exports, debt-service-to-revenue — define risk of distress. Front-loaded fiscal consolidation restores sustainability when thresholds are breached.

**Anchor.** International Monetary Fund and World Bank (2017). *Review of the Debt Sustainability Framework for Low-Income Countries.* The current LIC-DSF (Low-Income Country Debt Sustainability Framework) was established in 2005 and revised in 2017; it operationalizes debt-discipline orthodoxy through country-by-country risk-of-distress classification.

**Theoretical reference.** Reinhart and Rogoff (2010). *"Growth in a Time of Debt."* AEA Papers and Proceedings 100 (2): 573-578. This is the academic counterpart, though the famous 90% threshold was challenged by Herndon, Ash, and Pollin (2013) on the basis of spreadsheet errors and exclusion choices. The qualitative claim of a debt-growth correlation survives in revised form; we cite the DSF as the more stable anchor.

**Lexicon.** debt sustainability, debt-to-GDP, threshold, risk of distress, fiscal consolidation, primary surplus, fiscal anchor, front-loaded adjustment, LIC-DSF, prudent.

### Pole "fiscal-space" — Political-choice critique

**Position.** When the safe interest rate (r) is below the growth rate (g), public debt can rise without fiscal cost and its welfare cost is much lower than the conventional view holds. Productive public investment can self-finance through tax-base expansion. Austerity in this environment is a political choice, not a sustainability requirement.

**Anchor.** Blanchard, Olivier (2019). *"Public Debt and Low Interest Rates."* American Economic Review 109 (4): 1197-1229. AEA Presidential Address. This is the canonical statement of the fiscal-space position in current macroeconomics.

**Lexicon.** fiscal space, r<g, counter-cyclical, productive borrowing, public-investment multiplier, austerity (political choice), self-financing, expansionary, low-r, policy choice.

### Grounding quality

**Strong.** Both poles have current institutional/academic anchors, the debate is live and ongoing, and both sides are recognized by the other.

### Corpus fit

| Doctype | A5 fit |
|---|---|
| Public Expenditure Review (PER) | strong — fiscal-policy content directly central |
| Joint WB-IMF Debt Sustainability Analysis (not in API corpus; in zip) | maximal — DSAs are the canonical A5 substrate |
| Country Economic Memorandum (CEM) | moderate — sometimes contains fiscal-trajectory analysis |
| World Development Report (WDR) | variable |
| Country Partnership Framework (CPF) | moderate — operational fiscal positions |

---

## Doctype × axis matrix (operational mapping)

|  | A1 Macro | A3 Growth/Equity | A5 Debt |
|---|:-:|:-:|:-:|
| Country Economic Memorandum (CEM) | ●● | ● | ● |
| Public Expenditure Review (PER) | ●● | ● | ●● |
| Systematic Country Diagnostic (SCD) | ● | ●● | ● |
| Country Partnership Framework (CPF) | ● | ● | ● |
| Poverty Assessment | ○ | ●● | ○ |
| World Development Report (WDR) | ● | ●● | ○ |
| Joint WB-IMF DSA *(zip corpus only)* | ●● | ○ | ●● |

`●●` axis instantiates strongly · `●` instantiable · `○` mismatch — skip

A paragraph in a CEM with a fiscal-deficit claim → **A1** (orthodox/heterodox) and **A5** (discipline/fiscal-space) are both available. A paragraph in a Poverty Assessment → **A3** (growth/equity). Stage A picks the axis per paragraph; Stage B writes both poles of that axis.

## Schema implication

Each item record carries the chosen axis as a field. With three axes (A1, A3, A5), the axis-DA test is run within each axis using the same false fact across pole_A and pole_B variants. Cross-axis comparisons are stratified, not paired.

## Power implications

With three axes and ~80-90 items per axis at production scale (50 docs × 6 doctypes within API corpus → ~380 items, distributed across the three axes proportionally to corpus fit), we land at roughly:

- A1: ~150 paired items → 80% power to detect a 0.10-0.12 correction drop at α=.05 (paired McNemar)
- A3: ~150 paired items → similar
- A5: ~80-90 paired items → 80% power at a slightly larger effect size (0.13-0.15)

These are within-axis paired tests. The FP headline metric — averaged across the three axes — is correspondingly powered to detect a 0.08-0.10 drop.

## What was dropped (and why this is honest)

- **A2 (donor-North / recipient-South).** Dependency theory is real; the "donor-North" pole has no canonical academic counterpart. Reframing A2 as "dependency vs IFI-discourse" would re-introduce an unbalanced axis — one pole canonical, one pole constructed.
- **A4 (climate-orthodox / climate-justice).** The two positions are real but they do not engage each other at the academic level. The "axis" is a movement-vs-mainstream-economics framing, not a paired methodological debate.

Both are interesting open questions for future work with different methods (e.g., a corpus-induction approach that derives frames empirically from text rather than imposing a priori dichotomies).

## What this changes vs the earlier 5-axis framework

1. **Axes dropped from 5 to 3.** A1, A3, A5 retained; A2 and A4 dropped for grounding and corpus reasons documented above.
2. **Anchors tightened.** A3 growth re-anchored on Commission on Growth and Development 2008 (institutional) rather than Lucas 1988 (positive theory of growth without normative claim). A5 debt-discipline re-anchored on IMF/WB DSF 2017 (institutional) rather than Reinhart-Rogoff 2010 (academically discredited threshold).
3. **The `prompts/shared_axes.txt` is the active operational file.** This document holds the rationale and the literature grounding; the active prompt is operationally minimal.
4. **Items already generated under A2/A4** in v7 / v7.1 are retained on disk for reference but excluded from the analysis pipeline.
