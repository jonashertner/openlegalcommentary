# Cantonal KV on Site — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Display the 26 Kantonsverfassungen on the site with browsable article text, fetched from opencaselaw.

**Architecture:** A Python fetcher script calls the opencaselaw MCP tools (via direct API) to download each canton's constitution, storing per-law JSON files in `scripts/cantonal/`. The Astro site reads these files through an extended content lib, reusing the existing `[law]/index.astro` and `[law]/[article].astro` routes. A new canton section on the homepage links to each KV.

**Tech Stack:** Python (fetcher), TypeScript/Astro (site), opencaselaw API (data source)

---

## File Map

| Action | File | Purpose |
|--------|------|---------|
| Create | `scripts/cantonal/` | Directory for per-law JSON files |
| Create | `scripts/fetch_cantonal_laws.py` | Fetcher script — calls opencaselaw API, saves JSON |
| Create | `site/src/lib/cantons.ts` | Canton metadata (26 cantons, names, languages) |
| Modify | `site/src/lib/laws.ts` | Add `slug`, `canton?`, `language?` to `LawInfo`; add 26 KV entries |
| Modify | `site/src/lib/content.ts` | Load article lists/texts from cantonal JSON files |
| Modify | `site/src/pages/[lang]/[law]/index.astro:12-16` | Dynamic `getStaticPaths` from `LAWS` |
| Modify | `site/src/pages/[lang]/[law]/[article].astro:14-26` | Dynamic `getStaticPaths` from cantonal JSON |
| Modify | `site/src/pages/[lang]/index.astro` | Add cantonal section to homepage |
| Modify | `site/src/lib/i18n.ts` | Add translation keys for canton section |
| Create | `tests/test_fetch_cantonal_laws.py` | Tests for fetcher script |

---

### Task 1: Canton metadata module (`cantons.ts`)

**Files:**
- Create: `site/src/lib/cantons.ts`

- [ ] **Step 1: Create `cantons.ts` with 26 cantons**

```ts
// site/src/lib/cantons.ts
import type { Lang } from './i18n';

export interface Canton {
  code: string;        // "ZH"
  language: 'de' | 'fr' | 'it';
  name: Record<Lang, string>;
}

export const CANTONS: Canton[] = [
  { code: 'ZH', language: 'de', name: { de: 'Zürich', fr: 'Zurich', it: 'Zurigo', en: 'Zurich' } },
  { code: 'BE', language: 'de', name: { de: 'Bern', fr: 'Berne', it: 'Berna', en: 'Bern' } },
  { code: 'LU', language: 'de', name: { de: 'Luzern', fr: 'Lucerne', it: 'Lucerna', en: 'Lucerne' } },
  { code: 'UR', language: 'de', name: { de: 'Uri', fr: 'Uri', it: 'Uri', en: 'Uri' } },
  { code: 'SZ', language: 'de', name: { de: 'Schwyz', fr: 'Schwyz', it: 'Svitto', en: 'Schwyz' } },
  { code: 'OW', language: 'de', name: { de: 'Obwalden', fr: 'Obwald', it: 'Obvaldo', en: 'Obwalden' } },
  { code: 'NW', language: 'de', name: { de: 'Nidwalden', fr: 'Nidwald', it: 'Nidvaldo', en: 'Nidwalden' } },
  { code: 'GL', language: 'de', name: { de: 'Glarus', fr: 'Glaris', it: 'Glarona', en: 'Glarus' } },
  { code: 'ZG', language: 'de', name: { de: 'Zug', fr: 'Zoug', it: 'Zugo', en: 'Zug' } },
  { code: 'FR', language: 'fr', name: { de: 'Freiburg', fr: 'Fribourg', it: 'Friburgo', en: 'Fribourg' } },
  { code: 'SO', language: 'de', name: { de: 'Solothurn', fr: 'Soleure', it: 'Soletta', en: 'Solothurn' } },
  { code: 'BS', language: 'de', name: { de: 'Basel-Stadt', fr: 'Bâle-Ville', it: 'Basilea Città', en: 'Basel-Stadt' } },
  { code: 'BL', language: 'de', name: { de: 'Basel-Landschaft', fr: 'Bâle-Campagne', it: 'Basilea Campagna', en: 'Basel-Landschaft' } },
  { code: 'SH', language: 'de', name: { de: 'Schaffhausen', fr: 'Schaffhouse', it: 'Sciaffusa', en: 'Schaffhausen' } },
  { code: 'AR', language: 'de', name: { de: 'Appenzell Ausserrhoden', fr: 'Appenzell Rhodes-Extérieures', it: 'Appenzello Esterno', en: 'Appenzell Ausserrhoden' } },
  { code: 'AI', language: 'de', name: { de: 'Appenzell Innerrhoden', fr: 'Appenzell Rhodes-Intérieures', it: 'Appenzello Interno', en: 'Appenzell Innerrhoden' } },
  { code: 'SG', language: 'de', name: { de: 'St. Gallen', fr: 'Saint-Gall', it: 'San Gallo', en: 'St. Gallen' } },
  { code: 'GR', language: 'de', name: { de: 'Graubünden', fr: 'Grisons', it: 'Grigioni', en: 'Graubünden' } },
  { code: 'AG', language: 'de', name: { de: 'Aargau', fr: 'Argovie', it: 'Argovia', en: 'Aargau' } },
  { code: 'TG', language: 'de', name: { de: 'Thurgau', fr: 'Thurgovie', it: 'Turgovia', en: 'Thurgau' } },
  { code: 'TI', language: 'it', name: { de: 'Tessin', fr: 'Tessin', it: 'Ticino', en: 'Ticino' } },
  { code: 'VD', language: 'fr', name: { de: 'Waadt', fr: 'Vaud', it: 'Vaud', en: 'Vaud' } },
  { code: 'VS', language: 'de', name: { de: 'Wallis', fr: 'Valais', it: 'Vallese', en: 'Valais' } },
  { code: 'NE', language: 'fr', name: { de: 'Neuenburg', fr: 'Neuchâtel', it: 'Neuchâtel', en: 'Neuchâtel' } },
  { code: 'GE', language: 'fr', name: { de: 'Genf', fr: 'Genève', it: 'Ginevra', en: 'Geneva' } },
  { code: 'JU', language: 'fr', name: { de: 'Jura', fr: 'Jura', it: 'Giura', en: 'Jura' } },
];

export function getCantonByCode(code: string): Canton | undefined {
  return CANTONS.find(c => c.code.toLowerCase() === code.toLowerCase());
}
```

