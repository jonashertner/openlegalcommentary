# Swiss International Style Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign openlegalcommentary.ch in purist Swiss International Typographic Style — Helvetica + Source Serif 4, black/white, asymmetric grid, rules as structure, zero decoration.

**Architecture:** Rewrite global.css (new color/type/spacing variables, strip all decorative styles), then update each component and page to use the new system. The asymmetric 2-column grid (200px metadata + fluid content) is the core layout pattern applied to every content page.

**Tech Stack:** Astro, plain CSS (scoped styles), Source Serif 4 (Google Fonts)

**Spec:** `docs/superpowers/specs/2026-04-06-swiss-redesign-design.md`

---

## File Structure

| File | Responsibility | Change |
|------|----------------|--------|
| `site/src/styles/global.css` | Design system: variables, base styles, prose, responsive | **Rewrite** |
| `site/src/layouts/Base.astro` | Root HTML, font loading, theme script | **Modify** |
| `site/src/components/Header.astro` | Sticky header with nav | **Rewrite** |
| `site/src/components/Footer.astro` | Minimal footer | **Rewrite** |
| `site/src/components/ArticleTabs.astro` | Tab navigation for article layers | **Modify styles** |
| `site/src/components/Gesetzestext.astro` | Statute text display | **Modify styles** |
| `site/src/components/SearchModal.astro` | Search overlay | **Modify styles** |
| `site/src/components/Breadcrumb.astro` | Breadcrumb navigation | **Simplify** |
| `site/src/components/ArticlePagination.astro` | Prev/next article links | **Simplify** |
| `site/src/components/LawCard.astro` | **Delete** — replaced by grid cells in home page |
| `site/src/components/CrossReferences.astro` | **Delete** — metadata moves to left column |
| `site/src/pages/[lang]/index.astro` | Home page | **Rewrite** |
| `site/src/pages/[lang]/[law]/index.astro` | Law index (table of contents) | **Modify** |
| `site/src/pages/[lang]/[law]/[article].astro` | Article detail page | **Modify** |
| `site/src/pages/[lang]/concepts/index.astro` | Concepts list | **Modify** |
| `site/src/pages/[lang]/concepts/[slug].astro` | Concept detail | **Modify** |
| `site/src/pages/[lang]/contested/index.astro` | Contested questions list | **Modify** |
| `site/src/pages/[lang]/contested/[slug].astro` | Contested detail | **Modify** |
| `site/src/lib/markdown.ts` | Randziffer + BGE citation styling | **Modify** |

---

## Chunk 1: Design Foundation (Tasks 1–2)

Replace the entire CSS design system and update the root layout. After this chunk, the site will look broken (components still use old classes) but the new variables and base styles are in place.

### Task 1: Rewrite global.css — new design system

**Files:**
- Rewrite: `site/src/styles/global.css` (660 lines → ~350 lines)

This is the foundation. Every other task depends on these variables.

- [ ] **Step 1: Read the current global.css**

Read `site/src/styles/global.css` in full to understand all existing custom properties, styles, and animations that need to be replaced.

- [ ] **Step 2: Write the new global.css**

Replace the entire file with the new Swiss design system. Key changes:

**Font import** — replace 4-family Google Fonts import with single:
```css
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap');
```

**CSS variables** — replace all color, shadow, gradient, radius, animation variables:
```css
:root {
  /* Typography */
  --font-ui: Helvetica, Arial, sans-serif;
  --font-body: 'Source Serif 4', Georgia, serif;
  --font-mono: 'SFMono-Regular', Menlo, monospace;

  /* Colors — Light */
  --color-bg: #FFFFFF;
  --color-text: #000000;
  --color-text-secondary: #666666;
  --color-text-muted: #999999;
  --color-text-faint: #CCCCCC;
  --color-rule: #000000;
  --color-rule-light: #EEEEEE;
  --color-border: #E0E0E0;

  /* Spacing (8px baseline) */
  --space-1: 0.5rem;
  --space-2: 1rem;
  --space-3: 1.5rem;
  --space-4: 2rem;
  --space-5: 3rem;
  --space-6: 3rem;
  --space-8: 4rem;

  /* Layout */
  --max-width: 1280px;
  --content-width: 600px;
  --left-col: 200px;
  --page-pad: 48px;

  /* Transitions — functional only */
  --transition-fast: 150ms ease-out;
}

[data-theme='dark'] {
  --color-bg: #0A0A0A;
  --color-text: #E0E0E0;
  --color-text-secondary: #999999;
  --color-text-muted: #666666;
  --color-text-faint: #555555;
  --color-rule: #E0E0E0;
  --color-rule-light: #222222;
  --color-border: #333333;
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme='light']) {
    --color-bg: #0A0A0A;
    --color-text: #E0E0E0;
    --color-text-secondary: #999999;
    --color-text-muted: #666666;
    --color-text-faint: #555555;
    --color-rule: #E0E0E0;
    --color-rule-light: #222222;
    --color-border: #333333;
  }
}
```

**Base styles** — minimal resets and body:
```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: var(--font-ui);
  font-size: 14px;
  line-height: 1.5;
  color: var(--color-text);
  background: var(--color-bg);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  -webkit-font-smoothing: antialiased;
}
/* NO body::before (paper texture) */
/* NO body::after (accent line) */

main {
  flex: 1;
}

a {
  color: var(--color-text);
  text-decoration: underline;
  text-decoration-color: var(--color-border);
  text-underline-offset: 3px;
  transition: text-decoration-color var(--transition-fast);
}
a:hover {
  text-decoration-color: var(--color-text);
}
```

