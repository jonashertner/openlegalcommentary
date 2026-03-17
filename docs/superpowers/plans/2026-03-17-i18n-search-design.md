# i18n + Search + Visual Design Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add 4-language URL routing (DE/FR/IT/EN), Pagefind full-text search with command palette UI, and Swiss modernist visual elevation across the entire site.

**Architecture:** Three-phase implementation. Phase 1 restructures routes under `[lang]/`, creates an i18n module, and updates all components. Phase 2 replaces the JSON search with Pagefind and a command palette modal. Phase 3 refines typography, color, spacing, animations, and adds View Transitions. Each phase produces a working, buildable site.

**Tech Stack:** Astro 4 (static), TypeScript, Pagefind, CSS custom properties, View Transitions API

**Specs:**
- `docs/superpowers/specs/2026-03-17-site-wide-i18n-design.md`
- `docs/superpowers/specs/2026-03-17-search-and-visual-design.md`

---

## File Map

### New files
| File | Responsibility |
|------|---------------|
| `site/src/lib/i18n.ts` | All UI strings in 4 languages + `t()` helper + `Lang` type |
| `site/src/pages/index.astro` | Root redirect to `/de/` |
| `site/src/pages/[lang]/index.astro` | Translated home page |
| `site/src/pages/[lang]/about.astro` | Translated about page |
| `site/src/pages/[lang]/changelog.astro` | Translated changelog page |
| `site/src/pages/[lang]/[law]/index.astro` | Translated law TOC |
| `site/src/pages/[lang]/[law]/[article].astro` | Translated article page |
| `site/src/components/SearchModal.astro` | Pagefind command palette search |
| `scripts/fetch_article_texts_en.py` | Fetch English article texts from Fedlex |

### Modified files
| File | Changes |
|------|---------|
| `site/src/lib/base.ts` | Replace `BASE`/`HOME` with `langBase(lang)`/`langHome(lang)` |
| `site/src/lib/content.ts` | Add `lang` param to `loadArticle()`, remove `translations` field |
| `site/src/layouts/Base.astro` | Accept `lang` prop, set `<html lang>`, add `<meta name="current-lang">`, add `<link rel="alternate" hreflang>`, add `<link rel="canonical">` |
| `site/src/components/Header.astro` | Add `lang` prop, translate nav labels, add LanguageSwitcher + search trigger |
| `site/src/components/Footer.astro` | Add `lang` prop, translate section headings and links |
| `site/src/components/Breadcrumb.astro` | Add `lang` prop, translate "Home" label, use `langBase()` |
| `site/src/components/ArticleTabs.astro` | Add `lang` prop, translate tab labels, add sliding indicator |
| `site/src/components/ArticlePagination.astro` | Add `lang` prop, use `langBase()` |
| `site/src/components/LanguageSwitcher.astro` | Rewrite: `<a>` tags, accept `pagePath`, compute hrefs |
| `site/src/components/Gesetzestext.astro` | Add `lang` prop, load correct language text at build time |
| `site/src/styles/global.css` | Add tokens, refine typography/colors/spacing, add animations |
| `site/package.json` | Add pagefind, update build scripts |
| `site/astro.config.mjs` | Add View Transitions import |
| `agents/prompts.py` | Add `en` to translator prompt |
| `agents/translator.py` | Add `en` to supported languages |
| `agents/generation.py` | Add `en` to translation targets |
| `export/huggingface.py` | Add `summary_en`, `doctrine_en`, `caselaw_en` fields |

### Deleted files
| File | Reason |
|------|--------|
| `site/src/pages/about.astro` | Moved to `[lang]/about.astro` |
| `site/src/pages/changelog.astro` | Moved to `[lang]/changelog.astro` |
| `site/src/pages/[law]/index.astro` | Moved to `[lang]/[law]/index.astro` |
| `site/src/pages/[law]/[article].astro` | Moved to `[lang]/[law]/[article].astro` |
| `site/src/components/SearchBar.astro` | Replaced by `SearchModal.astro` |
| `scripts/generate_search_index.py` | Replaced by Pagefind |
| `site/public/search-index.json` | Replaced by Pagefind index |

---

## Phase 1: i18n Route Restructure

### Task 1: Create i18n module

**Files:**
- Create: `site/src/lib/i18n.ts`

- [ ] **Step 1: Create the i18n module with Lang type, LANGS constant, and t() function**

