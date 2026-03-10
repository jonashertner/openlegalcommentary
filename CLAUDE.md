# openlegalcommentary

Open-access, AI-generated, daily-updated legal commentary on Swiss federal law.

## Project structure

- `guidelines/` — Authoring guidelines (global + per-law) and quality evaluation rubric
- `content/` — Generated commentary organized by law and article
- `agents/` — Agent pipeline (coordinator, law agents, evaluator, translator)
- `site/` — Astro static site
- `export/` — HuggingFace dataset export
- `scripts/` — Utility scripts (article fetcher, validation)
- `tests/` — Test suite

## Content schema

Each article lives in `content/{law}/art-{number}/` with:
- `meta.yaml` — Article metadata and per-layer state
- `summary.md` — Plain-language summary (B1 reading level)
- `doctrine.md` — Doctrinal analysis with Randziffern
- `caselaw.md` — Case law digest, daily updated
- `*.fr.md` / `*.it.md` — French/Italian translations

## Guidelines

All authoring is governed by `guidelines/global.md` (core standards) and
`guidelines/{law}.md` (law-specific context). Quality evaluation uses
`guidelines/evaluate.md`.

## Laws covered

BV (SR 101), ZGB (SR 210), OR (SR 220), ZPO (SR 272),
StGB (SR 311.0), StPO (SR 312.0), SchKG (SR 281.1), VwVG (SR 172.021)

## Commands

- `uv run pytest` — run tests
- `uv run ruff check .` — lint
- `uv run python scripts/validate_content.py` — validate content schema
- `uv run python scripts/fetch_articles.py` — fetch article lists from opencaselaw
- `uv run python -m agents.pipeline daily` — run daily update pipeline
- `uv run python -m agents.pipeline bootstrap` — bootstrap all articles (initial run)
- `uv run python -m agents.pipeline single OR 41` — generate layers for one article
- `uv run python -m agents.pipeline bootstrap --law OR` — bootstrap one law
- `uv run python -m agents.pipeline bootstrap --max-budget 50` — bootstrap with budget limit
- `uv run python -m agents.pipeline bootstrap --state-file state.json` — resume bootstrap from state
- `uv run python -m scripts.scaffold_content` — scaffold content directories from article lists
- `uv run python -m scripts.fetch_articles` — fetch article lists from opencaselaw
