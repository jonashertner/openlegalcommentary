# Cantonal Kantonsverfassungen on Site — Design Spec

Date: 2026-04-13

## Goal

Display the 26 cantonal constitutions (Kantonsverfassungen) on the site as
browsable law text — article lists and Gesetzestext. No commentary, no
translations. Each law in its canton's publication language.

## Data pipeline

### Fetcher script

`scripts/fetch_cantonal_laws.py` — calls opencaselaw `get_legislation` API for
each canton's KV. Takes a list of cantons or `--all`. Saves per-law JSON.

Discovery: use `search_legislation(query="Verfassung"/"Constitution"/"Costituzione",
canton=XX)` to find the LexFind ID, then `get_legislation(lexfind_id=N)` for
full article text.

### Per-law JSON schema

Stored in `scripts/cantonal/{canton}-kv.json`:

```json
{
  "canton": "ZH",
  "law_key": "zh-kv",
  "sr_number": "101",
  "language": "de",
  "title": "Verfassung des Kantons Zürich",
  "lexfind_id": 21736,
  "fetched_at": "2026-04-13",
  "article_count": 147,
  "articles": [
    { "number": 1, "suffix": "", "raw": "1", "title": "Kanton Zürich" }
  ],
  "article_texts": {
    "1": [
      { "num": "1", "text": "Der Kanton Zürich ist ein souveräner Stand..." },
      { "num": "2", "text": "Er gründet auf der Eigen-..." }
    ]
  }
}
```

Mirrors the shape of existing `article_lists.json` + `article_texts.json` but
self-contained per law.

### Language mapping

- **de**: ZH, BE, LU, UR, SZ, OW, NW, GL, ZG, SO, BS, BL, SH, AR, AI, SG, GR, AG, TG, VS
- **fr**: FR, VD, NE, GE, JU
- **it**: TI

## Site integration

### `laws.ts`

Extend `LawInfo` interface:

```ts
export interface LawInfo {
  abbr: string;        // "KV ZH"
  sr: string;          // "101" (cantonal SR number)
  slug: string;        // "zh-kv" — URL slug
  canton?: string;     // "ZH" — undefined for federal laws
  language?: string;   // "de" — primary publication language
  name: Record<Lang, string>;
  description: Record<Lang, string>;
}
```

Federal laws get `slug` derived from `abbr.toLowerCase()` (backward compat).
Cantonal laws use `{canton}-{lawtype}` pattern.

### `cantons.ts`

New file with 26 cantons: abbreviation, official name (4 langs), publication
language. Small, stable data — hardcoded.

### `content.ts`

New loader for cantonal data. When the site encounters a cantonal law slug
(e.g. `zh-kv`), reads from `scripts/cantonal/zh-kv.json` instead of the
federal `article_lists.json` / `article_texts.json`.

Functions to add/extend:
- `listCantonalArticles(slug)` — reads from per-law JSON
- `getCantonalArticleText(slug, articleRaw)` — reads article_texts from JSON
- Existing `listArticles`, `getArticleText` dispatch to cantonal loader when
  the law has a `canton` field

### `getStaticPaths`

Both `[law]/index.astro` and `[law]/[article].astro` currently hardcode
`['bv', 'zgb', ...]`. Change to derive dynamically from `LAWS` array (all
slugs, federal + cantonal).

### Language behavior

All routes generated for all 4 site languages. When viewing a cantonal law
in a non-native language (e.g. `/fr/zh-kv/art-1`), article text displays in
the law's original language. Existing `fallback-notice` mechanism used.

## Homepage & navigation

### Cantonal section

New section below federal laws grid: "Kantone" heading, grid of 26 canton
tiles (abbreviation + name). Each links to the canton's KV for now
(`/{lang}/zh-kv/`). When more laws are added per canton later, tiles link to
a canton index page instead.

### Article pages

Existing `[law]/[article].astro` handles cantonal laws with no changes to
the template. Commentary tabs (summary/doctrine/caselaw) don't appear when
there's no content — the page shows Gesetzestext only.

The left sidebar shows canton instead of SR number for cantonal laws.

## Not in scope

- Commentary generation (doctrine, summary, caselaw)
- Translations of law text or law names
- Law structure data (Titel/Kapitel/Abschnitt TOC headings)
- Cantonal laws beyond KVs
- Content directories in `content/` (no commentary to store)
