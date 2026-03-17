# Site-wide i18n with URL-based routing

**Date:** 2026-03-17
**Status:** Approved

## Goal

Add full 4-language support (DE, FR, IT, EN) across the entire site with URL-based routing. Every page is statically generated in all 4 languages. No runtime language switching.

## URL Structure

```
/              → redirect to /de/
/de/           → German home
/fr/           → French home
/it/           → Italian home
/en/           → English home
/de/bv/art-5   → German article
/en/bv/art-5   → English article
/fr/about      → French about
/it/changelog   → Italian changelog
```

Old URLs (`/bv/art-5`, `/about`) are not preserved. No redirects.

## Languages

| Code | Label | Content source |
|------|-------|----------------|
| `de` | DE | `summary.md`, `doctrine.md`, `caselaw.md` (authoritative) |
| `fr` | FR | `summary.fr.md`, `doctrine.fr.md`, `caselaw.fr.md` |
| `it` | IT | `summary.it.md`, `doctrine.it.md`, `caselaw.it.md` |
| `en` | EN | `summary.en.md`, `doctrine.en.md`, `caselaw.en.md` (new) |

## Architecture

### 1. Route restructure

Move all pages under `src/pages/[lang]/`:

```
src/pages/
├── index.astro                → redirect to /de/
└── [lang]/
    ├── index.astro            → home page
    ├── about.astro            → about page
    ├── changelog.astro        → changelog page
    └── [law]/
        ├── index.astro        → law TOC
        └── [article].astro    → article page
```

Each page exports `getStaticPaths()` returning paths for `['de', 'fr', 'it', 'en']`. The `lang` param is threaded through all components.

### 2. i18n module — `src/lib/i18n.ts`

Single file containing all UI strings in 4 languages. Keyed access via helper function:

```typescript
export const LANGS = ['de', 'fr', 'it', 'en'] as const;
export type Lang = typeof LANGS[number];

export function t(key: string, lang: Lang): string;
```

Covers:
- Nav labels (Gesetze/Lois/Leggi/Laws, etc.)
- Page titles and headings
- Footer text
- Button labels, tab labels
- Section headings on index/about/changelog
- Meta descriptions for SEO

### 3. LanguageSwitcher in Header

- Always visible in the header, next to the theme toggle
- Renders as `<a>` tags (not buttons), linking to the same page path in other languages
- Current language highlighted
- Accepts `currentLang` and `currentPath` props to compute hrefs
- Example: on `/de/bv/art-5`, the EN link points to `/en/bv/art-5`

### 4. Content loading updates — `src/lib/content.ts`

- `loadArticle(law, dirName, lang)` — for `de`, loads `summary.md`; for others, loads `summary.{lang}.md`
- Remove the `translations` field from `ArticleContent` — each page load gets exactly one language
- Remove the runtime innerHTML switching script from `[article].astro`
- Remove the `<script id="translation-data">` JSON embedding pattern

### 5. Gesetzestext

- Load `article_texts.json` (de), `article_texts_fr.json` (fr), `article_texts_it.json` (it), `article_texts_en.json` (en)
- English texts fetched from Fedlex where available (BV has official English translation)
- If no English text exists for a law, show German text with a note: "Official English text not available. Showing German original."
- Remove runtime switching from Gesetzestext component

### 6. Agent pipeline — English translation

- Add `"en"` to supported languages in `translator.py`
- Update `build_translator_prompt()` to handle `en` target language
- Translation generates `.en.md` files alongside `.fr.md` and `.it.md`
- Pipeline processes: generate DE → evaluate → translate FR, IT, EN

### 7. Components receiving `lang` prop

All components that render translatable text receive a `lang: Lang` prop:

- `Header.astro` — nav labels, aria labels
- `Footer.astro` — section headings, links, attribution
- `LanguageSwitcher.astro` — current language, path computation
- `Gesetzestext.astro` — load correct language text
- `ArticleTabs.astro` — tab labels
- `Base.astro` (layout) — `<html lang={lang}>`, meta description, page title

### 8. Search

- `search-index.json` remains language-agnostic (article numbers and titles)
- Search result links include the current language prefix: `/${lang}/${law}/${slug}`
- Article titles in search index remain German (the canonical form)

### 9. Sitemap / SEO

- Each language version is a distinct static page
- `<html lang={lang}>` set correctly per page
- `<link rel="alternate" hreflang="...">` tags added to `<head>` pointing to all 4 language versions

## What does NOT change

- Content directory structure (`content/{law}/art-{NNN}/`)
- File naming convention (`.fr.md`, `.it.md`, `.en.md`)
- `meta.yaml` schema
- Python agent pipeline structure (only translator gains `en` support)
- Export pipeline (adds `summary_en`, `doctrine_en`, `caselaw_en` fields)
- Build tooling (Astro, no new dependencies)

## Build impact

- ~4x number of static pages
- No new runtime JS (language switching is now pure navigation)
- Removes existing language-switching JS (net reduction in client-side code)