```typescript
// site/src/lib/i18n.ts
export const LANGS = ['de', 'fr', 'it', 'en'] as const;
export type Lang = (typeof LANGS)[number];

const translations: Record<string, Record<Lang, string>> = {
  // Nav
  'nav.laws': { de: 'Gesetze', fr: 'Lois', it: 'Leggi', en: 'Laws' },
  'nav.about': { de: 'Über uns', fr: 'À propos', it: 'Chi siamo', en: 'About' },
  'nav.changelog': { de: 'Änderungen', fr: 'Modifications', it: 'Modifiche', en: 'Changelog' },

  // Breadcrumb
  'breadcrumb.home': { de: 'Startseite', fr: 'Accueil', it: 'Home', en: 'Home' },

  // Article tabs
  'tab.summary': { de: 'Übersicht', fr: 'Aperçu', it: 'Panoramica', en: 'Overview' },
  'tab.doctrine': { de: 'Doktrin', fr: 'Doctrine', it: 'Dottrina', en: 'Doctrine' },
  'tab.caselaw': { de: 'Rechtsprechung', fr: 'Jurisprudence', it: 'Giurisprudenza', en: 'Case Law' },

  // Article page
  'article.in_force_since': { de: 'In Kraft seit', fr: 'En vigueur depuis', it: 'In vigore dal', en: 'In force since' },
  'article.toc': { de: 'Inhaltsverzeichnis', fr: 'Table des matières', it: 'Indice', en: 'Table of Contents' },
  'article.back_to_top': { de: 'Nach oben', fr: 'Haut de page', it: 'Torna su', en: 'Back to top' },

  // Pagination
  'pagination.prev': { de: 'Vorheriger Artikel', fr: 'Article précédent', it: 'Articolo precedente', en: 'Previous article' },
  'pagination.next': { de: 'Nächster Artikel', fr: 'Article suivant', it: 'Articolo successivo', en: 'Next article' },

  // Footer
  'footer.commentary': { de: 'Kommentar', fr: 'Commentaire', it: 'Commento', en: 'Commentary' },
  'footer.project': { de: 'Projekt', fr: 'Projet', it: 'Progetto', en: 'Project' },
  'footer.license': { de: 'Lizenz', fr: 'Licence', it: 'Licenza', en: 'License' },
  'footer.all_laws': { de: 'Alle Gesetze', fr: 'Toutes les lois', it: 'Tutte le leggi', en: 'All Laws' },
  'footer.about': { de: 'Über uns', fr: 'À propos', it: 'Chi siamo', en: 'About' },
  'footer.changes': { de: 'Änderungen', fr: 'Modifications', it: 'Modifiche', en: 'Changelog' },
  'footer.content_license': { de: 'Inhalte: CC BY-SA 4.0', fr: 'Contenu : CC BY-SA 4.0', it: 'Contenuti: CC BY-SA 4.0', en: 'Content: CC BY-SA 4.0' },
  'footer.code_license': { de: 'Code: MIT', fr: 'Code : MIT', it: 'Codice: MIT', en: 'Code: MIT' },
  'footer.tagline': {
    de: 'Offener, KI-generierter Kommentar zum Schweizer Bundesrecht.',
    fr: 'Commentaire ouvert généré par IA sur le droit fédéral suisse.',
    it: 'Commento aperto generato dall\'IA sul diritto federale svizzero.',
    en: 'Open, AI-generated commentary on Swiss federal law.',
  },

  // Home page
  'home.eyebrow': { de: 'Schweizer Bundesrecht', fr: 'Droit fédéral suisse', it: 'Diritto federale svizzero', en: 'Swiss Federal Law' },
  'home.title': { de: 'Open Legal Commentary', fr: 'Open Legal Commentary', it: 'Open Legal Commentary', en: 'Open Legal Commentary' },
  'home.subtitle': {
    de: 'Offener, KI-generierter, täglich aktualisierter Kommentar zum Schweizer Bundesrecht.',
    fr: 'Commentaire ouvert, généré par IA, mis à jour quotidiennement sur le droit fédéral suisse.',
    it: 'Commento aperto, generato dall\'IA, aggiornato quotidianamente sul diritto federale svizzero.',
    en: 'Open, AI-generated, daily-updated commentary on Swiss federal law.',
  },
  'home.stat.laws': { de: 'Gesetze', fr: 'Lois', it: 'Leggi', en: 'Laws' },
  'home.stat.articles': { de: 'Artikel', fr: 'Articles', it: 'Articoli', en: 'Articles' },
  'home.stat.languages': { de: 'Sprachen', fr: 'Langues', it: 'Lingue', en: 'Languages' },
  'home.stat.updated': { de: 'Täglich aktualisiert', fr: 'Mise à jour quotidienne', it: 'Aggiornamento quotidiano', en: 'Updated daily' },
  'home.laws_heading': { de: 'Kommentierte Gesetze', fr: 'Lois commentées', it: 'Leggi commentate', en: 'Annotated Laws' },
  'home.layers_heading': { de: 'Drei Ebenen der Analyse', fr: 'Trois niveaux d\'analyse', it: 'Tre livelli di analisi', en: 'Three Layers of Analysis' },
  'home.layer1.title': { de: 'Übersicht', fr: 'Aperçu', it: 'Panoramica', en: 'Overview' },
  'home.layer1.desc': {
    de: 'Verständliche Zusammenfassung auf B1-Niveau. Was regelt der Artikel? Wer ist betroffen?',
    fr: 'Résumé accessible au niveau B1. Que règle l\'article ? Qui est concerné ?',
    it: 'Riassunto comprensibile a livello B1. Cosa regola l\'articolo? Chi è interessato?',
    en: 'Accessible summary at B1 level. What does the article regulate? Who is affected?',
  },
  'home.layer2.title': { de: 'Doktrin', fr: 'Doctrine', it: 'Dottrina', en: 'Doctrine' },
  'home.layer2.desc': {
    de: 'Akademische Analyse mit Randziffern, Streitständen und Literaturverweisen.',
    fr: 'Analyse académique avec numéros marginaux, controverses et références bibliographiques.',
    it: 'Analisi accademica con numeri marginali, controversie e riferimenti bibliografici.',
    en: 'Academic analysis with marginal numbers, doctrinal debates, and literature references.',
  },
  'home.layer3.title': { de: 'Rechtsprechung', fr: 'Jurisprudence', it: 'Giurisprudenza', en: 'Case Law' },
  'home.layer3.desc': {
    de: 'Leitentscheide des Bundesgerichts, thematisch geordnet und täglich aktualisiert.',
    fr: 'Arrêts de principe du Tribunal fédéral, classés par thème et mis à jour quotidiennement.',
    it: 'Sentenze principali del Tribunale federale, ordinate per tema e aggiornate quotidianamente.',
    en: 'Leading Federal Supreme Court decisions, organized by topic and updated daily.',
  },
  'home.open_heading': { de: 'Offen und frei', fr: 'Ouvert et libre', it: 'Aperto e libero', en: 'Open and Free' },
  'home.open_desc': {
    de: 'Alle Inhalte stehen unter CC BY-SA 4.0. Der Code ist MIT-lizenziert. Beitragen auf GitHub.',
    fr: 'Tout le contenu est sous CC BY-SA 4.0. Le code est sous licence MIT. Contribuez sur GitHub.',
    it: 'Tutti i contenuti sono sotto CC BY-SA 4.0. Il codice è sotto licenza MIT. Contribuisci su GitHub.',
    en: 'All content is CC BY-SA 4.0. Code is MIT licensed. Contribute on GitHub.',
  },

  // Law page
  'law.progress': { de: 'Fortschritt', fr: 'Progression', it: 'Progresso', en: 'Progress' },
  'law.articles_with_commentary': { de: 'Artikel mit Kommentar', fr: 'Articles commentés', it: 'Articoli commentati', en: 'Articles with commentary' },

  // Search
  'search.placeholder': { de: 'Artikel, Zitate oder Rechtsbegriffe suchen...', fr: 'Rechercher des articles, citations ou concepts juridiques...', it: 'Cerca articoli, citazioni o concetti giuridici...', en: 'Search articles, citations, or legal concepts...' },
  'search.no_results': { de: 'Keine Ergebnisse', fr: 'Aucun résultat', it: 'Nessun risultato', en: 'No results' },
  'search.dev_unavailable': { de: 'Suche nach Build verfügbar', fr: 'Recherche disponible après build', it: 'Ricerca disponibile dopo build', en: 'Search available after build' },

  // Gesetzestext
  'gesetzestext.label': { de: 'Gesetzestext', fr: 'Texte de loi', it: 'Testo di legge', en: 'Statute Text' },

  // Changelog
  'changelog.title': { de: 'Änderungen', fr: 'Modifications', it: 'Modifiche', en: 'Changelog' },
  'changelog.empty': { de: 'Noch keine Änderungen vorhanden.', fr: 'Aucune modification pour le moment.', it: 'Nessuna modifica al momento.', en: 'No changes yet.' },

  // About
  'about.title': { de: 'Über Open Legal Commentary', fr: 'À propos d\'Open Legal Commentary', it: 'Informazioni su Open Legal Commentary', en: 'About Open Legal Commentary' },

  // Meta
  'meta.description': {
    de: 'Offener, KI-generierter Kommentar zum Schweizer Bundesrecht. Täglich aktualisiert.',
    fr: 'Commentaire ouvert généré par IA sur le droit fédéral suisse. Mis à jour quotidiennement.',
    it: 'Commento aperto generato dall\'IA sul diritto federale svizzero. Aggiornato quotidianamente.',
    en: 'Open, AI-generated commentary on Swiss federal law. Updated daily.',
  },

  // Header aria
  'header.nav_label': { de: 'Hauptnavigation', fr: 'Navigation principale', it: 'Navigazione principale', en: 'Main navigation' },
  'header.menu_open': { de: 'Menü öffnen', fr: 'Ouvrir le menu', it: 'Apri menu', en: 'Open menu' },
  'header.theme_toggle': { de: 'Farbschema wechseln', fr: 'Changer le thème', it: 'Cambia tema', en: 'Toggle theme' },
  'header.search': { de: 'Suche', fr: 'Recherche', it: 'Ricerca', en: 'Search' },

  // Language switcher
  'lang.label': { de: 'Sprache', fr: 'Langue', it: 'Lingua', en: 'Language' },
};

export function t(key: string, lang: Lang): string {
  const entry = translations[key];
  if (!entry) return key;
  return entry[lang] ?? entry['de'] ?? key;
}
```