- [ ] **Step 2: Commit**

```bash
git add site/src/lib/cantons.ts
git commit -m "feat(site): add canton metadata module — 26 cantons with names and languages"
```

---

### Task 2: Extend `LawInfo` and add cantonal KV entries to `laws.ts`

**Files:**
- Modify: `site/src/lib/laws.ts`

- [ ] **Step 1: Add `slug`, `canton`, `language` fields to `LawInfo`**

In `site/src/lib/laws.ts`, change the interface to:

```ts
export interface LawInfo {
  abbr: string;
  sr: string;
  slug: string;           // URL slug — "bv" for federal, "zh-kv" for cantonal
  canton?: string;         // Two-letter canton code, undefined for federal
  language?: string;       // Primary publication language, undefined for federal (all 3)
  name: Record<Lang, string>;
  description: Record<Lang, string>;
}
```

Add `slug` to each existing federal law entry, matching the current behavior:
```ts
{ abbr: 'BV', sr: '101', slug: 'bv', name: { ... }, description: { ... } },
```

- [ ] **Step 2: Add 26 cantonal KV entries**

Add after the federal laws array:

```ts
export const CANTONAL_LAWS: LawInfo[] = [
  {
    abbr: 'KV ZH', sr: '101', slug: 'zh-kv', canton: 'ZH', language: 'de',
    name: { de: 'Verfassung des Kantons Zürich', fr: 'Verfassung des Kantons Zürich', it: 'Verfassung des Kantons Zürich', en: 'Verfassung des Kantons Zürich' },
    description: { de: 'Kantonsverfassung', fr: 'Constitution cantonale', it: 'Costituzione cantonale', en: 'Cantonal constitution' },
  },
  // ... all 26 cantons (see full list below)
];

// Combined list for site-wide use
export const ALL_LAWS: LawInfo[] = [...LAWS, ...CANTONAL_LAWS];
```

The 26 KV entries use the law title from the cantonal JSON files (fetched in Task 5). For the initial commit, use the titles from the expansion plan doc. The `name` field uses the original-language title in all 4 lang slots (no translation).

French-speaking cantons:
- FR: `Constitution du canton de Fribourg`
- VD: `Constitution du Canton de Vaud`
- NE: `Constitution de la République et Canton de Neuchâtel`
- GE: `Constitution de la République et canton de Genève`
- JU: `Constitution de la République et Canton du Jura`

Italian:
- TI: `Costituzione della Repubblica e Cantone Ticino`

All others: `Verfassung des Kantons {Name}`

- [ ] **Step 3: Update `getLawByAbbr` to search `ALL_LAWS` by slug**

Rename to `getLawBySlug` and update to check `slug` field:

```ts
export function getLawBySlug(slug: string): LawInfo | undefined {
  return ALL_LAWS.find(l => l.slug === slug);
}

// Backward compat — find by abbreviation (case-insensitive)
export function getLawByAbbr(abbr: string): LawInfo | undefined {
  return ALL_LAWS.find(l => l.abbr.toLowerCase() === abbr.toLowerCase() || l.slug === abbr.toLowerCase());
}

export function getLawAbbrList(): string[] {
  return ALL_LAWS.map(l => l.slug);
}
```

- [ ] **Step 4: Verify site still builds with federal laws**

```bash
cd site && npm run build
```

Expected: build succeeds, no type errors.

- [ ] **Step 5: Commit**

