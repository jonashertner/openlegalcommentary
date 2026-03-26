# World-Class Commentary System — Design

## Target Quality

Match the depth and rigor of the St. Galler Kommentar (Ehrenzeller/Schindler/Schweizer/Vallender, 4. Aufl. 2023) and BSK BV (Waldmann/Belser/Epiney, 2. Aufl. 2024). These are the gold standard for Swiss constitutional commentary.

## Current vs. Target

| Dimension | Current | Target |
|-----------|---------|--------|
| Randziffern per article | ~20 | 50–150 (scaled by significance) |
| Case law analysis | Lists decisions | Traces doctrinal evolution through case law |
| Comparative law | EMRK mention | Systematic comparison (DE, AT, FR, EU Charter) |
| Legislative history | Botschaft cited | Full history: Vernehmlassung, AB N/S, vote results |
| Scholarly discourse | Names 2-3 positions | Engages with reasoning, evidence, counter-arguments |
| Practical application | Generic examples | Domain-specific scenarios (tax, employment, education) |
| Temporal analysis | Static | Evolution of interpretation over time |
| Critical assessment | Descriptive | Evaluative: gaps, inconsistencies, reform proposals |
| Cross-references | Arrow notation | Explains interaction effect and systematic context |

## Architecture: Multi-Pass Deep Generation

Instead of one generation pass, use **specialized sub-agents** that each produce a section:

### Pass 1: Research Phase (no writing)

A research agent gathers all available information:

1. **Full case law corpus** — query opencaselaw for ALL decisions (not just top 20), analyze citation patterns, identify turning points
2. **Legislative history** — Botschaft, but also trace through parliamentary debates via Curia Vista
3. **Doctrinal landscape** — from BSK ref data + the law-specific guidelines, map all named positions
4. **Comparative parallels** — identify corresponding provisions in EMRK, German GG, Austrian B-VG, EU Charter
5. **Implementing legislation** — all federal laws that concretize this provision
6. **Recent developments** — decisions from last 2 years, pending initiatives, legislative reforms

Output: structured research brief (not prose)

### Pass 2: Historical Analysis

Generate the Entstehungsgeschichte section with:
- Constitutional genealogy (1848 → 1874 → 1999)
- Parliamentary debate specifics (AB N, AB S references)
- Vernehmlassung positions
- Popular vote results and context
- Subsequent amendments and their motivation

### Pass 3: Systematic & Comparative Analysis

Generate the systematic context with:
- Position within the constitution's structure
- Relationship to other fundamental rights / competence norms
- EMRK/international law parallels with substantive comparison
- Comparative constitutional law insights

### Pass 4: Doctrinal Core (Norminhalt)

The longest section. Generated per sub-topic of the article:
- For Art. 8: separate passes for Abs. 1 (equality), Abs. 2 (discrimination), Abs. 3 (gender), Abs. 4 (disability)
- Each sub-topic gets: definition, scope, limits, case law evolution, doctrinal positions, open questions
- Minimum 10 Randziffern per paragraph of the article text

### Pass 5: Case Law Synthesis

Not a list of decisions but a **narrative of doctrinal evolution**:
- Chronological analysis: how did the court's approach change?
- Identify landmark shifts and their doctrinal significance
- Group by thematic lines of jurisprudence
- Include key quotes with analysis of what they established

### Pass 6: Practical Application & Critical Assessment

- Domain-specific application scenarios
- Procedural aspects (burden of proof, standing, remedies)
- Critical evaluation: consistency, gaps, reform needs
- Open questions and future outlook

### Pass 7: Assembly & Quality Review

Combine all passes into a unified commentary:
- Ensure consistent Randziffern numbering
- Cross-reference between sections
- Verify all citations
- Check for redundancies between passes
- Apply the final evaluator

## Article Significance Classification

Not every article needs 150 Randziffern. Scale by significance:

| Category | Articles | Target N. | Budget |
|----------|----------|-----------|--------|
| **Tier 1: Foundational** | Art. 1-6, 8-10, 13, 26-27, 29, 36, 49, 190 (~20 articles) | 80–150 N. | $15–25/article |
| **Tier 2: Important** | Most fundamental rights, key competences (~60 articles) | 40–80 N. | $8–15/article |
| **Tier 3: Standard** | Organizational provisions, specific competences (~100 articles) | 25–50 N. | $4–8/article |
| **Tier 4: Brief** | Transitional provisions, repealed articles (~50 articles) | 10–25 N. | $2–4/article |

Total estimated cost for world-class BV: ~$1,500–2,500

## Key Literature Requirements

For every BV article, the doctrine MUST engage with:

1. **St. Galler Kommentar** (4. Aufl. 2023) — the author and their specific positions
2. **BSK BV** (2. Aufl. 2024) — the author and their specific positions
3. **Häfelin/Haller/Keller/Thurnherr** — Bundesstaatsrecht positions
4. **Müller/Schefer** (for fundamental rights) — Grundrechte positions
5. **Rhinow/Schefer/Uebersax** — Verfassungsrecht positions
6. **The Botschaft** (BBl reference) — always
7. **At least 3 BGE with analysis** — not just citation but analysis of what they established

For Tier 1 articles, additionally:
8. **Journal articles** (ZSR, ZBl, ZBJV, AJP) on the specific provision
9. **Dissertations/Habilitationen** on the topic
10. **Comparative law sources** (German BVerfG decisions, ECtHR case law)

## Implementation Plan

1. Build `scripts/generate_article_context.py` — automated research brief generation
2. Build `scripts/classify_articles.py` — significance tier classification
3. Update `agents/prompts.py` — multi-pass prompt templates
4. Update `agents/generation.py` — multi-pass generation pipeline
5. Update evaluation criteria — tier-specific quality thresholds
6. Run on Tier 1 articles first as proof of concept
7. Iterate on quality, then run full BV

## Success Criteria

A world-class commentary article should:
- Be citable in a Federal Supreme Court brief
- Contain every relevant BGE with analysis
- Present every major doctrinal position with author attribution
- Include comparative law perspective for fundamental rights
- Provide practical guidance for practicing lawyers
- Identify open questions and current debates
- Be internally consistent and well-structured
- Stand comparison with the corresponding St. Galler Kommentar entry