- [ ] **Step 2: Verify the module compiles**

Run: `cd site && npx astro check 2>&1 | head -20`

- [ ] **Step 3: Commit**

```bash
git add site/src/lib/i18n.ts
git commit -m "feat(i18n): add i18n module with 4-language UI strings"
```

### Task 2: Replace base.ts with lang-aware URL helpers

**Files:**
- Modify: `site/src/lib/base.ts`

- [ ] **Step 1: Rewrite base.ts**

```typescript
// site/src/lib/base.ts
import type { Lang } from './i18n';

export const BASE = import.meta.env.BASE_URL?.replace(/\/$/, '') ?? '';

export function langBase(lang: Lang): string {
  return `${BASE}/${lang}`;
}

export function langHome(lang: Lang): string {
  return `${BASE}/${lang}/`;
}

// Keep HOME for the root redirect page
export const HOME = BASE || '/';
```

- [ ] **Step 2: Commit**

```bash
git add site/src/lib/base.ts
git commit -m "feat(i18n): add langBase/langHome URL helpers"
```

### Task 3: Update Base layout for i18n

**Files:**
- Modify: `site/src/layouts/Base.astro`

- [ ] **Step 1: Add lang prop, html lang attribute, meta tags, hreflang links**

Update the layout to:
- Accept `lang` prop (default `'de'`)
- Set `<html lang={lang}>`
- Add `<meta name="current-lang" content={lang}>`
- Add `<link rel="alternate" hreflang>` for all 4 languages
- Add `<link rel="canonical">` pointing to DE version
- Pass `lang` to Header and Footer