```bash
git add site/src/lib/laws.ts
git commit -m "feat(site): extend LawInfo with slug/canton/language, add 26 KV entries"
```

---

### Task 3: Cantonal content loader in `content.ts`

**Files:**
- Modify: `site/src/lib/content.ts`

- [ ] **Step 1: Add cantonal JSON loader**

Add near the top of `content.ts`, after the existing cache variables:

```ts
const CANTONAL_DIR = path.resolve(import.meta.dirname, '../../..', 'scripts', 'cantonal');

interface CantonalLawData {
  canton: string;
  law_key: string;
  sr_number: string;
  language: string;
  title: string;
  lexfind_id: number;
  fetched_at: string;
  article_count: number;
  articles: { number: number; suffix: string; raw: string; title: string }[];
  article_texts: Record<string, ArticleTextParagraph[]>;
}

const _cantonalCache: Record<string, CantonalLawData> = {};

function loadCantonalLaw(slug: string): CantonalLawData | null {
  if (_cantonalCache[slug]) return _cantonalCache[slug];
  const filePath = path.join(CANTONAL_DIR, `${slug}.json`);
  try {
    const raw = fs.readFileSync(filePath, 'utf-8');
    const data = JSON.parse(raw) as CantonalLawData;
    _cantonalCache[slug] = data;
    return data;
  } catch {
    return null;
  }
}

export function listCantonalLawSlugs(): string[] {
  try {
    return fs.readdirSync(CANTONAL_DIR)
      .filter(f => f.endsWith('.json'))
      .map(f => f.replace('.json', ''));
  } catch {
    return [];
  }
}
```

- [ ] **Step 2: Extend `listArticles` to handle cantonal laws**

At the end of `listArticles`, before the fallback to `article_lists.json`, add a cantonal check:

```ts
export function listArticles(law: string): { meta: ArticleMeta; dirName: string; slug: string }[] {
  const dirs = listArticleDirs(law);
  if (dirs.length > 0) {
    // ... existing content-dir logic unchanged ...
  }

  // Check cantonal JSON
  const cantonal = loadCantonalLaw(law.toLowerCase());
  if (cantonal) {
    return cantonal.articles.map((entry) => {
      const num = entry.number;
      const suffix = entry.suffix || '';
      const dirName = `art-${String(num).padStart(3, '0')}${suffix}`;
      const slug = `art-${num}${suffix}`;
      const meta: ArticleMeta = {
        law: cantonal.law_key.toUpperCase(),
        article: num,
        article_suffix: suffix,
        title: entry.title || '',
        sr_number: cantonal.sr_number,
        absatz_count: 1,
        fedlex_url: '',
        lexfind_url: '',
        in_force_since: '',
        layers: {},
      };
      return { meta, dirName, slug };
    });
  }

  // Fallback: build article list from article_lists.json (no content dirs)
  // ... existing code unchanged ...
}
```

- [ ] **Step 3: Extend `getArticleText` to check cantonal data**

Add a cantonal check at the start of `getArticleText`:

```ts
export function getArticleText(law: string, articleRaw: string, lang: string = 'de'): ArticleTextParagraph[] {
  // Check cantonal JSON first
  const cantonal = loadCantonalLaw(law.toLowerCase());
  if (cantonal) {
    return cantonal.article_texts[articleRaw] || [];
  }

  // Existing federal logic
  const texts = getArticleTexts(lang);
  const key = _findLawKey(texts, law);
  if (!key) return [];
  const artKey = _findArticleKey(texts[key], articleRaw);
  return artKey ? texts[key][artKey] : [];
}
```

- [ ] **Step 4: Extend `getLawStats` to handle cantonal laws**

Add cantonal check before the `article_lists.json` fallback:

```ts
export function getLawStats(law: string): LawStats {
  const dirs = listArticleDirs(law);
  if (dirs.length === 0) {
    // Check cantonal JSON
    const cantonal = loadCantonalLaw(law.toLowerCase());
    if (cantonal) {
      return { totalArticles: cantonal.article_count, completedArticles: 0, withContent: 0 };
    }

    const lists = getArticleLists();
    const count = lists[law.toUpperCase()]?.article_count ?? 0;
    return { totalArticles: count, completedArticles: 0, withContent: 0 };
  }
  // ... existing content-dir logic unchanged ...
}
```

- [ ] **Step 5: Extend `getArticleNav` to use cantonal article lists**

The existing `getArticleNav` calls `listArticleDirs` which only looks at content dirs. For cantonal laws with no content dirs, we need navigation from the article list:

