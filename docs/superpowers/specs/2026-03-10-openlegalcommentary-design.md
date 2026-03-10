# openlegalcommentary.ch — Design Specification

**Date:** 2026-03-10
**Status:** Approved

## Mission

An open-access, AI-generated, daily-updated legal commentary on the most relevant Swiss federal laws. Built on the principle that Swiss law belongs to the people — accessible from citizen to Supreme Court judge, updated every night, free forever.

## Scope

Eight core Swiss federal laws, all from day one:

| Law | SR Number | Approx. Articles |
|-----|-----------|-------------------|
| BV (Bundesverfassung) | 101 | ~200 |
| ZGB (Zivilgesetzbuch) | 210 | ~980 |
| OR (Obligationenrecht) | 220 | ~1180 |
| ZPO (Zivilprozessordnung) | 272 | ~410 |
| StGB (Strafgesetzbuch) | 311.0 | ~400 |
| StPO (Strafprozessordnung) | 312.0 | ~460 |
| SchKG (Schuldbetreibungs- und Konkursgesetz) | 281.1 | ~350 |
| VwVG (Verwaltungsverfahrensgesetz) | 172.021 | ~74 |

**Total: ~4,050 articles × 3 layers × 3 languages = ~36,000 content units**

## Audiences

All of the following, served simultaneously through the layered content model:

1. **Legal practitioners** (lawyers, judges) — practical reference for daily work
2. **Law students** — study aid, doctrinal orientation
3. **Legal scholars** — research-grade, comprehensive doctrinal analysis
4. **General public** — accessible plain-language explanations

## Content Model

### Per-article structure

Each article gets a directory in the repository:

```
content/
  or/
    art-041/
      meta.yaml          # Article metadata, per-layer state
      summary.md         # Layer 1: Plain-language summary
      doctrine.md        # Layer 2: Doctrinal analysis
      caselaw.md         # Layer 3: Case law digest
      summary.fr.md      # French translations
      summary.it.md      # Italian translations
      doctrine.fr.md
      doctrine.it.md
      caselaw.fr.md
      caselaw.it.md
```

### Three layers

**Layer 1 — Ubersicht (Summary)**
- Audience: General public, law students
- Reading level: B1 German — a motivated Gymnasium graduate must understand it fully
- Length: 150–300 words
- Content: What the article does, who it affects, key practical consequence
- Technical terms explained in parentheses on first use
- Concrete examples where abstract rules would otherwise remain opaque
- Update frequency: When doctrine layer changes

