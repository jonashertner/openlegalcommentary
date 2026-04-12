# openlegalcommentary

Open-access, AI-generated, daily-updated legal commentary on Swiss federal law.

## Project structure

- `guidelines/` — Authoring guidelines (global + per-law) and quality evaluation rubric
- `content/` — Generated commentary organized by law, article, concept, and contested question
- `agents/` — Agent pipeline (coordinator, law agents, evaluator, translator)
- `site/` — Astro static site (4 languages: DE/FR/IT/EN, URL-based routing under `/{lang}/`)
- `export/` — HuggingFace dataset export
- `scripts/` — Utility scripts (article fetcher, validation, citation audit, Botschaft digestion)
- `tests/` — Test suite (189 tests)
- `docs/superpowers/specs/` — Design specs, roadmap, experiment results
- `docs/superpowers/plans/` — Implementation plans

## Content schema

Each article lives in `content/{law}/art-{number}/` with:
- `meta.yaml` — Article metadata and per-layer state
- `summary.md` — Plain-language summary (B1 reading level)
- `doctrine.md` — Doctrinal analysis with Randziffern
- `caselaw.md` — Case law digest, daily updated
- `*.fr.md` / `*.it.md` / `*.en.md` — French/Italian/English translations

Content types: article, concept, contested, comparison

Concept pages live in `content/concepts/{slug}/` with `meta.yaml` (ConceptMeta).
Contested pages live in `content/contested/{slug}/` with `meta.yaml` (ContestedMeta).

## Guidelines

All authoring is governed by `guidelines/global.md` (core standards) and
`guidelines/{law}.md` (law-specific context). Quality evaluation uses
`guidelines/evaluate.md`. Cross-cutting content types have their own guidelines:
`guidelines/concepts.md` and `guidelines/contested.md`.

## Laws covered

BV (SR 101), ZGB (SR 210), OR (SR 220), ZPO (SR 272),
StGB (SR 311.0), StPO (SR 312.0), SchKG (SR 281.1), VwVG (SR 172.021),
BGFA (SR 935.61)

**Content state:** BV and BGFA have substantial doctrine coverage with
Sonnet 4.6 quality. Other 7 laws have bootstrapped content from Opus 4
that hasn't been regenerated yet.

## Agent pipeline architecture

### Model configuration (`agents/config.py`)

- **Doctrine generation:** Sonnet 4.6 (`claude-sonnet-4-6`) — switched from
  Opus after Phase 0 experiment showed 10-13x cost reduction with equal or
  better quality. See `docs/superpowers/specs/2026-04-10-phase-0-sonnet-test-results.md`.
- **Evaluator:** Opus 4.6 (`claude-opus-4-6`) — independent quality judge.
- **Caselaw/Summary/Translator:** Sonnet 4.6.
- **Prompt caching:** enabled on system prompt in `agents/anthropic_client.py`
  (ephemeral cache, ~$0.40/article savings).

### Generation loop (`agents/generation.py`)

Three safety layers protect content quality:

1. **Delete-on-retry:** at the start of each attempt, the target layer file
   is deleted so the agent sees a blank slate. Without this, Sonnet sometimes
   sees existing content and exits without writing (the "write-skip" failure).
2. **Write-skip safeguard:** after each attempt, hashes the file before/after.
   If unchanged, the attempt is marked as failed and retried with explicit
   feedback telling the agent to call `write_layer_content`.
3. **Rollback-on-failure:** a pre-generation snapshot is captured and restored
   if ALL retry attempts fail. No article is ever left worse than its baseline.

### Doctrine prompt (`agents/prompts.py`)

The doctrine `LAYER_INSTRUCTIONS` include:
- Mandatory final action: `write_layer_content` call required
- Literature-format citation preference (avoids fabricated BSK N. numbers)
- Konzision discipline (anti-redundancy guidance)
- Anti-fabrication guard: "ONLY cite specifics that appear in the Materialien
  block provided. Do not supplement from training knowledge."
- No vote counts (not legally relevant)

### Materialien integration (`agents/references.py`)

The `format_preparatory_materials()` function loads and formats up to 4 source
types per article:
- Botschaft (Federal Council Message) — BBl page refs, legislative intent
- Erläuterungsbericht (Explanatory Report) — pre-Botschaft rationale
- AB Ständerat (Council of States debates) — named speakers, quotes
- AB Nationalrat (National Council debates) — named speakers, contested points

Data files in `scripts/preparatory_materials/`:
- `{law}.json` — Botschaft per-article digest
- `{law}_erlaeuterungsbericht.json` — Erläuterungsbericht digest
- `{law}_ab_staenderat.json` — AB Ständerat per-article debate data
- `{law}_ab_nationalrat.json` — AB Nationalrat per-article debate data

