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

Old URLs (`/bv/art-5`, `/about`) are not preserved. No redirects. The site is new and not yet indexed or widely linked.

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

**Note:** Do NOT enable Astro's built-in `i18n` config (`defaultLocale`/`locales`) — this is a manual `[lang]` route. Enabling the Astro adapter would create routing conflicts.

### 2. URL helper — replace `BASE` with `langBase(lang)`

The current `src/lib/base.ts` exports `BASE` (empty string) and `HOME`. Replace with:

```typescript
export function langBase(lang: Lang): string {
  return `/${lang}`;
}
export function langHome(lang: Lang): string {
  return `/${lang}/`;
}
```

All components currently using `BASE` must be updated:
- `Header.astro` — nav links
- `Footer.astro` — footer links
- `Breadcrumb.astro` — home link, law link
- `ArticlePagination.astro` — prev/next links
- `SearchBar.astro` — result links (see section 8)
- `[law]/index.astro` — article TOC links
- `[article].astro` — internal links

### 3. i18n module — `src/lib/i18n.ts`

Single file containing all UI strings in 4 languages. Keyed access via helper function:

```typescript
export const LANGS = ['de', 'fr', 'it', 'en'] as const;
export type Lang = typeof LANGS[number];

export function t(key: string, lang: Lang): string;
```

Covers:
- Nav labels (Gesetze/Lois/Leggi/Laws)
- Page titles and headings
- Footer text (section headings, attribution)
- Button labels, tab labels (Übersicht/Doktrin/Rechtsprechung)
- Section headings on index/about/changelog
- Meta descriptions for SEO
- Inline labels: "In Kraft seit" / "En vigueur depuis" / "In vigore dal" / "In force since"
- Breadcrumb: "Home" label
- Aria labels
- Homepage stat label "Sprachen" → "4" (driven from `LANGS.length`)

### 4. LanguageSwitcher in Header

- Always visible in the header, next to the theme toggle
- Renders as `<a>` tags (not buttons), linking to the same page path in other languages
- Current language highlighted
- Accepts `currentLang` and `pagePath` props (path without the lang prefix, e.g., `/bv/art-5`)
- Href computation: `/${targetLang}${pagePath}` — simple concatenation, no regex substitution
- Preserves query parameters (e.g., `?layer=doctrine`) by reading them at build time and appending
- Remove the old `LanguageSwitcher` usage inside `[article].astro` body

### 5. Content loading updates — `src/lib/content.ts`

- `loadArticle(law, dirName, lang)` — for `de`, loads `summary.md`; for others, loads `summary.{lang}.md`
- **Fallback behavior:** if the requested language file is missing, fall back to the German file. This is expected during rollout when not all articles have all translations yet. No placeholder message needed — the German content is valid.
- Remove the `translations` field from `ArticleContent` — each page load gets exactly one language
- Remove the runtime innerHTML switching script from `[article].astro`
- Remove the `<script id="translation-data">` JSON embedding pattern

### 6. Gesetzestext

- Load `article_texts.json` (de), `article_texts_fr.json` (fr), `article_texts_it.json` (it), `article_texts_en.json` (en)
- English texts: create `scripts/fetch_article_texts_en.py` to fetch from Fedlex where available (BV has official English). Run alongside existing `fetch_article_texts_i18n.py`.
- If no English text exists for an article, fall back to German text (same fallback as content)
- Remove runtime switching from Gesetzestext component — it receives `lang` prop and loads the correct file at build time

### 7. Agent pipeline — English translation

- Add `"en"` to supported languages in `translator.py`
- Update `build_translator_prompt()` to handle `en` target language
- Translation generates `.en.md` files alongside `.fr.md` and `.it.md`
- Pipeline processes: generate DE → evaluate → translate FR, IT, EN

### 8. Components receiving `lang` prop

All components that render translatable text receive a `lang: Lang` prop:

- `Header.astro` — nav labels, aria labels
- `Footer.astro` — section headings, links, attribution
- `Breadcrumb.astro` — "Home" label, aria-label
- `LanguageSwitcher.astro` — current language, path computation
- `Gesetzestext.astro` — load correct language text
- `ArticleTabs.astro` — tab labels
- `ArticlePagination.astro` — prev/next labels
- `SearchBar.astro` — placeholder text
- `Base.astro` (layout) — `<html lang={lang}>`, meta description, page title

### 9. Search

- `search-index.json` remains language-agnostic (article numbers and titles)
- Search result links include the current language prefix: `/${lang}/${law}/${slug}`
- Inject `lang` into client-side JS via `<meta name="current-lang" content={lang}>` in `Base.astro`, read by SearchBar's click handler
- Article titles in search index remain German (the canonical form)

### 10. Sitemap / SEO

- Each language version is a distinct static page
- `<html lang={lang}>` set correctly per page
- `<link rel="alternate" hreflang="...">` tags added to `<head>` pointing to all 4 language versions
- `<link rel="canonical">` pointing to the DE version (authoritative source)

### 11. Export pipeline update

Add English fields to the HuggingFace export:
- `summary_en`, `doctrine_en`, `caselaw_en` added to each JSONL record
- Update `export/huggingface.py` to read `.en.md` files
- Update dataset card schema table

## What does NOT change

- Content directory structure (`content/{law}/art-{NNN}/`)
- File naming convention (`.fr.md`, `.it.md`, `.en.md`)
- `meta.yaml` schema
- Python agent pipeline structure (only translator gains `en` support)
- Build tooling (Astro, no new dependencies)

## Build impact

- ~4x number of static pages
- No new runtime JS (language switching is now pure navigation)
- Removes existing language-switching JS (net reduction in client-side code)