```ts
export function getArticleNav(
  law: string,
  currentDirName: string
): { prev: { slug: string; title: string } | null; next: { slug: string; title: string } | null } {
  const dirs = listArticleDirs(law);

  if (dirs.length === 0) {
    // Use listArticles fallback (covers both article_lists.json and cantonal JSON)
    const articles = listArticles(law);
    const currentSlug = dirNameToSlug(currentDirName);
    const idx = articles.findIndex(a => a.slug === currentSlug);
    return {
      prev: idx > 0 ? { slug: articles[idx - 1].slug, title: articles[idx - 1].meta.title } : null,
      next: idx >= 0 && idx < articles.length - 1 ? { slug: articles[idx + 1].slug, title: articles[idx + 1].meta.title } : null,
    };
  }

  // Existing content-dir logic unchanged
  const idx = dirs.indexOf(currentDirName);
  // ... rest unchanged ...
}
```

Note: `dirNameToSlug` is a private function already defined at line 158. We need it here, and it's already in scope.

- [ ] **Step 6: Commit**

```bash
git add site/src/lib/content.ts
git commit -m "feat(site): extend content lib to load cantonal law data from per-law JSON"
```

---

### Task 4: Update `getStaticPaths` in both route files

**Files:**
- Modify: `site/src/pages/[lang]/[law]/index.astro:12-16`
- Modify: `site/src/pages/[lang]/[law]/[article].astro:14-26`

- [ ] **Step 1: Update law index page `getStaticPaths`**

In `site/src/pages/[lang]/[law]/index.astro`, replace the hardcoded law list:

```ts
// Old:
export function getStaticPaths() {
  const laws = ['bv', 'zgb', 'or', 'zpo', 'stgb', 'stpo', 'schkg', 'vwvg', 'bgfa'];
  return LANGS.flatMap(lang =>
    laws.map(law => ({ params: { lang, law } }))
  );
}

// New:
import { ALL_LAWS } from '../../../lib/laws';
import { listCantonalLawSlugs } from '../../../lib/content';

export function getStaticPaths() {
  const federalSlugs = LAWS.map(l => l.slug);
  const cantonalSlugs = listCantonalLawSlugs();
  const allSlugs = [...federalSlugs, ...cantonalSlugs];
  return LANGS.flatMap(lang =>
    allSlugs.map(law => ({ params: { lang, law } }))
  );
}
```

Also update the import: change `LAWS, getLawByAbbr` to `LAWS, ALL_LAWS, getLawByAbbr` (or just use the existing `getLawByAbbr` which already searches `ALL_LAWS` after Task 2).

- [ ] **Step 2: Update article page `getStaticPaths`**

In `site/src/pages/[lang]/[law]/[article].astro`, replace the hardcoded law list:

```ts
// Old:
export function getStaticPaths() {
  const laws = ['bv', 'zgb', 'or', 'zpo', 'stgb', 'stpo', 'schkg', 'vwvg', 'bgfa'];
  return LANGS.flatMap(lang =>
    laws.flatMap(law => {
      const dirs = listArticleDirs(law);
      return dirs.map(dir => {
        const match = dir.match(/^art-(\d+)([a-z]*)$/);
        const slug = match ? `art-${parseInt(match[1], 10)}${match[2] || ''}` : dir;
        return { params: { lang, law, article: slug } };
      });
    })
  );
}

// New:
import { listCantonalLawSlugs } from '../../../lib/content';

export function getStaticPaths() {
  const federalSlugs = ['bv', 'zgb', 'or', 'zpo', 'stgb', 'stpo', 'schkg', 'vwvg', 'bgfa'];
  const cantonalSlugs = listCantonalLawSlugs();
  const allSlugs = [...federalSlugs, ...cantonalSlugs];
  return LANGS.flatMap(lang =>
    allSlugs.flatMap(law => {
      // For federal laws, use content dirs; for cantonal, use listArticles
      const dirs = listArticleDirs(law);
      if (dirs.length > 0) {
        return dirs.map(dir => {
          const match = dir.match(/^art-(\d+)([a-z]*)$/);
          const slug = match ? `art-${parseInt(match[1], 10)}${match[2] || ''}` : dir;
          return { params: { lang, law, article: slug } };
        });
      }
      // Cantonal or article_lists.json fallback
      const articles = listArticles(law);
      return articles.map(art => ({ params: { lang, law, article: art.slug } }));
    })
  );
}
```

- [ ] **Step 3: Update article page sidebar for cantonal laws**

In `[article].astro`, the sidebar currently shows "Gesetz" and "SR {meta.sr_number}". For cantonal laws, show the canton name instead. Around line 148-150, update:

```astro
{lawInfo.canton ? (
  <>
    <div class="label">Kanton</div>
    <div class="meta-value">{lawInfo.canton}</div>
    <div class="meta-sub">{lawInfo.sr}</div>
  </>
) : (
  <>
    <div class="label">Gesetz</div>
    <div class="meta-value">{lawInfo.abbr.toUpperCase()}</div>
    <div class="meta-sub">SR {meta.sr_number}</div>
  </>
)}
```

- [ ] **Step 4: Update Gesetzestext source link for cantonal laws**

The `Gesetzestext.astro` component shows a "Fedlex" link. For cantonal laws there's no Fedlex URL, so it shouldn't render. This already works — `fedlexUrl` will be empty string, and the component only renders the link when `resolvedFedlexUrl` is truthy. Verify this is the case (it is — `fedlexUrl` comes from `meta.fedlex_url` which will be `''` for cantonal articles).