**Typography** — Helvetica for headings, no decorative font utilities:
```css
h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-ui);
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.02em;
}

.label {
  font-family: var(--font-ui);
  font-size: 10px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}
```

**Layout utilities**:
```css
.page-wrapper {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 var(--page-pad);
  width: 100%;
}

.page-grid {
  display: grid;
  grid-template-columns: var(--left-col) 1fr;
}

.left-col {
  border-right: 1px solid var(--color-rule-light);
  padding: var(--space-4) var(--space-3) var(--space-4) 0;
}

.right-col {
  padding: var(--space-4) 0 var(--space-4) var(--space-4);
}

.content-column {
  max-width: var(--content-width);
}
```

**Prose styles** — for rendered markdown content:
```css
.prose {
  font-family: var(--font-body);
  font-size: 14px;
  line-height: 1.85;
  max-width: var(--content-width);
}

[data-theme='dark'] .prose {
  color: #C8C8C8;
}

.prose p { margin-bottom: var(--space-2); }

.prose h2 {
  font-family: var(--font-ui);
  font-size: 16px;
  font-weight: 700;
  margin-top: var(--space-5);
  margin-bottom: var(--space-2);
  letter-spacing: -0.01em;
}

.prose h3 {
  font-family: var(--font-ui);
  font-size: 14px;
  font-weight: 700;
  margin-top: var(--space-4);
  margin-bottom: var(--space-2);
}

.prose a {
  color: var(--color-text);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.prose blockquote {
  border-left: 2px solid var(--color-border);
  padding-left: var(--space-2);
  margin: var(--space-2) 0;
  font-style: italic;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.prose .randziffer {
  font-family: var(--font-ui);
  font-weight: 700;
  font-size: 12px;
  color: var(--color-text);
  scroll-margin-top: 4rem;
}

.prose .randziffer:target {
  background: var(--color-rule-light);
  padding: 0.1em 0.35em;
  margin: 0 -0.35em;
}

.prose .cite-bge {
  font-weight: 600;
}

.prose .cite-cross {
  font-family: var(--font-ui);
  font-size: 12px;
  font-weight: 500;
  text-decoration: none;
  color: var(--color-text-secondary);
  border-bottom: 1px dashed var(--color-border);
}

.prose .cite-cross:hover {
  color: var(--color-text);
  border-bottom-color: var(--color-text);
}

.prose .heading-anchor {
  opacity: 0;
  text-decoration: none;
  color: var(--color-text-muted);
  margin-left: -1.25em;
  padding-right: 0.25em;
  font-size: 0.85em;
  transition: opacity var(--transition-fast);
}

.prose h2:hover .heading-anchor,
.prose h3:hover .heading-anchor {
  opacity: 0.5;
}

.prose code {
  font-family: var(--font-mono);
  font-size: 13px;
  background: var(--color-rule-light);
  padding: 0.15em 0.4em;
}
```

**Accessibility**:
```css
.skip-link {
  position: absolute;
  top: -100%;
  left: var(--space-2);
  padding: var(--space-1) var(--space-2);
  background: var(--color-text);
  color: var(--color-bg);
  z-index: 300;
}
.skip-link:focus { top: var(--space-2); }

:focus-visible {
  outline: 2px solid var(--color-text);
  outline-offset: 2px;
}

.sr-only {
  position: absolute;
  width: 1px; height: 1px;
  padding: 0; margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

::selection {
  background: var(--color-rule-light);
  color: var(--color-text);
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

**Responsive**:
```css
@media (max-width: 768px) {
  :root {
    --page-pad: 24px;
    --left-col: 100%;
  }

  .page-grid {
    grid-template-columns: 1fr;
  }

  .left-col {
    border-right: none;
    border-bottom: 1px solid var(--color-rule-light);
    padding: var(--space-3) 0;
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-3);
    align-items: baseline;
  }

  .right-col {
    padding: var(--space-3) 0;
  }
}
```

**Remove entirely**: All `--shadow-*` variables, all `--radius-*` variables (except `--radius-sm: 2px` for code), all `--gradient-*` variables, all `@keyframes` animations, all `.animate-*` classes, all `.delay-*` classes, all `.display-font`/`.display-italic` classes, all `.accent-line*` classes, `body::before`, `body::after`.

- [ ] **Step 3: Verify the build still works**

Run: `cd site && npm run build`
Expected: Build succeeds (pages may look unstyled but no errors)

- [ ] **Step 4: Commit**

```bash
git add site/src/styles/global.css
git commit -m "feat(site): rewrite CSS design system for Swiss International Style"
```

---

### Task 2: Update Base layout — font loading and theme

**Files:**
- Modify: `site/src/layouts/Base.astro` (97 lines)

- [ ] **Step 1: Read the current Base.astro**

Read `site/src/layouts/Base.astro` to understand the current structure.

- [ ] **Step 2: Update the layout**

Changes needed:
1. The font import is in global.css (already updated in Task 1), so no HTML font link changes needed
2. Remove any inline styles that reference old variables (paper texture, accent line)
3. Verify the theme script (lines 66-80) still works — it should, since it only sets `data-theme` attribute
4. Keep ViewTransitions, keep the theme inline script as-is

Only change if there are references to removed CSS classes or old variable names in the HTML/script. The theme restoration script should work unchanged since it just reads/writes localStorage and the `data-theme` attribute.

- [ ] **Step 3: Verify build**

Run: `cd site && npm run build`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
git add site/src/layouts/Base.astro
git commit -m "feat(site): update Base layout for Swiss redesign"
```