**Layer 2 — Doktrin (Doctrinal Analysis)**
- Audience: Scholars, practitioners
- Structure: Numbered marginal notes (Randziffern / N.)
- Content:
  - Legislative history (Botschaft reference, Materialien)
  - Systematic context (position within the law's structure)
  - Doctrinal debates (Streitfragen) with majority/minority positions, named authors
  - Practical application guidance
- Minimum 3 secondary sources per article
- Update frequency: When case law layer shifts significantly (new leading case, doctrinal shift), or weekly

**Layer 3 — Rechtsprechung (Case Law Digest)**
- Audience: Practitioners, scholars
- Structure: Grouped by topic, ordered by importance (leading cases first), then chronologically
- Per entry: Decision reference, date, core holding (Regeste-style), relevance to article, key passage quote
- Every BGE cited in opencaselaw for this article must appear
- Decisions from last 12 months must be included if relevant
- Update frequency: Daily (when new decisions appear in opencaselaw)

### meta.yaml

```yaml
law: OR
article: 41
title: "Haftung aus unerlaubter Handlung"
sr_number: "220"
absatz_count: 2
fedlex_url: "https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de#art_41"
lexfind_id: 25688
lexfind_url: "https://www.lexfind.ch/tol/25688/de"
in_force_since: "2026-01-01"
layers:
  summary:
    last_generated: "2026-03-09"
    last_reviewed: "2026-03-01"
    version: 3
    quality_score: 0.94
  doctrine:
    last_generated: "2026-03-07"
    trigger: "new_leading_case"
    version: 12
    quality_score: 0.96
  caselaw:
    last_generated: "2026-03-10"
    new_decisions_count: 2
    version: 187
    total_decisions: 47
    quality_score: 0.92
```

### Languages

- German is the authoritative version
- French and Italian are AI-translated from German by the translation agent
- Legal terminology must use official translations (from Fedlex termdat)
- Translations regenerated when their source layer changes

## Agent Architecture

Inspired by Karpathy's autoresearch pattern: human edits the program (`guidelines/*.md`), agents edit the output (`content/`).

### Agents

```
┌─────────────────────────────────────────────────┐
│                 Coordinator Agent                │
│  - Orchestrates daily run                       │
│  - Queries opencaselaw for new decisions        │
│  - Maps decisions to laws and articles          │
│  - Dispatches law agents in parallel            │
│  - Cross-reference consistency check            │
│  - Merges law branches to main                  │
│  - Triggers site build + HuggingFace export     │
│  - Generates daily changelog                    │
└────────────┬────────────────────────────────────┘
             │
     ┌───────┼───────┬───────┬───────┬───────┬───────┬───────┐
     ▼       ▼       ▼       ▼       ▼       ▼       ▼       ▼
  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐
  │ BV  │ │ ZGB │ │ OR  │ │ ZPO │ │StGB │ │StPO │ │SchKG│ │VwVG │
  │Agent│ │Agent│ │Agent│ │Agent│ │Agent│ │Agent│ │Agent│ │Agent│
  └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘
     │       │       │       │       │       │       │       │
     ▼       ▼       ▼       ▼       ▼       ▼       ▼       ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                     Evaluator Agent                         │
  │  - Quality gate: non-negotiables + scored dimensions        │
  │  - Reject/retry cycle (max 3 attempts)                      │
  │  - Flags for human review if threshold not met              │
  └─────────────────────────────────────────────────────────────┘
     │
     ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                    Translator Agent                          │
  │  - DE → FR, DE → IT for all changed layers                  │
  │  - Uses Fedlex termdat for official legal terminology        │
  └─────────────────────────────────────────────────────────────┘
```

### Per-law agent design

Each law agent is a parameterized instance of the same base agent, configured with:

- **Global guidelines** (`guidelines/global.md`) — core principles, layer specs, quality standards
- **Per-law guidelines** (`guidelines/{law}.md`) — domain context, key treatises, cross-reference patterns, structural notes
- **Evaluation rubric** (`guidelines/evaluate.md`) — quality scoring criteria

Following the autoresearch pattern:
- Human refines `guidelines/*.md` (the "program")
- Agent generates/updates `content/` (the "output")
- Quality evaluation determines keep/discard (the "metric")

### Tools available to each law agent

- **opencaselaw MCP** (single data source for law text AND case law):
  - Law text: `get_law` (article enumeration + full article text), `search_laws` (full-text search across statutes)
  - Legislation metadata: `get_legislation` (LexFind IDs, Fedlex URLs, in-force dates), `search_legislation` (33,000+ texts)
  - Case law: `search_decisions`, `find_citations`, `find_leading_cases`, `get_decision`, `get_case_brief`
  - Analysis: `get_statistics`, `analyze_legal_trend`, `find_appeal_chain`
- **Content tools**: Read/write article directories, meta.yaml management
- **Cross-reference resolver**: Validate and create links between articles across laws

### Daily pipeline

```
GitHub Actions cron (02:00 CET)
  │
  ▼
Coordinator: query opencaselaw for new decisions since last run
  │
  ▼
Coordinator: map decisions → laws → articles
  │
  ├──► BV Agent (parallel)
  ├──► ZGB Agent (parallel)
  ├──► OR Agent (parallel)
  ├──► ZPO Agent (parallel)
  ├──► StGB Agent (parallel)
  ├──► StPO Agent (parallel)
  ├──► SchKG Agent (parallel)
  └──► VwVG Agent (parallel)
       │
       Each agent:
       1. Receive batch of new decisions for its law
       2. Map decisions to specific articles
       3. Regenerate case law layer for affected articles
       4. Evaluate: does new case law shift doctrine?
       5. If yes → regenerate doctrine layer → regenerate summary layer
       6. Self-evaluate against guidelines/evaluate.md
       7. If quality >= threshold → stage changes
       8. If quality < threshold → retry (max 3), then flag for human
       │
       ▼
Evaluator: cross-agent consistency check
  │
  ▼
Translator: DE → FR/IT for all changed layers
  │
  ▼
Coordinator:
  1. Merge all changes to main
  2. Trigger Astro site build
  3. Trigger HuggingFace export
  4. Generate daily changelog
  │
  ▼
Published: openlegalcommentary.ch + HuggingFace
```

### Initial generation

One-time bootstrap: generate all ~4,050 articles × 3 layers. Run as a batch job, parallelized across law agents. Estimated ~$500–1,000 in API costs. Run once, then switch to incremental daily updates.

## Quality Standards

### Core Principles

**This commentary exists to make Swiss law accessible, understandable, and useful to every person it affects — from the Federal Supreme Court judge to the citizen reading their rights for the first time. It upholds the Swiss legislative tradition that law belongs to the people, not to the profession.**

1. **Academic Excellence** — Every statement traceable to a primary source. Doctrinal positions attributed precisely — no "die herrschende Lehre" without naming authors. Minority positions presented fairly.
2. **Precision** — Legal terms used exactly as defined in the law. No synonyms where the law uses a specific term. Citations complete and verifiable. Temporal scope explicit.
3. **Concision** — Every sentence earns its place. No filler, no repetition, no hedging. If it can be said in fewer words without losing meaning, it must be.
4. **Relevance** — Lead with what matters most in practice. Theoretical debates only when they affect outcomes. Deprecated doctrine marked, not elaborated.
5. **Accessibility** — Summary layer comprehensible to a Gymnasium graduate. Technical terms always explained on first use. Concrete examples for abstract rules.
6. **Professionalism** — Neutral, objective tone. No advocacy. Consistent terminology across all 8 laws.

### Quality evaluation

**Non-negotiables (binary — any failure rejects the output):**
- No unsourced legal claims
- No factual errors (holdings must match actual decisions, verified against opencaselaw)
- No missing leading cases (all BGE for this article must appear in case law layer)
- Correct legal terminology (terms match SR text exactly)
- Structural completeness (all required sections present)

**Scored dimensions (must exceed threshold):**
- Precision: 0.95
- Concision: 0.90
- Accessibility: 0.90
- Relevance: 0.90
- Academic rigor: 0.95

### Evaluation loop

```
Generate layer
  │
  ▼
Evaluate against guidelines/evaluate.md
  │
  ├── All non-negotiables pass AND scores >= thresholds → Publish
  │
  ├── Non-negotiable failure OR scores < threshold → Retry with feedback
  │   (max 3 attempts)
  │
  └── Still failing after 3 attempts → Flag for human review
```

## Drafting Materials

**Phase 1 (launch):** Reference by citation only. Commentary cites BBl numbers and links to Fedlex. Does not store full Botschaft text.

**Phase 2 (future):** Ingest Botschaften, committee reports, Amtliches Bulletin into a searchable corpus. Law agents query at generation time for richer legislative history sections.

## Website

### Technology

- **Framework:** Astro (content-focused, Markdown-native, fast builds)
- **Hosting:** GitHub Pages (via CNAME to openlegalcommentary.ch)
- **Build trigger:** GitHub Actions on content changes to main

### Navigation

```
openlegalcommentary.ch/
├── /                           Landing page: mission, 8 law cards
├── /{law}                      Law overview: table of contents, stats
├── /{law}/{article}            Article page: 3 layers, tab navigation
├── /{law}/{article}?layer=...  Direct link to specific layer
├── /search                     Full-text search across all commentary
├── /about                      Mission, methodology, guidelines
├── /changelog                  Daily auto-generated update log
└── /api                        Dataset info, HuggingFace link
```

### Visual Design

**Design language: International Typographic Style (Schweizer Typografie)**

The commentary inherits from the Swiss design tradition — clarity *is* beauty.

**Typography:**
- Primary (headings, navigation): Inter — variable weight, screen-optimized
- Body (legal text, commentary): Source Serif 4 — readable serif, scholarly authority
- Citations/references: JetBrains Mono
- Scale: Perfect fourth (1.333) modular scale
- Measure: 65–75 characters per line, always

**Grid:**
- 12-column fluid grid, max-width 1440px
- Content column: 720px optimal reading width
- Generous margins — white space is not wasted space
- Baseline grid: all text aligns to 8px vertical rhythm

**Color:**
- Near-black on warm white (#1a1a1a on #fafaf8)
- One accent: Swiss red (#E8000D) — links, active states
- Subtle warm grays for hierarchy (#6b6b6b, #e5e5e3)
- No gradients, no shadows, no decoration
- Dark mode: inverted with same restraint

**Principles:**
- No ornament — every pixel serves comprehension
- The design disappears — the reader sees only the law and its meaning
- Mobile-first: lawyers in courtrooms, students on trains
- No login, no paywall — open access, period

### Article page layout

- Law text (from Fedlex) always visible at top as fixed reference
- Three tabs below: Ubersicht | Doktrin | Rechtsprechung
- BGE references hyperlink to opencaselaw.ch
- SR cross-references hyperlink to the relevant article within the commentary
- Botschaft references link to Fedlex
- Language switcher (DE/FR/IT), defaults to browser language
- Breadcrumb: Law → Part → Title → Article
- Article pagination: ← previous | next →
- Footer: last updated date, source count, version

### Responsive behavior

- **Desktop (>1024px):** Full grid, centered content column, law tabs in top bar
- **Tablet (768–1024px):** Content fills width with 32px padding
- **Mobile (<768px):** Law selector becomes dropdown, layer tabs become full-width pills, bottom bar navigation

### Surpassing the Basler Kommentar

This is not a digital BSK. It is what a legal commentary would be if invented today:

| BSK limitation | Our advantage |
|---|---|
| CHF 300–500 per volume, paywall | Free, forever, for everyone |
| New edition every 5–8 years | Updated every night |
| Practitioners only | Citizen to Supreme Court judge |
| Primitive keyword search | Full-text + semantic search across all laws |
| Dead cross-references ("siehe OR 41") | Live hyperlinks, bidirectional |
| Stale case law on publication day | Today's BGE, tomorrow in the commentary |
| One language per edition | DE/FR/IT, always in sync |
| Print-optimized typography | Screen-native Swiss typographic excellence |
| Opaque authorial choices | Every source linked, every update logged |

## Infrastructure

### Repository structure

```
openlegalcommentary/
├── .github/
│   └── workflows/
│       ├── daily-update.yml        # Cron: triggers coordinator agent
│       ├── build-site.yml          # Builds static site on content changes
│       └── export-huggingface.yml  # Publishes dataset to HuggingFace
├── guidelines/
│   ├── global.md                   # Core principles & standards
│   ├── evaluate.md                 # Quality rubric
│   ├── bv.md
│   ├── zgb.md
│   ├── or.md
│   ├── zpo.md
│   ├── stgb.md
│   ├── stpo.md
│   ├── schkg.md
│   └── vwvg.md
├── content/                        # Generated commentary (Markdown)
│   ├── bv/art-001/ ...
│   ├── zgb/art-001/ ...
│   └── ...
├── agents/
│   ├── coordinator.py
│   ├── law_agent.py
│   ├── evaluator.py
│   ├── translator.py
│   └── tools/
│       ├── opencaselaw.py
│       ├── fedlex.py
│       └── content.py
├── site/                           # Astro static site
│   ├── src/
│   │   ├── layouts/
│   │   ├── pages/
│   │   └── components/
│   ├── astro.config.mjs
│   └── package.json
├── export/
│   └── huggingface.py
├── pyproject.toml
├── LICENSE-CODE                    # MIT
├── LICENSE-CONTENT                 # CC BY-SA 4.0
└── CLAUDE.md
```

### Technology stack

| Component | Choice | Rationale |
|---|---|---|
| Agent framework | Claude Agent SDK (Python) | Native Claude integration, tool use |
| LLM for doctrine + evaluation | Claude Opus | Highest quality for complex legal analysis |
| LLM for case law + translation | Claude Sonnet | Cost-efficient for structured tasks |
| Static site | Astro | Content-focused, Markdown-native, fast |
| CI/CD | GitHub Actions | Free for public repos, cron support |
| Dataset hosting | HuggingFace Datasets | Standard, Parquet support |
| Case law source | opencaselaw MCP | Existing infrastructure, daily updated |
| Law text + legislation metadata | opencaselaw MCP (`get_law`, `get_legislation`) | LexFind-backed, current consolidated texts |

### Cost estimate

**Daily steady state** (~50 new decisions/day, ~30 affected articles):
- Case law generation (Sonnet): ~$0.30
- Doctrine regeneration (Opus, ~5/day): ~$0.75
- Summary regeneration (Sonnet): ~$0.05
- Quality evaluation (Opus): ~$5.25
- Translation (Sonnet): ~$0.70
- **Total: ~$7/day, ~$210/month**

**Initial bootstrap** (all ~4,050 articles × 3 layers): ~$500–1,000 one-time

### Licensing

- **Code:** MIT License
- **Content:** CC BY-SA 4.0 (commentary stays open, derivatives must share alike)