No code change needed, but verify during testing.

- [ ] **Step 5: Verify build with a test cantonal JSON**

Create a minimal test file to verify the build works:

```bash
mkdir -p scripts/cantonal
cat > scripts/cantonal/zh-kv.json << 'TESTEOF'
{
  "canton": "ZH",
  "law_key": "zh-kv",
  "sr_number": "101",
  "language": "de",
  "title": "Verfassung des Kantons Zürich",
  "lexfind_id": 21736,
  "fetched_at": "2026-04-13",
  "article_count": 2,
  "articles": [
    { "number": 1, "suffix": "", "raw": "1", "title": "Kanton Zürich" },
    { "number": 2, "suffix": "", "raw": "2", "title": "Rechtsstaatliche Grundsätze" }
  ],
  "article_texts": {
    "1": [
      { "num": "1", "text": "Der Kanton Zürich ist ein souveräner Stand der Schweizerischen Eidgenossenschaft." },
      { "num": "2", "text": "Er gründet auf der Eigen- und Mitverantwortung seiner Einwohnerinnen und Einwohner." }
    ],
    "2": [
      { "num": "1", "text": "Grundlage und Schranke staatlichen Handelns ist das Recht." }
    ]
  }
}
TESTEOF
```

```bash
cd site && npm run build
```

Expected: Build succeeds. Pages generated for `/de/zh-kv/`, `/de/zh-kv/art-1`, etc.

- [ ] **Step 6: Remove test file and commit**

Remove the test JSON (it will be generated properly in Task 5):

```bash
rm scripts/cantonal/zh-kv.json
```

```bash
git add site/src/pages/[lang]/[law]/index.astro site/src/pages/[lang]/[law]/[article].astro
git commit -m "feat(site): dynamic getStaticPaths — include cantonal laws from JSON files"
```

---

### Task 5: Fetcher script — download 26 KVs from opencaselaw

**Files:**
- Create: `scripts/fetch_cantonal_laws.py`
- Create: `tests/test_fetch_cantonal_laws.py`

This script calls the opencaselaw API to fetch cantonal law texts. Since the opencaselaw tools are MCP-based and not a standard Python library, the fetcher will use the opencaselaw REST API directly (the same API backing the MCP tools) or call the `get_legislation` endpoint.

However, looking at the existing codebase, the project already uses opencaselaw via MCP tools in the agent pipeline. The simplest approach: write a script that uses `httpx` to call the LexFind PDF download + parse endpoint that `get_legislation` wraps, OR write a script that the human runs interactively with Claude (using the MCP tools directly).

**Practical approach:** Write a Python script that:
1. For each canton, calls the opencaselaw.ch API to search for the constitution
2. Downloads and parses the full text
3. Saves the per-law JSON

The opencaselaw MCP server's `get_legislation` tool downloads PDFs from LexFind and parses them with PyMuPDF. We can replicate this logic or call the API endpoint directly.

**Simplest path:** Since we have MCP access right now, fetch all 26 KVs interactively in this session and save the JSON files. Then write a refresh script for future updates.

- [ ] **Step 1: Create the fetcher script structure**