The `currentPath` prop becomes `pagePath` — the path without the lang prefix (e.g., `/bv/art-5`).

- [ ] **Step 2: Verify the layout renders**

Run: `cd site && npx astro check 2>&1 | head -20`

- [ ] **Step 3: Commit**

```bash
git add site/src/layouts/Base.astro
git commit -m "feat(i18n): update Base layout with lang prop and hreflang tags"
```

### Task 4: Update LanguageSwitcher to use `<a>` tags

**Files:**
- Modify: `site/src/components/LanguageSwitcher.astro`

- [ ] **Step 1: Rewrite component**

Replace the button-based switcher with `<a>` tag links:
- Accept `currentLang: Lang` and `pagePath: string` props
- Always show all 4 languages (DE/FR/IT/EN)
- Compute href as `langBase(targetLang) + pagePath`
- Current language gets `aria-current="true"` and active styling
- Add client-side script to append `window.location.search` to each link's href on page load (for `?layer=` preservation)

- [ ] **Step 2: Commit**

```bash
git add site/src/components/LanguageSwitcher.astro
git commit -m "feat(i18n): rewrite LanguageSwitcher as <a> tag navigation"
```

### Task 5: Update Header with lang prop, LanguageSwitcher, and search trigger

**Files:**
- Modify: `site/src/components/Header.astro`

- [ ] **Step 1: Update component**

- Accept `lang: Lang` and `pagePath: string` props
- Translate nav labels using `t('nav.laws', lang)` etc.
- Translate aria labels
- Add LanguageSwitcher next to theme toggle
- Add search trigger button (magnifying glass + `⌘K` badge) — for now just the button, search modal comes in Phase 2
- Use `langHome(lang)` for the logo link
- Use `langBase(lang)` for nav links

- [ ] **Step 2: Commit**

```bash
git add site/src/components/Header.astro
git commit -m "feat(i18n): translate Header nav and add LanguageSwitcher"
```

### Task 6: Update Footer with lang prop

**Files:**
- Modify: `site/src/components/Footer.astro`

- [ ] **Step 1: Update component**

- Accept `lang: Lang` prop
- Translate section headings, link labels, tagline using `t()` calls
- Use `langHome(lang)` for internal links

- [ ] **Step 2: Commit**

```bash
git add site/src/components/Footer.astro
git commit -m "feat(i18n): translate Footer"
```

### Task 7: Update Breadcrumb with lang prop

**Files:**
- Modify: `site/src/components/Breadcrumb.astro`

- [ ] **Step 1: Update component**

- Accept `lang: Lang` prop
- Translate "Home" label using `t('breadcrumb.home', lang)`
- Use `langHome(lang)` for home link
- Use `langBase(lang)` for intermediate breadcrumb links

- [ ] **Step 2: Commit**

```bash
git add site/src/components/Breadcrumb.astro
git commit -m "feat(i18n): translate Breadcrumb"
```

### Task 8: Update ArticleTabs with lang prop

**Files:**
- Modify: `site/src/components/ArticleTabs.astro`

- [ ] **Step 1: Update component**

- Accept `lang: Lang` prop
- Translate tab labels using `t('tab.summary', lang)` etc.
- Translate TOC toggle label
- Keep existing client-side tab switching and IntersectionObserver logic

- [ ] **Step 2: Commit**

```bash
git add site/src/components/ArticleTabs.astro
git commit -m "feat(i18n): translate ArticleTabs labels"
```