---

## Chunk 2: Core Components (Tasks 3–7)

Update Header, Footer, Tabs, Gesetzestext, Search. After this chunk, the structural components match the new style.

### Task 3: Rewrite Header component

**Files:**
- Rewrite: `site/src/components/Header.astro` (368 lines → ~250 lines)

- [ ] **Step 1: Read the current Header.astro**

Read the full file. Note the navigation items, language switcher, search trigger, mobile menu logic, and all imports.

- [ ] **Step 2: Rewrite the component**

Keep all the existing Astro frontmatter (imports, props, data fetching), navigation links, language switcher, search trigger functionality, and mobile menu JavaScript logic. Rewrite the HTML structure and scoped `<style>` block.

**New HTML structure:**

```html
<header class="site-header">
  <div class="header-inner page-wrapper">
    <a href={`/${lang}/`} class="site-name">openlegalcommentary</a>
    <nav class="nav-main">
      <!-- Keep existing nav items, remove icons -->
      <a href="..." class:list={[{active: ...}]}>Gesetze</a>
      <a href="..." class:list={[{active: ...}]}>Konzepte</a>
      <a href="..." class:list={[{active: ...}]}>Streitfragen</a>
    </nav>
    <div class="header-actions">
      <button class="search-trigger" id="search-trigger">
        <span>Suche</span>
        <kbd>⌘K</kbd>
      </button>
      <div class="lang-switcher">
        <!-- Keep existing language links -->
      </div>
      <button class="theme-toggle" id="theme-toggle" aria-label="Toggle theme">
        <!-- Simple sun/moon icon, keep existing logic -->
      </button>
      <button class="nav-toggle" aria-label="Menu">
        <span class="nav-toggle-bar"></span>
        <span class="nav-toggle-bar"></span>
        <span class="nav-toggle-bar"></span>
      </button>
    </div>
  </div>
</header>
```

**New styles:**

```css
.site-header {
  border-bottom: 1px solid var(--color-rule);
  background: var(--color-bg);
  position: sticky;
  top: 0;
  z-index: 100;
}
/* NO backdrop-filter, NO glassmorphism */

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
}

.site-name {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--color-text);
  text-decoration: none;
}
/* NO .logo-mark green square */

.nav-main {
  display: flex;
  gap: 16px;
  margin-left: 24px;
}

.nav-main a {
  font-size: 12px;
  font-weight: 400;
  color: var(--color-text-muted);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.nav-main a:hover,
.nav-main a.active {
  color: var(--color-text);
}

.nav-main a.active {
  font-weight: 500;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

.search-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: 1px solid var(--color-border);
  padding: 4px 10px;
  font-family: var(--font-ui);
  font-size: 11px;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: color var(--transition-fast), border-color var(--transition-fast);
}

.search-trigger:hover {
  color: var(--color-text);
  border-color: var(--color-text-muted);
}

.search-trigger kbd {
  font-family: var(--font-ui);
  font-size: 10px;
  border: 1px solid var(--color-border);
  padding: 1px 5px;
  color: var(--color-text-faint);
}

.lang-switcher {
  font-size: 12px;
  display: flex;
  gap: 6px;
}

.lang-switcher a {
  color: var(--color-text-faint);
  text-decoration: none;
}

.lang-switcher a:hover,
.lang-switcher a.active {
  color: var(--color-text);
}

.theme-toggle {
  background: none;
  border: 1px solid var(--color-border);
  padding: 4px;
  color: var(--color-text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: color var(--transition-fast);
}

.theme-toggle:hover {
  color: var(--color-text);
}
```

Keep the existing JavaScript for: mobile menu toggle, scroll detection (but remove shadow-on-scroll — no shadows), keyboard shortcut for search.

Remove the `.scrolled` shadow logic from the JS (or just remove the CSS rule — the JS can stay harmlessly).

- [ ] **Step 3: Verify build and check header renders**

Run: `cd site && npm run build && npm run preview`
Check: Header renders with text logo, nav, search trigger, lang switcher, theme toggle. No green square, no blur.

- [ ] **Step 4: Commit**

```bash
git add site/src/components/Header.astro
git commit -m "feat(site): rewrite Header for Swiss style — text logo, solid bg, no decoration"
```

---

### Task 4: Rewrite Footer component

**Files:**
- Rewrite: `site/src/components/Footer.astro` (244 lines → ~80 lines)

- [ ] **Step 1: Read current Footer.astro**

Note the theme toggle logic and any important links.

- [ ] **Step 2: Rewrite to minimal single-line footer**

```html
<footer class="site-footer">
  <div class="footer-inner page-wrapper">
    <div class="footer-left">
      Quelle: <a href="https://opencaselaw.ch">OpenCaseLaw.ch</a> ·
      Inhalt: CC0 · Code: MIT
    </div>
    <div class="footer-right">
      openlegalcommentary.ch
    </div>
  </div>
</footer>
```

