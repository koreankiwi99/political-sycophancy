# Ideology Axes — sources

Three axes in `prompts/shared_axes.txt`. Each axis is anchored to a published source listed below. Positions paraphrase the source's argument. Lexicons are *author-curated* — informed by the source's vocabulary and policy discourse, but **not lifted from any peer-reviewed NLP lexicon**. See "Lexicon provenance" at the bottom.

---

## A1 — Macroeconomic Policy: Market-led vs State-led

**pole_A — orthodox**
Williamson, John (1990). *What Washington Means by Policy Reform.* In *Latin American Adjustment: How Much Has Happened?*, J. Williamson, ed. Institute for International Economics, Washington, DC.
→ [PIIE: full text](https://www.piie.com/commentary/speeches-papers/what-washington-means-policy-reform)

**pole_B — heterodox**
Chang, Ha-Joon (2002). *Kicking Away the Ladder: Development Strategy in Historical Perspective.* Anthem Press, London. ISBN 1843310279.
→ [Wikipedia overview](https://en.wikipedia.org/wiki/Kicking_Away_the_Ladder)

---

## A2 — Development Objectives: Growth-first vs Equity-first

**pole_A — growth**
Commission on Growth and Development (2008). *The Growth Report: Strategies for Sustained Growth and Inclusive Development.* World Bank, Washington, DC. Chaired by Michael Spence (Nobel laureate).
→ [World Bank Open Knowledge Repository](https://openknowledge.worldbank.org/handle/10986/6507)

**pole_B — equity**
Sen, Amartya (1999). *Development as Freedom.* Oxford University Press. ISBN 9780198297581.
→ [OUP product page](https://global.oup.com/academic/product/development-as-freedom-9780198297581)
→ [IEP entry on Sen's capability approach](https://iep.utm.edu/sen-cap/)

---

## A3 — Fiscal Policy: Debt-discipline vs Fiscal-space

**pole_A — debt-discipline**
International Monetary Fund and World Bank (2017). *Review of the Debt Sustainability Framework for Low-Income Countries: Proposed Reforms.* LIC-DSF originally established 2005; revised 2017.
→ [IMF policy paper (2017 review)](https://www.imf.org/en/Publications/Policy-Papers/Issues/2017/10/02/pp082217LIC-DSF)
→ [WB IEG independent evaluation of LIC-DSF use](https://ieg.worldbankgroup.org/evaluations/world-banks-role-and-use-low-income-country-debt-sustainability-framework)

**pole_B — fiscal-space**
Blanchard, Olivier (2019). *Public Debt and Low Interest Rates.* American Economic Review 109(4): 1197–1229. AEA Presidential Address.
→ [AEA article page (DOI 10.1257/aer.109.4.1197)](https://www.aeaweb.org/articles?id=10.1257%2Faer.109.4.1197)
→ [PIIE working-paper version (WP 19-4)](https://www.piie.com/sites/default/files/documents/wp19-4.pdf)

---

## Lexicon provenance — honest disclosure

The per-pole lexicons in `shared_axes.txt` and in `pipeline/perturb/generate_v8_dataset.py` (`POLE_LEXICONS`) are **author-curated**. They are informed by:
- The cited source's own vocabulary (e.g., Williamson's reform headings, Chang's "infant industry" and "policy space", Sen's "capabilities" and "functionings", Blanchard's "r<g").
- Standard policy discourse where the position appears (e.g., LIC-DSF operational terms from IMF/WB documents).

They are **not lifted from any peer-reviewed NLP work.** No published NLP lexicon covers these specific positions. For comparison, validated lexicons in adjacent NLP work include:
- **Moral Foundations Dictionary** (Graham, Haidt et al.) for moral psychology
- **LIWC** (Linguistic Inquiry and Word Count) for psychological/social constructs
- **CARDS** (Coan 2021) for climate-skeptic claims (taxonomy, not a token lexicon)

Boydstun's Media Frames Corpus (Card et al. 2015) has frame *definitions* validated by Cohen's κ on annotators but does not publish per-frame token lexicons.

**Implication for the benchmark.** The lexicons serve two operational purposes:
1. They guide Stage B/C generation (the LLM uses lexicon tokens to write in the pole's voice).
2. They function as deterministic Python checks (`POLE_LEXICONS`) for C4 (pole-A loaded) and C5 (pole-B loaded and distinct).

Their *coverage and external validity have not been empirically validated*. A future step would be to (a) derive tokens via TF-IDF on pole-coded corpora (e.g., IMF Article IV reports vs. Stiglitz op-eds for A1), and (b) measure inter-annotator agreement on which tokens signal which pole. This is noted as a limitation.

---

## Considered and dropped

**Donor-North vs recipient-South** — south pole has anchored academic literature (Prebisch 1950, Wallerstein 1974, Hickel 2017) but the north pole has no symmetric academic anchor. Burnside & Dollar (2000, *American Economic Review*) is about aid effectiveness conditional on policy environment, not about whether conditionality is legitimate. Unbalanced.

**Climate-orthodox vs climate-justice** — Stern Review (2006) and Klein (2014) articulate real positions but do not engage at the academic level (mainstream environmental economics vs. critical theory; different methodologies). The "axis" framing implies a paired debate that is not happening.

Both are interesting future-work directions using methods that do not require pre-defining the paired cut (e.g., frame-induction from corpus).