```python
# scripts/fetch_cantonal_laws.py
"""Fetch cantonal law texts from opencaselaw and save as per-law JSON."""

import json
import sys
from datetime import date
from pathlib import Path

CANTONAL_DIR = Path(__file__).parent / "cantonal"

# Canton → constitution search config
# language: the publication language for the canton
# query: search term to find the constitution
CANTON_KV_CONFIG = {
    "ZH": {"language": "de", "query": "Verfassung des Kantons Zürich"},
    "BE": {"language": "de", "query": "Verfassung des Kantons Bern"},
    "LU": {"language": "de", "query": "Verfassung des Kantons Luzern"},
    "UR": {"language": "de", "query": "Verfassung des Kantons Uri"},
    "SZ": {"language": "de", "query": "Verfassung des Kantons Schwyz"},
    "OW": {"language": "de", "query": "Verfassung des Kantons Obwalden"},
    "NW": {"language": "de", "query": "Verfassung des Kantons Nidwalden"},
    "GL": {"language": "de", "query": "Verfassung des Kantons Glarus"},
    "ZG": {"language": "de", "query": "Verfassung des Kantons Zug"},
    "FR": {"language": "fr", "query": "Constitution du canton de Fribourg"},
    "SO": {"language": "de", "query": "Verfassung des Kantons Solothurn"},
    "BS": {"language": "de", "query": "Verfassung des Kantons Basel-Stadt"},
    "BL": {"language": "de", "query": "Verfassung des Kantons Basel-Landschaft"},
    "SH": {"language": "de", "query": "Verfassung des Kantons Schaffhausen"},
    "AR": {"language": "de", "query": "Verfassung des Kantons Appenzell Ausserrhoden"},
    "AI": {"language": "de", "query": "Verfassung des Kantons Appenzell Innerrhoden"},
    "SG": {"language": "de", "query": "Verfassung des Kantons St. Gallen"},
    "GR": {"language": "de", "query": "Verfassung des Kantons Graubünden"},
    "AG": {"language": "de", "query": "Verfassung des Kantons Aargau"},
    "TG": {"language": "de", "query": "Verfassung des Kantons Thurgau"},
    "TI": {"language": "it", "query": "Costituzione della Repubblica e Cantone Ticino"},
    "VD": {"language": "fr", "query": "Constitution du Canton de Vaud"},
    "VS": {"language": "de", "query": "Verfassung des Kantons Wallis"},
    "NE": {"language": "fr", "query": "Constitution de la République et Canton de Neuchâtel"},
    "GE": {"language": "fr", "query": "Constitution de la République et canton de Genève"},
    "JU": {"language": "fr", "query": "Constitution de la République et Canton du Jura"},
}


def save_cantonal_law(
    canton: str,
    title: str,
    sr_number: str,
    lexfind_id: int,
    language: str,
    articles: list[dict],
    article_texts: dict[str, list[dict]],
) -> Path:
    """Save a cantonal law to its JSON file."""
    CANTONAL_DIR.mkdir(parents=True, exist_ok=True)
    slug = f"{canton.lower()}-kv"
    data = {
        "canton": canton,
        "law_key": slug,
        "sr_number": sr_number,
        "language": language,
        "title": title,
        "lexfind_id": lexfind_id,
        "fetched_at": date.today().isoformat(),
        "article_count": len(articles),
        "articles": articles,
        "article_texts": article_texts,
    }
    out_path = CANTONAL_DIR / f"{slug}.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_path


def parse_legislation_response(canton: str, response: dict) -> tuple[list[dict], dict[str, list[dict]]]:
    """Parse a get_legislation API response into articles list and article_texts dict.

    The response contains an 'articles' list where each entry has:
    - article_num: str (e.g. "1", "2a", "10bis")
    - heading: str (article title/marginal note)
    - text: str (full article text)

    We parse the text into paragraph structures matching ArticleTextParagraph.
    """
    articles_list = []
    article_texts = {}

    for art in response.get("articles", []):
        art_num_raw = art.get("article_num", "")
        heading = art.get("heading", "")
        text = art.get("text", "")

        # Parse article number: separate numeric part from suffix
        import re
        match = re.match(r"^(\d+)([a-z]*)$", art_num_raw)
        if not match:
            continue
        num = int(match.group(1))
        suffix = match.group(2)

        articles_list.append({
            "number": num,
            "suffix": suffix,
            "raw": art_num_raw,
            "title": heading,
        })

        # Parse text into paragraphs
        # Cantonal texts from LexFind PDFs come as continuous text with
        # numbered paragraphs like "1 Text..." and lettered items "a. text"
        paragraphs = parse_article_text(text)
        article_texts[art_num_raw] = paragraphs

    return articles_list, article_texts


def parse_article_text(text: str) -> list[dict]:
    """Parse article text into paragraph structures.

    Handles numbered paragraphs (1, 2, 3...) and lettered list items (a., b., c...).
    Returns list of ArticleTextParagraph-shaped dicts.
    """
    import re

    if not text.strip():
        return []

    lines = text.strip().split("\n")
    paragraphs = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for numbered paragraph: starts with digit(s) followed by space
        num_match = re.match(r"^(\d+)\s+(.+)$", line)
        if num_match:
            paragraphs.append({"num": num_match.group(1), "text": num_match.group(2)})
            continue

        # Otherwise treat as unnumbered paragraph
        if paragraphs and paragraphs[-1].get("text"):
            # If the last paragraph has text and this line doesn't start with a number,
            # it might be a continuation. But for simplicity, treat as new paragraph.
            paragraphs.append({"num": None, "text": line})
        else:
            paragraphs.append({"num": None, "text": line})

    # If we got no numbered paragraphs, return the whole text as one paragraph
    if not paragraphs:
        paragraphs = [{"num": None, "text": text.strip()}]

    return paragraphs


if __name__ == "__main__":
    # This script is designed to be run interactively with Claude (MCP tools)
    # or extended with direct API calls.
    # Usage: python -m scripts.fetch_cantonal_laws --canton ZH
    import argparse

    parser = argparse.ArgumentParser(description="Fetch cantonal laws from opencaselaw")
    parser.add_argument("--canton", help="Two-letter canton code (e.g., ZH). Omit for all.")
    parser.add_argument("--list", action="store_true", help="List available cantons")
    args = parser.parse_args()

    if args.list:
        for code, cfg in CANTON_KV_CONFIG.items():
            print(f"{code}: {cfg['query']} ({cfg['language']})")
        sys.exit(0)

    cantons = [args.canton.upper()] if args.canton else list(CANTON_KV_CONFIG.keys())
    print(f"Cantons to fetch: {', '.join(cantons)}")
    print("Use the MCP tools (search_legislation + get_legislation) to fetch each canton's KV,")
    print("then call save_cantonal_law() with the results.")
```