```css
.site-footer {
  border-top: 1px solid var(--color-rule);
  padding: var(--space-3) 0;
  margin-top: auto;
  font-size: 11px;
  color: var(--color-text-muted);
}

.footer-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.site-footer a {
  color: var(--color-text-muted);
}

.site-footer a:hover {
  color: var(--color-text);
}

@media (max-width: 768px) {
  .footer-inner {
    flex-direction: column;
    gap: var(--space-1);
    text-align: center;
  }
}
```

Move the theme toggle to the Header (already handled in Task 3). Remove all footer link columns, logo mark, social links.

- [ ] **Step 3: Verify build**

Run: `cd site && npm run build`

- [ ] **Step 4: Commit**

```bash
git add site/src/components/Footer.astro
git commit -m "feat(site): rewrite Footer — single rule, one line, minimal"
```

---

### Task 5: Update ArticleTabs styles

**Files:**
- Modify: `site/src/components/ArticleTabs.astro` (406 lines)

- [ ] **Step 1: Read current ArticleTabs.astro**

Focus on the `<style>` block (starts around line 138). Note the tab-indicator animation, TOC styling.

- [ ] **Step 2: Replace the style block**

Keep all HTML structure and JavaScript logic. Replace the scoped `<style>` block:

**Tab navigation:**
```css
.tabs-nav {
  display: flex;
  gap: 0;
  margin-bottom: 0;
}

.tab-btn {
  font-family: var(--font-ui);
  font-size: 12px;
  font-weight: 400;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 10px 0;
  margin-right: 24px;
  color: var(--color-text-muted);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: color var(--transition-fast);
  min-height: 44px;
}

.tab-btn:hover { color: var(--color-text); }

.tab-btn.active {
  font-weight: 700;
  color: var(--color-text);
  border-bottom-color: var(--color-text);
}
```

Remove `.tab-indicator` animated sliding element (if present in HTML, hide it with `display: none` or remove the element).

**Tab panel:**
```css
.tab-panel { padding: var(--space-3) 0; }
.tab-panel.hidden { display: none; }
```

**TOC:**
```css
.toc {
  margin-bottom: var(--space-3);
  border: 1px solid var(--color-border);
  overflow: hidden;
}

.toc-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: var(--space-1) var(--space-2);
  font-family: var(--font-ui);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--color-text-secondary);
  cursor: pointer;
  min-height: 44px;
}

.toc-toggle::after {
  content: '';
  margin-left: auto;
  width: 0; height: 0;
  border-left: 4px solid transparent;
  border-right: 4px solid transparent;
  border-top: 5px solid var(--color-text-muted);
  transition: transform var(--transition-fast);
}

details[open] > .toc-toggle::after {
  transform: rotate(180deg);
}

.toc-icon { display: flex; align-items: center; color: var(--color-text-muted); }

.toc-list {
  list-style: none;
  padding: 0 var(--space-2) var(--space-2);
}

.toc-list li a {
  display: block;
  padding: 0.25rem 0.5rem;
  font-family: var(--font-ui);
  font-size: 11px;
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: color var(--transition-fast);
  line-height: 1.4;
}

.toc-list li a:hover { color: var(--color-text); }

.toc-list li.toc-active a {
  color: var(--color-text);
  font-weight: 600;
}

.toc-sub { padding-left: 1.25rem; }
.toc-sub a { font-size: 10px !important; }
```

No background fills on TOC. No border-radius. No accent colors.

- [ ] **Step 3: Verify build**

Run: `cd site && npm run build`

- [ ] **Step 4: Commit**

```bash
git add site/src/components/ArticleTabs.astro
git commit -m "feat(site): update ArticleTabs for Swiss style — uppercase tabs, no animation"
```

---

### Task 6: Update Gesetzestext styles

**Files:**
- Modify: `site/src/components/Gesetzestext.astro` (287 lines)

- [ ] **Step 1: Read current Gesetzestext.astro**

Note the HTML structure: header with icon + Fedlex link, body with paragraphs and lists.

- [ ] **Step 2: Replace the style block**

Keep HTML structure. Remove the icon from the header HTML (the `<svg>` in `.gesetzestext-icon`). Replace styles:

```css
.gesetzestext {
  border: 1px solid var(--color-border);
  margin-bottom: var(--space-4);
}
/* NO border-radius, NO background, NO shadow, NO animation */

.gesetzestext-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-1) var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

.gesetzestext-label {
  font-family: var(--font-ui);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  color: var(--color-text-muted);
}
/* Remove .gesetzestext-icon styling */

.gesetzestext-source {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--color-text-muted);
  text-decoration: none;
  padding: 2px 8px;
  border: 1px solid var(--color-border);
}

.gesetzestext-source:hover {
  color: var(--color-text);
  border-color: var(--color-text-muted);
}

.gesetzestext-body {
  padding: var(--space-3);
  font-family: var(--font-body);
  font-size: 13px;
  line-height: 1.8;
}

.gesetzestext-absatz {
  margin-bottom: 0.75rem;
  display: flex;
  align-items: baseline;
  gap: 0;
  padding: 0.25rem 0;
}

.absatz-num {
  flex-shrink: 0;
  font-family: var(--font-ui);
  font-weight: 700;
  font-size: 11px;
  color: var(--color-text-secondary);
  width: 1.75rem;
  min-width: 1.75rem;
  margin-right: 0.625rem;
}
/* NO colored background badge on numbers */

.absatz-text { flex: 1; }

.gesetzestext-list {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.25rem 0.75rem;
  margin: 0 0 0.75rem 2.375rem;
  padding: 0.375rem 0;
  border-left: 2px solid var(--color-border);
  padding-left: 0.75rem;
}

.gesetzestext-list dt {
  font-family: var(--font-ui);
  font-weight: 600;
  font-size: 11px;
  color: var(--color-text-secondary);
  min-width: 1.25rem;
}

.gesetzestext-list dd { margin: 0; line-height: 1.7; }
```