### Task 9: Update ArticlePagination with lang prop

**Files:**
- Modify: `site/src/components/ArticlePagination.astro`

- [ ] **Step 1: Update component**

- Accept `lang: Lang` prop
- Translate "Vorheriger/Nächster Artikel" using `t()` calls
- Use `langBase(lang)` for prev/next links

- [ ] **Step 2: Commit**

```bash
git add site/src/components/ArticlePagination.astro
git commit -m "feat(i18n): translate ArticlePagination"
```

### Task 10: Update Gesetzestext for build-time lang loading

**Files:**
- Modify: `site/src/components/Gesetzestext.astro`

- [ ] **Step 1: Update component**

- Accept `lang: Lang` prop
- Load the correct `article_texts_{lang}.json` at build time (no runtime switching)
- Translate the "Gesetzestext" label using `t('gesetzestext.label', lang)`
- Update Fedlex link to use the correct language URL
- Remove all `lang-change` event listener code
- Remove the `<script id="gesetzestext-i18n">` JSON embedding

- [ ] **Step 2: Commit**

```bash
git add site/src/components/Gesetzestext.astro
git commit -m "feat(i18n): load Gesetzestext at build time per language"
```

### Task 11: Update content.ts for per-language loading

**Files:**
- Modify: `site/src/lib/content.ts`

- [ ] **Step 1: Update loadArticle to accept lang parameter**