**Current coverage:** BV has all 4 sources (67-83 articles per source).
BGFA has Botschaft only (37 articles).

## Citation audit tool

`scripts/citation_patterns.py` + `scripts/verify_citations.py`

Extracts citations from doctrine layers (BGE, BGer, BSK, CR, BBl, St. Galler,
literature) and verifies them against reference data:
- BGE/BGer: trusted (verifiable via opencaselaw)
- BSK: verified against `scripts/commentary_refs/{law}_refs.json` — checks
  both top-level `authors` AND `positions[].author` / `controversies[]` (loose match)
- BBl: verified against preparatory materials data (when available)
- Literature: unchecked (extraction defined but not wired into verification)

Run: `uv run python -m scripts.verify_citations --law BV --summary`

**Current BV state:** 76 flagged citations across 20 articles (down from 290
at the start of the quality arc).

## Materialien pipeline (Botschaften + AB + Erläuterungsberichte)

### Source discovery and download

Source PDFs for BV are from the BJ archive:
https://www.bj.admin.ch/bj/de/home/staat/archiv/bundesverfassung.html

Downloaded to `data/botschaften/bv-materialien/` (gitignored).
Extracted text in `data/botschaften/*.txt` (gitignored).

### Digestion (`scripts/digest_botschaften.py`)

Sends extracted text to Claude in chunks (~400k chars each) with article
numbers AND titles for correct mapping. The title-matching approach is
essential because the Botschaft uses draft article numbering (VE 96) that
differs from the final 1999 BV.

Features:
- Automatic chunking at page boundaries for texts > 400k chars
- Streaming mode for long API calls
- JSON repair for truncated output (trailing commas, unclosed braces)
- Incremental save after each chunk
- Budget cap (`--max-budget`)

For AB (parliamentary debate) digestion, use a custom prompt (see the
one-off scripts used in the April 2026 session — not yet formalized into
a reusable command).

## Commands

### Core pipeline
- `uv run pytest` — run tests (189 tests)
- `uv run ruff check .` — lint
- `uv run python -m agents.pipeline daily` — run daily update pipeline
- `uv run python -m agents.pipeline single BV 8 --layers doctrine` — generate one layer for one article
- `uv run python -m agents.pipeline single BV 75 --suffix b --layers doctrine` — suffix article
- `uv run python -m agents.pipeline bootstrap --law BV` — bootstrap one law
- `uv run python -m agents.pipeline bootstrap --max-budget 50` — bootstrap with budget limit

### Citation audit
- `uv run python -m scripts.verify_citations --law BV --summary` — audit one law
- `uv run python -m scripts.verify_citations --law BV --article 8` — audit one article
- `uv run python -m scripts.verify_citations --all --summary` — audit all laws

### Materialien pipeline
- `uv run python -m scripts.discover_botschaften` — discover Botschaften via parliament API
- `uv run python -m scripts.download_botschaften --law BV` — download Botschaft PDFs
- `uv run python -m scripts.extract_botschaften --law BV` — extract text from PDFs
- `uv run python -m scripts.digest_botschaften --law BV --model claude-sonnet-4-6` — digest per article

### Content management
- `uv run python -m scripts.scaffold_content` — scaffold content directories
- `uv run python -m scripts.fetch_articles` — fetch article lists from opencaselaw
- `uv run python scripts/validate_content.py` — validate content schema

### Site
- `cd site && npm run dev` — start local dev server
- `cd site && npm run build` — build static site (includes Pagefind; always use this, not `astro build`)
- `cd site && npm run preview` — preview built site

## Known issues and next steps

See `docs/superpowers/specs/2026-04-11-world-class-improvements-backlog.md` for
the full prioritized backlog (~70 items across 11 categories).

**Priority items:**
1. Regenerate BV Grundrechte (Art. 7-36) with Materialien — the validated
   approach produces world-class Entstehungsgeschichte with named speakers,
   BBl pages, and real quotes
2. Fix suffix article statute-text bug (34 BV articles affected)
3. Expand Materialien to other laws (each needs its own BJ archive source)
4. Cross-reference click-through on the site (→ Art. 8 BV should be a link)
5. BGE auto-linking to opencaselaw.ch

**Write-skip rate:** ~20% on BV articles (caught by safeguard, retried
automatically). Root cause: Sonnet sometimes exits the agent loop without
calling `write_layer_content`, especially when BSK reference data is injected.
The delete-on-retry + write-skip safeguard handles this but costs extra
retries. Further prompt optimization may reduce the rate.

## Deployment

GitHub Pages via `.github/workflows/build-site.yml`. Triggered on push to
main when content/site/scripts/agents paths change. Build takes ~10 minutes.

CI runs lint + tests on every push (`.github/workflows/ci.yml`).
HuggingFace export runs on content changes (`.github/workflows/export-huggingface.yml`).