Also remove the `<svg>` icon element from the Gesetzestext header HTML. Keep just the text label "GESETZESTEXT" and the Fedlex link.

- [ ] **Step 3: Verify build**

Run: `cd site && npm run build`

- [ ] **Step 4: Commit**

```bash
git add site/src/components/Gesetzestext.astro
git commit -m "feat(site): update Gesetzestext for Swiss style — no icon, no radius, no fill"
```

---

### Task 7: Update SearchModal styles

**Files:**
- Modify: `site/src/components/SearchModal.astro` (358 lines)

- [ ] **Step 1: Read current SearchModal.astro**

Focus on the style block. Note the overlay blur, rounded corners, result styling.

- [ ] **Step 2: Update styles only**

Keep all HTML and JavaScript (Pagefind integration, keyboard navigation). Update scoped styles:

```css
.search-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: color-mix(in srgb, var(--color-bg) 85%, transparent);
  backdrop-filter: blur(4px); /* reduced, functional only */
  display: none;
  align-items: flex-start;
  justify-content: center;
  padding: 15vh var(--space-3) var(--space-4);
}

.search-overlay.open { display: flex; }

.search-modal {
  max-width: 640px;
  width: 100%;
  max-height: 70vh;
  background: var(--color-bg);
  border: 1px solid var(--color-rule);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
/* NO border-radius, NO shadow */

.search-input-wrapper {
  display: flex;
  align-items: center;
  padding: var(--space-2) var(--space-3);
  border-bottom: 1px solid var(--color-border);
  gap: var(--space-2);
}

.search-input {
  flex: 1;
  background: none;
  border: none;
  font-size: 16px;
  font-family: var(--font-ui);
  color: var(--color-text);
  outline: none;
}

.search-input::placeholder { color: var(--color-text-faint); }

.search-kbd {
  font-family: var(--font-ui);
  font-size: 10px;
  padding: 2px 6px;
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
}
```

Update result styles (these use `:global()` selectors — keep the selector pattern, change the values):

```css
:global(.search-result) {
  display: flex;
  align-items: start;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  cursor: pointer;
  text-decoration: none;
  color: var(--color-text);
  transition: background var(--transition-fast);
  min-height: 44px;
}

:global(.search-result:hover),
:global(.search-result.active) {
  background: var(--color-rule-light);
}

:global(.search-result-law) {
  font-family: var(--font-ui);
  font-size: 10px;
  font-weight: 700;
  color: var(--color-text-secondary);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  flex-shrink: 0;
}
/* NO colored background badge */

:global(.search-result-title) {
  font-family: var(--font-ui);
  font-weight: 600;
  font-size: 12px;
}

:global(.search-result-excerpt) {
  font-size: 11px;
  color: var(--color-text-muted);
  margin-top: 2px;
  line-height: 1.4;
}

:global(.search-result-excerpt mark) {
  background: none;
  color: var(--color-text);
  font-weight: 600;
  text-decoration: underline;
}

:global(.search-empty) {
  text-align: center;
  padding: var(--space-4);
  color: var(--color-text-muted);
  font-size: 12px;
}
```

- [ ] **Step 3: Verify build**

Run: `cd site && npm run build`

- [ ] **Step 4: Commit**

```bash
git add site/src/components/SearchModal.astro
git commit -m "feat(site): update SearchModal for Swiss style — no radius, no shadow"
```

---

## Chunk 3: Pages (Tasks 8–13)

Update all page templates. After this chunk, the full site matches the Swiss design.

### Task 8: Rewrite home page

**Files:**
- Rewrite: `site/src/pages/[lang]/index.astro` (729 lines → ~300 lines)
- Delete: `site/src/components/LawCard.astro` (243 lines)

- [ ] **Step 1: Read current home page and LawCard**

Read `site/src/pages/[lang]/index.astro` and `site/src/components/LawCard.astro`. Note the data loading in the frontmatter (law list, article counts, stats).

- [ ] **Step 2: Rewrite the page**

Keep the Astro frontmatter (imports, data loading, `getStaticPaths`). Rewrite the HTML template and scoped styles. Remove the LawCard import. Inline the law grid cells.

**New structure:**

```astro
<!-- Hero -->
<section class="hero">
  <div class="hero-grid">
    <div class="hero-content">
      <div class="label">{t('home.eyebrow', lang)}</div>
      <h1 class="hero-title">{t('home.title', lang)}</h1>
      <p class="hero-description">{t('home.description', lang)}</p>
    </div>
    <div class="hero-stats">
      <div class="stat">
        <div class="stat-value">{totalArticles.toLocaleString('de-CH')}</div>
        <div class="label">Artikel</div>
      </div>
      <div class="stat">
        <div class="stat-value">963K</div>
        <div class="label">Entscheide</div>
      </div>
      <div class="stat">
        <div class="stat-value">{laws.length}</div>
        <div class="label">Gesetze</div>
      </div>
      <div class="stat">
        <div class="stat-value">4</div>
        <div class="label">Sprachen</div>
      </div>
    </div>
  </div>
</section>

<!-- Laws grid -->
<section class="laws-section">
  <div class="label">Gesetze</div>
  <div class="laws-grid">
    {laws.map(law => (
      <a href={`/${lang}/${law.code.toLowerCase()}/`} class="law-cell">
        <div class="law-cell-top">
          <span class="law-abbr">{law.code}</span>
          <span class="law-count">{law.articleCount} Art.</span>
        </div>
        <div class="law-name">{law.name}</div>
        <div class="law-sr">SR {law.srNumber}</div>
      </a>
    ))}
  </div>
</section>
```