- [ ] **Step 2: Write test for `parse_article_text` and `save_cantonal_law`**

```python
# tests/test_fetch_cantonal_laws.py
"""Tests for cantonal law fetcher."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from scripts.fetch_cantonal_laws import parse_article_text, save_cantonal_law, parse_legislation_response


def test_parse_article_text_numbered_paragraphs():
    text = "1 Der Kanton Zürich ist ein souveräner Stand.\n2 Er gründet auf der Eigenverantwortung."
    result = parse_article_text(text)
    assert len(result) == 2
    assert result[0] == {"num": "1", "text": "Der Kanton Zürich ist ein souveräner Stand."}
    assert result[1] == {"num": "2", "text": "Er gründet auf der Eigenverantwortung."}


def test_parse_article_text_single_unnumbered():
    text = "Die Landessprachen sind Deutsch, Französisch, Italienisch und Rätoromanisch."
    result = parse_article_text(text)
    assert len(result) == 1
    assert result[0] == {"num": None, "text": text}


def test_parse_article_text_empty():
    assert parse_article_text("") == []
    assert parse_article_text("  ") == []


def test_save_cantonal_law(tmp_path):
    with patch("scripts.fetch_cantonal_laws.CANTONAL_DIR", tmp_path):
        path = save_cantonal_law(
            canton="ZH",
            title="Verfassung des Kantons Zürich",
            sr_number="101",
            lexfind_id=21736,
            language="de",
            articles=[{"number": 1, "suffix": "", "raw": "1", "title": "Kanton Zürich"}],
            article_texts={"1": [{"num": "1", "text": "Test text"}]},
        )
        assert path.name == "zh-kv.json"
        data = json.loads(path.read_text())
        assert data["canton"] == "ZH"
        assert data["law_key"] == "zh-kv"
        assert data["article_count"] == 1
        assert data["article_texts"]["1"][0]["text"] == "Test text"


def test_parse_legislation_response():
    response = {
        "articles": [
            {"article_num": "1", "heading": "Kanton Zürich", "text": "1 Souveräner Stand.\n2 Eigenverantwortung."},
            {"article_num": "2", "heading": "Grundsätze", "text": "Grundlage ist das Recht."},
        ]
    }
    articles, texts = parse_legislation_response("ZH", response)
    assert len(articles) == 2
    assert articles[0]["number"] == 1
    assert articles[0]["title"] == "Kanton Zürich"
    assert len(texts["1"]) == 2
    assert texts["2"][0]["num"] is None
```

- [ ] **Step 3: Run tests**

```bash
uv run pytest tests/test_fetch_cantonal_laws.py -v
```

Expected: All 5 tests pass.

- [ ] **Step 4: Commit**

```bash
git add scripts/fetch_cantonal_laws.py tests/test_fetch_cantonal_laws.py
git commit -m "feat: add cantonal law fetcher script with article text parser"
```

---

### Task 6: Fetch all 26 KVs via opencaselaw MCP tools

**Files:**
- Create: `scripts/cantonal/*.json` (26 files)

This task is done interactively with Claude using the MCP tools. For each canton:

1. Call `search_legislation(query="Verfassung", canton="XX", fetch_top_n_texts=1)` to find the LexFind ID
2. Call `get_legislation(lexfind_id=N)` to get the full article list with text
3. Save via `save_cantonal_law()`

- [ ] **Step 1: Fetch German-speaking cantons (20 cantons)**

For each of ZH, BE, LU, UR, SZ, OW, NW, GL, ZG, SO, BS, BL, SH, AR, AI, SG, GR, AG, TG, VS:

```
search_legislation(query="Verfassung des Kantons {Name}", canton="{CODE}", language="de", fetch_top_n_texts=1)
```

Then `get_legislation(lexfind_id=N, language="de")` and save the result.

- [ ] **Step 2: Fetch French-speaking cantons (5 cantons)**

For FR, VD, NE, GE, JU:

```
search_legislation(query="Constitution", canton="{CODE}", language="fr", fetch_top_n_texts=1)
```

Then `get_legislation(lexfind_id=N, language="fr")` and save.

- [ ] **Step 3: Fetch TI (Italian)**

```
search_legislation(query="Costituzione", canton="TI", language="it", fetch_top_n_texts=1)
```

Then `get_legislation(lexfind_id=N, language="it")` and save.

- [ ] **Step 4: Verify all 26 files exist and have articles**

```bash
ls scripts/cantonal/*.json | wc -l  # Should be 26
for f in scripts/cantonal/*.json; do
  count=$(python3 -c "import json; d=json.load(open('$f')); print(d['article_count'])")
  echo "$(basename $f): $count articles"
done
```

- [ ] **Step 5: Update `laws.ts` KV titles from fetched data**

Update each KV entry's `name` field to match the actual title from the fetched JSON (in case the expansion plan had slightly different titles).