- `loadArticle(law, dirName, lang)` — for `de`, load `summary.md`; for others, load `summary.{lang}.md`
- If the language-specific file is empty or missing, fall back to the German file
- Remove the `translations` field from `ArticleContent` interface
- Remove the translation loading loop from `loadArticle()`
- Update `getArticleTextI18n()`: add `'en'` to the language loop `['de', 'fr', 'it', 'en']`
- Update `getArticleText()` to accept optional `lang` param (default `'de'`) for single-language loading
- Keep `loadArticleMeta()`, `listArticleDirs()`, `listArticles()`, `getLawStats()`, `getArticleNav()` unchanged (they don't need lang)

- [ ] **Step 2: Commit**

```bash
git add site/src/lib/content.ts
git commit -m "feat(i18n): add lang parameter to loadArticle with fallback"
```

### Task 12: Create route pages under [lang]/

**Files:**
- Create: `site/src/pages/[lang]/index.astro` (from current `index.astro`)
- Create: `site/src/pages/[lang]/about.astro` (from current `about.astro`)
- Create: `site/src/pages/[lang]/changelog.astro` (from current `changelog.astro`)
- Create: `site/src/pages/[lang]/[law]/index.astro` (from current `[law]/index.astro`)
- Create: `site/src/pages/[lang]/[law]/[article].astro` (from current `[law]/[article].astro`)
- Modify: `site/src/pages/index.astro` (replace with redirect)

- [ ] **Step 1: Create `site/src/pages/[lang]/` directory structure**

```bash
mkdir -p site/src/pages/\[lang\]/\[law\]
```

- [ ] **Step 2: Move and update index.astro (home page)**

Copy `site/src/pages/index.astro` to `site/src/pages/[lang]/index.astro`. Update:
- Add `getStaticPaths()` returning `LANGS.map(lang => ({ params: { lang } }))`
- Extract `lang` from `Astro.params`
- Replace all hardcoded German text with `t()` calls
- Pass `lang` and `pagePath="/"` to `Base` layout and all components
- Update all internal links to use `langBase(lang)` prefix
- Update stats: languages count = `LANGS.length`

- [ ] **Step 3: Replace root index.astro with redirect**

```astro
---
// site/src/pages/index.astro
return Astro.redirect('/de/');
---
```

- [ ] **Step 4: Move and update about.astro**

Copy to `[lang]/about.astro`. Add `getStaticPaths()`, translate all UI text with `t()`, pass `lang` prop to components.

- [ ] **Step 5: Move and update changelog.astro**

Copy to `[lang]/changelog.astro`. Add `getStaticPaths()`, translate labels with `t()`, pass `lang` to components. Update article links to include `langBase(lang)` prefix.

- [ ] **Step 6: Move and update [law]/index.astro**

Copy to `[lang]/[law]/index.astro`. Update `getStaticPaths()` to iterate over both `LANGS` and laws. Translate UI text. Update all article links to use `langBase(lang)`.

- [ ] **Step 7: Move and update [law]/[article].astro**

Copy to `[lang]/[law]/[article].astro`. Update `getStaticPaths()` to iterate over `LANGS`, laws, and articles. Call `loadArticle(law, dirName, lang)` for the correct language content. Translate all inline labels. Remove the `lang-change` event listener and translation data embedding. Pass `lang` to all components.

- [ ] **Step 8: Delete old page files**

```bash
rm site/src/pages/about.astro
rm site/src/pages/changelog.astro
rm -rf site/src/pages/\[law\]
```

- [ ] **Step 9: Build and verify**

Run: `cd site && npm run build 2>&1 | tail -20`

Expected: Build succeeds, generates pages under `dist/de/`, `dist/fr/`, `dist/it/`, `dist/en/`.

- [ ] **Step 10: Spot-check generated pages**

```bash
ls site/dist/de/ site/dist/en/ site/dist/fr/ site/dist/it/
cat site/dist/en/index.html | head -10  # should have <html lang="en">
```

- [ ] **Step 11: Commit**

```bash
git add site/src/pages/
git commit -m "feat(i18n): restructure routes under [lang]/ with 4-language static generation"
```

### Task 13: Agent pipeline — add English translation support

**Files:**
- Modify: `agents/prompts.py`
- Modify: `agents/translator.py`
- Modify: `agents/generation.py`

- [ ] **Step 1: Add English to translator prompt**

In `agents/prompts.py`, update `build_translator_prompt()`:
- Add `"en": ("English", "english")` to `lang_config` dict

- [ ] **Step 2: Add English to valid languages in translator.py**

In `agents/translator.py`, update `VALID_LANGUAGES` (or equivalent validation):
- Change from `("fr", "it")` to `("fr", "it", "en")`

- [ ] **Step 3: Add English to translation targets**

In `agents/generation.py`, find where `translate_layer()` is called for `"fr"` and `"it"` — add `"en"`.

- [ ] **Step 4: Run existing tests**

Run: `uv run pytest tests/test_prompts.py tests/test_translator.py -v`
Expected: All pass (or update tests for new `en` support)

- [ ] **Step 5: Commit**

```bash
git add agents/prompts.py agents/translator.py agents/generation.py
git commit -m "feat(i18n): add English translation support to agent pipeline"
```

### Task 14: Export pipeline — add English fields

**Files:**
- Modify: `export/huggingface.py`

- [ ] **Step 1: Add English content fields**

In `export_article()`, add:
```python
"summary_en": read_if_exists(art_dir / "summary.en.md"),
"doctrine_en": read_if_exists(art_dir / "doctrine.en.md"),
"caselaw_en": read_if_exists(art_dir / "caselaw.en.md"),
```

Update the dataset card schema table to include the English fields.

- [ ] **Step 2: Run lint**

Run: `uv run ruff check export/huggingface.py`

- [ ] **Step 3: Commit**

```bash
git add export/huggingface.py
git commit -m "feat(i18n): add English fields to HuggingFace export"
```

### Task 15a: Create English article texts fetch script

**Files:**
- Create: `scripts/fetch_article_texts_en.py`

- [ ] **Step 1: Create the script**

Model after `scripts/fetch_article_texts_i18n.py` but for English only. Fetch from Fedlex where official English translations exist (BV has one). For laws without English Fedlex text, create an empty entry so `getArticleText(law, article, 'en')` falls back to German gracefully.

- [ ] **Step 2: Run the script**

```bash
uv run python scripts/fetch_article_texts_en.py
```

Expected: creates `scripts/article_texts_en.json`

- [ ] **Step 3: Commit**

```bash
git add scripts/fetch_article_texts_en.py scripts/article_texts_en.json
git commit -m "feat(i18n): add English article text fetching from Fedlex"
```

---

## Phase 2: Pagefind Search

### Task 15: Atomic search swap — install Pagefind, create SearchModal, delete old search

This task is atomic to avoid a broken intermediate state where neither old nor new search works.

**Files:**
- Create: `site/src/components/SearchModal.astro`
- Delete: `site/src/components/SearchBar.astro`
- Delete: `scripts/generate_search_index.py`
- Delete: `site/public/search-index.json`
- Modify: `site/package.json`
- Modify: `site/src/pages/[lang]/[law]/[article].astro`
- Modify: `site/src/components/Header.astro`
- Modify: `site/src/layouts/Base.astro`

- [ ] **Step 1: Install Pagefind**

```bash
cd site && npm install -D pagefind@^1.3.0
```

- [ ] **Step 2: Update package.json scripts**

Remove the `"prebuild"` line. Add:
```json
"postbuild": "pagefind --site dist"
```

Note: always use `npm run build`, not `astro build` directly, to ensure postbuild runs.

- [ ] **Step 3: Add Pagefind data attributes to article pages**

On the article content wrapper element in `[lang]/[law]/[article].astro`, add:
```html
<article
  data-pagefind-body
  data-pagefind-filter="language:{lang}"
  data-pagefind-meta="law:{law}, article:{articleNumber}"
>
```

- [ ] **Step 4: Add `data-pagefind-ignore` to Base layout chrome**

In `Base.astro`, add `data-pagefind-ignore` to the `<header>` and `<footer>` wrappers so non-article pages (index, about, changelog) don't pollute the search index with nav/footer text.

- [ ] **Step 5: Create SearchModal.astro**

Build the command palette search modal:
- Frosted glass overlay (`backdrop-filter: blur(20px)`)
- Centered modal (max-width 640px) with large input field
- Magnifying glass icon + keyboard shortcut badge
- Scrollable results list
- Each result: law badge, article number, title, content snippet with highlights
- Empty state hint text (translated via `t('search.placeholder', lang)`)
- Full mobile variant (full-screen takeover)
- "Search all languages" toggle that removes the language filter from queries

Client-side script:
- Listen for `astro:page-load` to initialize (View Transitions compatible)
- Open on cmd+K / ctrl+K or search button click
- Close on Escape or click outside
- Arrow key navigation through results
- Debounced Pagefind search (150ms)
- Read `document.documentElement.lang` for language filter: pass `{ filters: { language: currentLang } }` to `pagefind.search()`
- Dynamic import of `/pagefind/pagefind.js` with graceful fallback for dev mode (show `t('search.dev_unavailable', lang)`)
- Accept `lang: Lang` prop for translated text

- [ ] **Step 6: Update Header to use SearchModal**

Replace the SearchBar import with SearchModal import in Header.astro. The search trigger button in the header opens the modal.

- [ ] **Step 7: Delete old search infrastructure**

```bash
rm site/src/components/SearchBar.astro
rm scripts/generate_search_index.py
rm -f site/public/search-index.json
```

- [ ] **Step 8: Build and verify**

```bash
cd site && npm run build 2>&1 | tail -10
ls site/dist/pagefind/
```

Expected: Build succeeds. `pagefind/` directory with index files.

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "feat(search): atomic swap to Pagefind with command palette SearchModal"
```

---

## Phase 3: Visual Design Elevation

### Task 16: CSS token additions and typography refinements

**Files:**
- Modify: `site/src/styles/global.css`

- [ ] **Step 1: Add new tokens and refine existing ones**

Add to `:root`:
```css
--space-16: 12rem;
--gradient-accent: linear-gradient(135deg, #DC2626, #B91C1C);
--color-hover-tint: color-mix(in srgb, var(--color-accent) 4%, var(--color-bg));
--color-glass: color-mix(in srgb, var(--color-bg-elevated) 80%, transparent);
--max-width: 1280px; /* was 1200px */
```

Refine typography:
```css
/* Tighter tracking for display text */
.text-display { letter-spacing: -0.03em; }

/* Better prose spacing */
.prose p { margin-bottom: 1.5em; }
.prose { line-height: 1.75; } /* was 1.7 */
```

Add dark mode glass override:
```css
[data-theme='dark'] {
  --color-glass: color-mix(in srgb, var(--color-bg-elevated) 65%, transparent);
}
```

- [ ] **Step 2: Add top accent line**

```css
body::before {
  content: '';
  display: block;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--gradient-accent);
  z-index: 200;
}
```

- [ ] **Step 3: Add skip-to-content link**

In `Base.astro`:
```html
<a href="#main-content" class="skip-link">Skip to content</a>
```

```css
.skip-link {
  position: absolute;
  top: -100%;
  left: var(--space-2);
  padding: var(--space-1) var(--space-2);
  background: var(--color-accent);
  color: white;
  z-index: 300;
  border-radius: var(--radius-md);
}
.skip-link:focus { top: var(--space-2); }
```

- [ ] **Step 4: Commit**

```bash
git add site/src/styles/global.css site/src/layouts/Base.astro
git commit -m "feat(design): add CSS tokens, accent line, typography refinements"
```

### Task 17: Home page visual elevation

**Files:**
- Modify: `site/src/pages/[lang]/index.astro`

- [ ] **Step 1: Refine hero section**

- Use `--space-16` for hero vertical padding
- Use Instrument Serif for stat values (numbers)
- Tighter letter-spacing on hero title (`-0.03em`)
- Accent line becomes gradient
- Update languages stat to `LANGS.length` (4)

- [ ] **Step 2: Laws grid to 3 columns**

```css
.laws-grid { grid-template-columns: repeat(3, 1fr); }
@media (max-width: 1024px) { .laws-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 640px) { .laws-grid { grid-template-columns: 1fr; } }
```

Add hover accent border on cards.

- [ ] **Step 3: Commit**

```bash
git add site/src/pages/[lang]/index.astro
git commit -m "feat(design): elevate home page — hero, grid, typography"
```

### Task 18: Article page visual refinements

**Files:**
- Modify: `site/src/pages/[lang]/[law]/[article].astro`
- Modify: `site/src/components/ArticleTabs.astro`

- [ ] **Step 1: Refine reading progress bar**

Change from 3px to 2px height, use `var(--gradient-accent)` for the fill.

- [ ] **Step 2: Add sliding tab indicator**

In `ArticleTabs.astro`, add a `::after` pseudo-element on the tab bar. Client-side JS measures active tab's `offsetLeft` and `width`, then animates the indicator via `transform: translateX()` and `width`. Listen on `astro:page-load` for initialization.

- [ ] **Step 3: Elevate Gesetzestext panel**

Add `box-shadow: var(--shadow-sm)` and `background: var(--color-bg-elevated)` to the Gesetzestext wrapper.

- [ ] **Step 4: Commit**

```bash
git add site/src/pages/[lang]/[law]/[article].astro site/src/components/ArticleTabs.astro
git commit -m "feat(design): article page — progress bar, sliding tabs, Gesetzestext elevation"
```

### Task 19: Law index page refinements

**Files:**
- Modify: `site/src/pages/[lang]/[law]/index.astro`

- [ ] **Step 1: Refine progress bar and article list**

- Thinner progress bar (3px) with gradient accent fill
- Structural headings get subtle left accent border
- Article list items: hover translateX(4px) + accent left border reveal

- [ ] **Step 2: Commit**

```bash
git add site/src/pages/[lang]/[law]/index.astro
git commit -m "feat(design): law index — progress bar, structural headings, hover effects"
```

### Task 20: Responsive refinements

**Files:**
- Modify: `site/src/styles/global.css`
- Modify: various components

- [ ] **Step 1: Ensure all touch targets are minimum 44px**

Audit and fix: search trigger, language switcher links, theme toggle, nav links, tab buttons.

- [ ] **Step 2: Gesetzestext collapsible on mobile**

Wrap Gesetzestext in a `<details>` element on mobile (< 640px):
```css
@media (max-width: 640px) {
  .gesetzestext-wrapper { /* collapsible styles */ }
}
```

- [ ] **Step 3: Article tabs horizontally scrollable on mobile**

```css
@media (max-width: 640px) {
  .tabs { overflow-x: auto; -webkit-overflow-scrolling: touch; flex-wrap: nowrap; }
}
```

- [ ] **Step 4: Commit**

```bash
git add site/src/styles/global.css site/src/components/
git commit -m "feat(design): responsive refinements — touch targets, mobile collapsibles"
```

### Task 21: Micro-interactions and View Transitions

**Files:**
- Modify: `site/src/layouts/Base.astro`
- Modify: `site/astro.config.mjs`
- Modify: `site/src/styles/global.css`

- [ ] **Step 1: Enable View Transitions**

In `Base.astro`, add:
```astro
---
import { ViewTransitions } from 'astro:transitions';
---
<head>
  <ViewTransitions />
</head>
```

- [ ] **Step 2: Update all client-side scripts to use `astro:page-load`**

Replace `DOMContentLoaded` listeners with `astro:page-load` in:
- Header.astro (theme toggle, nav toggle)
- ArticleTabs.astro (tab init, TOC tracking)
- SearchModal.astro (keyboard shortcuts, Pagefind init)
- [article].astro (reading progress, back-to-top)

- [ ] **Step 3: Add hover effects to cards**

```css
.law-card {
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
}
.law-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}
```

- [ ] **Step 4: Add scroll-triggered fade-in**

```css
.fade-in-on-scroll {
  opacity: 0;
  transform: translateY(16px);
  transition: opacity 0.5s var(--ease-out), transform 0.5s var(--ease-out);
}
.fade-in-on-scroll.visible {
  opacity: 1;
  transform: translateY(0);
}
```

Add IntersectionObserver script in `Base.astro` to toggle `.visible` class. Respect `prefers-reduced-motion`.

- [ ] **Step 5: Sticky header shadow on scroll**

```javascript
document.addEventListener('astro:page-load', () => {
  const header = document.querySelector('.site-header');
  if (!header) return;
  const observer = new IntersectionObserver(
    ([e]) => header.classList.toggle('scrolled', !e.isIntersecting),
    { threshold: [1] }
  );
  const sentinel = document.createElement('div');
  sentinel.style.height = '1px';
  document.body.prepend(sentinel);
  observer.observe(sentinel);
});
```

```css
.site-header.scrolled { box-shadow: var(--shadow-sm); }
```

- [ ] **Step 6: Commit**

```bash
git add site/src/layouts/Base.astro site/astro.config.mjs site/src/styles/global.css site/src/components/
git commit -m "feat(design): View Transitions, micro-interactions, scroll effects"
```

### Task 22: Final build verification

- [ ] **Step 1: Full build**

```bash
cd site && npm run build 2>&1 | tail -30
```

Expected: Build succeeds. Pages generated for all 4 languages. Pagefind index created.

- [ ] **Step 2: Preview and spot-check**

```bash
cd site && npm run preview &
```

Check:
- `/` redirects to `/de/`
- `/de/` shows German home page
- `/en/` shows English home page
- `/de/bv/art-1` shows German article
- Language switcher links work across all pages
- Search modal opens with cmd+K
- Search returns results with highlighted snippets
- Dark mode works
- Mobile responsive (resize browser)

- [ ] **Step 3: Run Python tests**

```bash
uv run pytest -q
uv run ruff check .
```

Expected: All pass.

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat: complete i18n + Pagefind search + visual design elevation"
```

---

## Update CLAUDE.md

### Task 23: Update project documentation

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update CLAUDE.md**

Update the commands section:
- Change `cd site && npm run build` note: "Always use `npm run build`, not `astro build` directly (postbuild runs Pagefind)"
- Add: `cd site && npm run build` includes Pagefind index generation
- Note the 4-language URL structure under project structure

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for i18n and Pagefind"
```