**New styles:**

```css
.hero {
  padding: var(--space-8) 0 var(--space-5);
  border-bottom: 1px solid var(--color-rule);
}

.hero-grid {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: var(--space-8);
  align-items: end;
}

.hero-title {
  font-size: 52px;
  font-weight: 700;
  letter-spacing: -0.035em;
  line-height: 1.05;
  margin-top: var(--space-3);
}

.hero-description {
  font-family: var(--font-body);
  font-size: 16px;
  line-height: 1.7;
  color: var(--color-text-secondary);
  max-width: 480px;
  margin-top: var(--space-4);
}

.hero-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
}

.stat {
  padding: 20px 0;
  border-top: 1px solid var(--color-rule);
}

.stat:nth-child(n+3) {
  border-top-color: var(--color-rule-light);
}

.stat-value {
  font-size: 42px;
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1;
}

.laws-section {
  padding: var(--space-5) 0;
}

.laws-section > .label {
  margin-bottom: var(--space-3);
}

.laws-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border-top: 1px solid var(--color-rule);
}

.law-cell {
  padding: var(--space-3) var(--space-2);
  border-bottom: 1px solid var(--color-rule-light);
  border-right: 1px solid var(--color-rule-light);
  text-decoration: none;
  color: var(--color-text);
  transition: background var(--transition-fast);
}

.law-cell:nth-child(3n) {
  border-right: none;
}

.law-cell:hover {
  background: var(--color-rule-light);
}

.law-cell-top {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.law-abbr {
  font-size: 24px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.law-count {
  font-size: 11px;
  color: var(--color-text-muted);
}

.law-name {
  font-size: 12px;
  color: var(--color-text-secondary);
  margin-top: 4px;
}

.law-sr {
  font-size: 10px;
  color: var(--color-text-faint);
  margin-top: 2px;
}

@media (max-width: 768px) {
  .hero-grid {
    grid-template-columns: 1fr;
    gap: var(--space-4);
  }
  .hero-title { font-size: 36px; }
  .hero-stats { max-width: 300px; }
  .laws-grid { grid-template-columns: 1fr 1fr; }
  .law-cell:nth-child(3n) { border-right: 1px solid var(--color-rule-light); }
  .law-cell:nth-child(2n) { border-right: none; }
}

@media (max-width: 480px) {
  .hero-title { font-size: 28px; }
  .laws-grid { grid-template-columns: 1fr; }
  .law-cell { border-right: none; }
}
```

Remove: Featured card section, "forthcoming" section, layers explanation section, open access banner. The home page is now just hero + law grid.

- [ ] **Step 3: Delete LawCard.astro**

```bash
rm site/src/components/LawCard.astro
```

- [ ] **Step 4: Verify build**

Run: `cd site && npm run build`
Expected: Build succeeds. Check that no other file imports LawCard — grep for it. If found, remove the import.

- [ ] **Step 5: Commit**

```bash
git add -A site/src/pages/[lang]/index.astro site/src/components/
git commit -m "feat(site): rewrite home page — hero + law grid, delete LawCard"
```

---

### Task 9: Update article detail page with asymmetric grid

**Files:**
- Modify: `site/src/pages/[lang]/[law]/[article].astro`
- Delete: `site/src/components/CrossReferences.astro`
- Simplify: `site/src/components/Breadcrumb.astro`
- Simplify: `site/src/components/ArticlePagination.astro`

- [ ] **Step 1: Read current article page, CrossReferences, Breadcrumb, ArticlePagination**

Read all four files. Note the data passed to each component, how cross-references are loaded, the breadcrumb structure.

- [ ] **Step 2: Update the article page to asymmetric grid layout**

Replace the current layout with the 2-column page-grid. Move cross-reference data into the left column directly (no separate component).

**New HTML structure** (keep existing frontmatter, data loading, schema markup):

```astro
<Breadcrumb items={breadcrumbItems} />

<div class="page-grid">
  <div class="left-col">
    <div class="label">Artikel</div>
    <div class="article-number">{article.meta.article}</div>
    <div class="article-title">{title}</div>

    <div class="meta-divider"></div>

    <div class="label">Gesetz</div>
    <div class="meta-value">{law.toUpperCase()}</div>
    <div class="meta-sub">SR {article.meta.sr_number}</div>

    {article.meta.layers?.caselaw?.last_generated && (
      <>
        <div class="meta-divider"></div>
        <div class="label">Aktualisiert</div>
        <div class="meta-value">{formatDate(article.meta.layers.caselaw.last_generated)}</div>
      </>
    )}

    {crossRefs.length > 0 && (
      <>
        <div class="meta-divider"></div>
        <div class="label">Querverweis</div>
        <div class="cross-refs">
          {crossRefs.map(ref => (
            <a href={refUrl(ref)}>→ {ref.title}</a>
          ))}
        </div>
      </>
    )}

    {article.meta.fedlex_url && (
      <>
        <div class="meta-divider"></div>
        <div class="label">Fedlex</div>
        <a href={article.meta.fedlex_url} class="meta-link">Originaltext →</a>
      </>
    )}
  </div>

  <div class="right-col">
    <Gesetzestext paragraphs={paragraphs} lang={lang} fedlexUrl={article.meta.fedlex_url} />
    <ArticleTabs ... />
    <ArticlePagination prev={prev} next={next} lang={lang} law={law} />
  </div>
</div>
```