- [ ] **Step 6: Commit**

```bash
git add scripts/cantonal/
git commit -m "data: fetch 26 Kantonsverfassungen from opencaselaw API"
```

---

### Task 7: Homepage cantonal section

**Files:**
- Modify: `site/src/pages/[lang]/index.astro`
- Modify: `site/src/lib/i18n.ts`

- [ ] **Step 1: Add translation keys**

In `site/src/lib/i18n.ts`, add:

```ts
'home.cantons_heading': { de: 'Kantonsverfassungen', fr: 'Constitutions cantonales', it: 'Costituzioni cantonali', en: 'Cantonal Constitutions' },
'home.cantons_subtitle': { de: '26 Kantone', fr: '26 cantons', it: '26 cantoni', en: '26 cantons' },
```

- [ ] **Step 2: Add cantonal section to homepage**

In `site/src/pages/[lang]/index.astro`, add imports and a new section after the federal laws grid:

Add to the frontmatter:
```ts
import { CANTONS } from '../../lib/cantons';
import { CANTONAL_LAWS } from '../../lib/laws';
```

Add after the `</section>` closing the `laws-section`:

```astro
<!-- Cantonal constitutions -->
{CANTONAL_LAWS.length > 0 && (
  <section class="cantons-section">
    <div class="label">{t('home.cantons_heading', lang)}</div>
    <p class="cantons-subtitle">{t('home.cantons_subtitle', lang)}</p>
    <div class="cantons-grid">
      {CANTONS.map((canton) => {
        const kvLaw = CANTONAL_LAWS.find(l => l.canton === canton.code);
        if (!kvLaw) return null;
        const stats = getLawStats(kvLaw.slug);
        return (
          <a href={`${langBase(lang)}/${kvLaw.slug}/`} class="canton-cell">
            <span class="canton-code">{canton.code}</span>
            <span class="canton-name">{canton.name[lang]}</span>
            <span class="canton-articles">{stats.totalArticles} Art.</span>
          </a>
        );
      })}
    </div>
  </section>
)}
```

- [ ] **Step 3: Add styles for cantonal section**

Add to the `<style>` block:

```css
.cantons-section {
  padding: var(--space-5) 0;
  border-top: 1px solid var(--color-rule);
}

.cantons-section > .label {
  margin-bottom: var(--space-1);
}

.cantons-subtitle {
  font-size: 12px;
  color: var(--color-text-muted);
  margin: 0 0 var(--space-3);
}

.cantons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 1px;
  background: var(--color-rule-light);
  border: 1px solid var(--color-rule-light);
}

.canton-cell {
  display: flex;
  flex-direction: column;
  padding: var(--space-2);
  background: var(--color-bg);
  text-decoration: none;
  color: var(--color-text);
  transition: background var(--transition-fast);
}

.canton-cell:hover {
  background: var(--color-rule-light);
}

.canton-code {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.canton-name {
  font-size: 11px;
  color: var(--color-text-secondary);
  margin-top: 2px;
}

.canton-articles {
  font-size: 10px;
  color: var(--color-text-muted);
  margin-top: 2px;
}
```

- [ ] **Step 4: Build and verify**

```bash
cd site && npm run build
```

Expected: Build succeeds. Homepage has a cantonal section with 26 canton tiles.

- [ ] **Step 5: Start dev server and verify in browser**

```bash
cd site && npm run dev
```

Check:
- Homepage at `/de/` shows cantonal section
- Clicking a canton leads to the KV article list
- Clicking an article shows the Gesetzestext
- Navigation between articles works
- French cantons show French text at `/fr/ge-kv/art-1`

- [ ] **Step 6: Commit**

```bash
git add site/src/pages/[lang]/index.astro site/src/lib/i18n.ts
git commit -m "feat(site): add cantonal constitutions section to homepage — 26 cantons"
```

---

### Task 8: Final verification and cleanup

- [ ] **Step 1: Run full test suite**

```bash
uv run pytest
```

Expected: All 189+ tests pass (plus the new cantonal tests).

- [ ] **Step 2: Run linter**

```bash
uv run ruff check .
```

Expected: No errors.

- [ ] **Step 3: Full site build**

```bash
cd site && npm run build
```

Expected: Build succeeds. Page count increased by ~26 (law index pages) + ~3200 (article pages) × 4 languages.

- [ ] **Step 4: Spot-check pages**

Preview built site:
```bash
cd site && npm run preview
```

Check:
- `/de/zh-kv/` — ZH KV article list, 147 articles
- `/de/zh-kv/art-1` — Gesetzestext displays, no commentary tabs
- `/fr/ge-kv/` — GE constitution in French
- `/it/ti-kv/` — TI constitution in Italian
- `/en/zh-kv/art-1` — Shows German text (original language) with fallback notice
- Article navigation (prev/next) works
- Homepage cantonal section renders correctly

- [ ] **Step 5: Final commit if any fixups needed**

```bash
git add -A
git commit -m "fix: cantonal KV display cleanup"
```