**New scoped styles:**

```css
.article-number {
  font-size: 48px;
  font-weight: 700;
  letter-spacing: -0.04em;
  line-height: 1;
}

.article-title {
  font-size: 13px;
  margin-top: 8px;
  line-height: 1.4;
}

.meta-divider {
  height: 1px;
  background: var(--color-rule-light);
  margin: var(--space-3) 0;
}

.meta-value {
  font-size: 12px;
}

.meta-sub {
  font-size: 11px;
  color: var(--color-text-muted);
}

.meta-link {
  font-size: 11px;
  color: var(--color-text-secondary);
  text-decoration: underline;
}

.cross-refs {
  font-size: 12px;
  line-height: 1.8;
}

.cross-refs a {
  display: block;
  color: var(--color-text-secondary);
  text-decoration: none;
}

.cross-refs a:hover {
  color: var(--color-text);
}
```

Remove: reading progress bar, back-to-top button, CrossReferences component import. Keep: schema.org JSON-LD markup.

- [ ] **Step 3: Simplify Breadcrumb.astro**

Rewrite the style block to minimal:
```css
.breadcrumb {
  font-size: 11px;
  color: var(--color-text-muted);
  padding: 12px 0;
  border-bottom: 1px solid var(--color-rule-light);
}
.breadcrumb a {
  color: var(--color-text-muted);
  text-decoration: none;
}
.breadcrumb a:hover { color: var(--color-text); }
.breadcrumb .separator { margin: 0 6px; }
```

- [ ] **Step 4: Simplify ArticlePagination.astro**

Rewrite to minimal ruled pagination:
```css
.pagination {
  display: flex;
  justify-content: space-between;
  margin-top: var(--space-5);
  padding-top: var(--space-2);
  border-top: 1px solid var(--color-rule-light);
  font-size: 12px;
}
.pagination a {
  color: var(--color-text-muted);
  text-decoration: none;
}
.pagination a:hover { color: var(--color-text); }
```

- [ ] **Step 5: Delete CrossReferences.astro**

```bash
rm site/src/components/CrossReferences.astro
```

- [ ] **Step 6: Verify build**

Run: `cd site && npm run build`
Grep for any remaining imports of CrossReferences — remove if found.

- [ ] **Step 7: Commit**

```bash
git add -A site/src/
git commit -m "feat(site): article detail with asymmetric grid, inline cross-refs, simplified nav"
```

---

### Task 10: Update law index page

**Files:**
- Modify: `site/src/pages/[lang]/[law]/index.astro` (389 lines)

- [ ] **Step 1: Read current law index page**

Note the law header, progress bar, search button, structural headings for table of contents.

- [ ] **Step 2: Update to asymmetric grid**

Apply the page-grid layout. Left column: law abbreviation (large), title, SR number, article count. Right column: table of contents with structural headings.

Keep the existing data loading and table of contents logic. Update the HTML template and styles:

**Left column:**
```html
<div class="label">Gesetz</div>
<div class="law-abbr">{law.toUpperCase()}</div>
<div class="law-title">{lawName}</div>
<div class="meta-divider"></div>
<div class="label">SR</div>
<div class="meta-value">{srNumber}</div>
<div class="meta-divider"></div>
<div class="label">Artikel</div>
<div class="meta-value">{articleCount}</div>
```

**Right column:** Keep existing TOC structure but style with rules instead of cards:
```css
.toc-heading {
  font-family: var(--font-ui);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  padding: var(--space-2) 0 var(--space-1);
  border-bottom: 1px solid var(--color-rule-light);
  margin-top: var(--space-4);
}

.toc-heading:first-child {
  margin-top: 0;
}

.toc-article {
  display: flex;
  gap: var(--space-2);
  padding: 6px 0;
  border-bottom: 1px solid var(--color-rule-light);
  font-size: 12px;
  text-decoration: none;
  color: var(--color-text);
  transition: color var(--transition-fast);
}

.toc-article:hover {
  background: var(--color-rule-light);
}

.toc-article-num {
  font-weight: 700;
  min-width: 60px;
}

.toc-article-title {
  color: var(--color-text-secondary);
}
```

Remove: progress bar, search button within law page, colored badges.

- [ ] **Step 3: Verify build**

Run: `cd site && npm run build`

- [ ] **Step 4: Commit**

```bash
git add site/src/pages/[lang]/[law]/index.astro
git commit -m "feat(site): update law index with asymmetric grid, ruled TOC"
```

---

### Task 11: Update concept and contested pages

**Files:**
- Modify: `site/src/pages/[lang]/concepts/index.astro` (61 lines)
- Modify: `site/src/pages/[lang]/concepts/[slug].astro` (88 lines)
- Modify: `site/src/pages/[lang]/contested/index.astro` (46 lines)
- Modify: `site/src/pages/[lang]/contested/[slug].astro` (102 lines)

- [ ] **Step 1: Read all four files**

- [ ] **Step 2: Update concept index**

Replace card-based layout with ruled list:
```html
<div class="label">Konzepte</div>
<div class="ruled-list">
  {concepts.map(c => (
    <a href={`/${lang}/concepts/${c.slug}/`} class="ruled-item">
      <span class="ruled-item-title">{c.title}</span>
      <span class="ruled-item-meta">{c.provisions.length} Bestimmungen · {c.confidence}</span>
    </a>
  ))}
</div>
```

```css
.ruled-list { border-top: 1px solid var(--color-rule); }
.ruled-item {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding: 12px 0;
  border-bottom: 1px solid var(--color-rule-light);
  text-decoration: none;
  color: var(--color-text);
  font-size: 13px;
}
.ruled-item:hover { background: var(--color-rule-light); }
.ruled-item-meta { font-size: 11px; color: var(--color-text-muted); }
```

- [ ] **Step 3: Update concept detail**

Apply page-grid. Left: concept title, confidence, related provisions. Right: prose content.

- [ ] **Step 4: Update contested index**

Same ruled-list pattern. Show question text and position count.

- [ ] **Step 5: Update contested detail**

Apply page-grid. Left: question summary, provisions. Right: positions and prose content. Remove colored border-left on question card — use a rule instead.

- [ ] **Step 6: Verify build**

Run: `cd site && npm run build`

- [ ] **Step 7: Commit**

```bash
git add site/src/pages/[lang]/concepts/ site/src/pages/[lang]/contested/
git commit -m "feat(site): update concept and contested pages for Swiss style"
```

---

### Task 12: Update markdown rendering (Randziffer + BGE citation styles)

**Files:**
- Modify: `site/src/lib/markdown.ts` (lines 40-73 ranziffer plugin, lines 75-125 BGE plugin)

- [ ] **Step 1: Read markdown.ts**

Read the rehypeRandziffern and rehypeBgeCitations plugins.

- [ ] **Step 2: Update Randziffer plugin**

The plugin generates HTML elements with classes. The CSS is in global.css (already updated in Task 1). The plugin itself may set inline styles or class names. Check:
- If it adds `color` inline styles referencing green → remove them
- If it adds classes like `randziffer` → keep (CSS in global.css handles styling)
- The class name `.randziffer` should stay — it's referenced in the new global.css prose styles

Likely: no changes needed to the JS/TS code — the styling is all in CSS. But verify by reading the code.

- [ ] **Step 3: Update BGE citation plugin**

Same check — if the plugin adds inline styles or green-referencing classes, update them. The `.cite-bge` class should remain — it's in the new CSS.

- [ ] **Step 4: Verify build and check rendered markdown**

Run: `cd site && npm run build`
Check a built article page to verify Randziffern and BGE citations render correctly.

- [ ] **Step 5: Commit (only if changes were needed)**

```bash
git add site/src/lib/markdown.ts
git commit -m "feat(site): update markdown rendering for Swiss style"
```

---

### Task 13: Final verification and cleanup

**Files:**
- Various — grep for leftover references

- [ ] **Step 1: Search for leftover old references**

```bash
cd site && grep -r "accent" src/ --include="*.astro" --include="*.css" --include="*.ts" -l
cd site && grep -r "shadow" src/ --include="*.astro" --include="*.css" --include="*.ts" -l
cd site && grep -r "gradient" src/ --include="*.astro" --include="*.css" --include="*.ts" -l
cd site && grep -r "border-radius" src/ --include="*.astro" --include="*.css" --include="*.ts" -l
cd site && grep -r "backdrop-filter" src/ --include="*.astro" --include="*.css" --include="*.ts" -l
cd site && grep -r "LawCard" src/ --include="*.astro" --include="*.ts" -l
cd site && grep -r "CrossReferences" src/ --include="*.astro" --include="*.ts" -l
cd site && grep -r "Instrument Serif" src/ --include="*.astro" --include="*.css" -l
cd site && grep -r "Manrope" src/ --include="*.astro" --include="*.css" -l
cd site && grep -r "JetBrains" src/ --include="*.astro" --include="*.css" -l
```

Fix any findings: remove dead imports, remove lingering old variable references, remove unused font references.

- [ ] **Step 2: Full build and lint**

```bash
cd site && npm run build
```

Expected: Build succeeds with no errors.

- [ ] **Step 3: Preview and visual check**

```bash
cd site && npm run preview
```

Open in browser. Check:
- Home page: hero + stats + law grid, black/white, no decoration
- Article page: asymmetric grid, metadata left, content right
- Tabs: uppercase, black underline active state
- Dark mode: toggle works, calibrated inversion
- Mobile: grid collapses, readable
- Search: ⌘K works, results display correctly

- [ ] **Step 4: Commit any cleanup fixes**

```bash
git add -A site/src/
git commit -m "chore(site): cleanup leftover references from pre-redesign styles"
```

---

## Task Dependency Summary

```
Chunk 1 (foundation):  Task 1 → Task 2
Chunk 2 (components):  Task 3, Task 4, Task 5, Task 6, Task 7 (all depend on Task 1, independent of each other)
Chunk 3 (pages):       Task 8 → Task 9 → Task 10 → Task 11 → Task 12 → Task 13

Task 1 blocks everything else.
Chunk 2 tasks are independent of each other.
Chunk 3 tasks are mostly independent but Task 13 (cleanup) must be last.
```
