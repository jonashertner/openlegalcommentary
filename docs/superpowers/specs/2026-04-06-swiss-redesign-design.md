# Swiss International Style Redesign — Design Specification

**Date:** 2026-04-06
**Status:** Draft

## Vision

Redesign openlegalcommentary.ch in the tradition of Swiss International Typographic Style (Müller-Brockmann, Helvetica, mathematical grids, asymmetric layouts) applied to a legal reference tool. Strip all decoration. Let typography, grid, and whitespace do the work. The content IS the design.

**Reference:** Typographische Monatsblätter, NZZ, Müller-Brockmann's grid systems.

## Design Principles

1. **Grid as skeleton** — A consistent asymmetric grid (metadata left, content right) structures every page. Rules (lines) make the grid visible.
2. **Typography as hierarchy** — Size and weight create all differentiation. No color coding, no icons for emphasis.
3. **Whitespace as design** — Generous space is structural, not decorative.
4. **Black and white** — No accent color. Black for structure and emphasis. Grays for hierarchy. Period.
5. **Flat and honest** — No shadows, no gradients, no glass effects, no texture overlays, no decorative animations.
6. **Function only** — Every element serves a purpose. If it doesn't help the practitioner find what they need, remove it.

## What Changes

### Strip

| Current | Action |
|---------|--------|
| Paper texture overlay (`body::before` fractal noise) | Remove |
| Glass morphism header (`backdrop-filter: blur`) | Remove — solid background |
| Gradient accent line (`body::after`, `--gradient-accent`) | Remove |
| Card shadows (`--shadow-*`) | Remove all shadow variables |
| Hover lift animations (`transform: translateY(-2px)`) | Remove |
| Decorative animations (`fadeUp`, `scaleIn`, `slideInLeft`) | Remove |
| Forest green accent color (`#166534`) | Remove — no accent color |
| Warm cream background (`#FAFDF7`) | Replace with `#FFFFFF` |
| 4 font families (Instrument Serif, Manrope, Source Serif 4, JetBrains Mono) | Reduce to 2 |
| Rounded corners (`border-radius: 8-16px`) | Remove or minimal (2px max) |
| Icon decorations in headers | Remove |

### Introduce

| Element | Purpose |
|---------|---------|
| Asymmetric 2-column grid (200px + 1fr) | Metadata left, content right — every page |
| Horizontal rules as structural elements | Replace cards/shadows with ruled sections |
| Uppercase micro-labels (10px, 0.15em tracking) | Section identification |
| Full-width header rule (1px solid #000) | Primary structural division |
| System Helvetica for all UI | Single UI typeface, zero font loading for UI |
| Bold article numbers as wayfinding | Large, heavy numerals for article identification |

## Typography

### Typeface Pairing

| Role | Typeface | Weight | Usage |
|------|----------|--------|-------|
| **UI / Structure** | Helvetica, Arial, sans-serif (system) | 400, 500, 700 | Headers, navigation, labels, tabs, metadata, cross-references |
| **Body / Reading** | Source Serif 4, Georgia, serif (Google Fonts) | 400, 600 | Commentary prose, Gesetzestext, blockquotes |

No other fonts. Remove Instrument Serif, Manrope, JetBrains Mono from the font loading. Code snippets (if any) use the system monospace stack.

### Type Scale

```css
--text-xs:   10px;    /* Micro-labels, uppercase tracking */
--text-sm:   11px;    /* Metadata, secondary info */
--text-base: 12px;    /* Navigation, tabs, UI text */
--text-body: 14px;    /* Prose body text (Source Serif 4) */
--text-md:   15px;    /* Lead body text */
--text-lg:   24px;    /* Law abbreviations, section headings */
--text-xl:   36px;    /* Article numbers */
--text-2xl:  42px;    /* Hero stats */
--text-hero: 52px;    /* Hero title */
```

### Micro-Labels

A key pattern throughout the design — small uppercase labels that identify sections:

```css
.label {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 10px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: #999;
}
```

Used for: ARTIKEL, GESETZ, AKTUALISIERT, QUERVERWEIS, GESETZESTEXT, GESETZE, etc.

## Color

### Light Mode (Default)

```css
--color-bg:             #FFFFFF;
--color-text:           #000000;
--color-text-secondary: #666666;
--color-text-muted:     #999999;
--color-text-faint:     #CCCCCC;
--color-rule:           #000000;    /* Primary structural rules */
--color-rule-light:     #EEEEEE;    /* Secondary dividers */
--color-border:         #E0E0E0;    /* Gesetzestext box, inputs */
```

### Dark Mode

```css
[data-theme='dark'] {
  --color-bg:             #0A0A0A;
  --color-text:           #E0E0E0;
  --color-text-secondary: #999999;
  --color-text-muted:     #666666;
  --color-text-faint:     #555555;
  --color-rule:           #E0E0E0;
  --color-rule-light:     #222222;
  --color-border:         #333333;
}
```

Body text in dark mode: `#C8C8C8` (slightly dimmer than UI text for reading comfort).

### No Accent Color

All interactive states (links, active tabs, hover) use `#000000` (light) / `#E0E0E0` (dark) — the primary text color. Inactive states use gray. There is no green, no red, no blue. The only visual distinction is weight and position.

Links: underlined, same text color. Hover: slightly darker/lighter gray.

Active tab: bold + 2px black underline.

## Layout Grid

### The Asymmetric Grid

Every content page uses the same grid: a fixed-width left column for metadata, a fluid right column for content.

```
┌──────────────────────────────────────────────────────┐
│  Header (full width, rule below)                      │
├──────────┬───────────────────────────────────────────┤
│          │                                            │
│  200px   │  Content (fluid)                           │
│  Metadata│                                            │
│  Column  │  · Tabs                                    │
│          │  · Prose (max-width: 600px)                │
│  · Label │  · Gesetzestext                            │
│  · Value │  · Pagination                              │
│  · Rule  │                                            │
│  · Label │                                            │
│  · Value │                                            │
│          │                                            │
└──────────┴───────────────────────────────────────────┘
```

```css
.page-grid {
  display: grid;
  grid-template-columns: 200px 1fr;
}
```

**Left column contents** (article detail): Article number (large, bold), article title, law abbreviation, SR number, last updated date, cross-references, Fedlex link. Separated by light rules.

**Mobile**: The grid collapses to single column. Left column metadata moves above the content.

### Max Widths

```css
--max-width:     1280px;   /* Page wrapper */
--content-width: 600px;    /* Prose reading width */
--left-col:      200px;    /* Metadata column */
```

## Page Designs

### Home Page

```
┌─────────────────────────────────────────────────────┐
│  openlegalcommentary    Gesetze  Konzepte  ...  ⌘K  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  OPEN ACCESS · TÄGLICH AKTUALISIERT · KI-GENERIERT  │
│                                                      │
│  Kommentar zum         ┌─────────┬─────────┐        │
│  Schweizer             │  4 843  │  963K   │        │
│  Bundesrecht           │ ARTIKEL │ENTSCHEIDE│        │
│                        ├─────────┼─────────┤        │
│  [description in       │    9    │    4    │        │
│   Source Serif 4]      │ GESETZE │SPRACHEN │        │
│                        └─────────┴─────────┘        │
├─────────────────────────────────────────────────────┤
│  GESETZE                                             │
│  ┌───────────┬───────────┬───────────┐              │
│  │ BV    233 │ ZGB 1126  │ OR  1584  │              │
│  │ Bundes-   │ Zivilge-  │ Obligatio-│              │
│  │ verfassung│ setzbuch  │ nenrecht  │              │
│  ├───────────┼───────────┼───────────┤              │
│  │ ZPO   426 │ StGB  466 │ StPO  478 │              │
│  ├───────────┼───────────┼───────────┤              │
│  │ SchKG 400 │ VwVG   92 │ BGFA   38 │              │
│  └───────────┴───────────┴───────────┘              │
├─────────────────────────────────────────────────────┤
│  Quelle: OpenCaseLaw.ch · CC0 · MIT                 │
└─────────────────────────────────────────────────────┘
```

- Hero: asymmetric, title left (52px Helvetica bold), stats grid right (rule-separated)
- Eyebrow: uppercase micro-label
- Description: Source Serif 4, secondary color
- Laws: 3-column grid, ruled borders (not cards), bold abbreviations, article counts
- Footer: single rule, one line

### Article Detail Page

```
┌─────────────────────────────────────────────────────┐
│  openlegalcommentary    Gesetze  Konzepte  ...  ⌘K  │
├─────────────────────────────────────────────────────┤
│  BGFA → Art. 12                                      │
├──────────┬──────────────────────────────────────────┤
│          │                                           │
│ ARTIKEL  │  ┌─ Gesetzestext ────────────────────┐   │
│ 12       │  │ ¹ Die Anwältinnen und Anwälte ...  │   │
│ Berufs-  │  │   a. sorgfältige Berufsausübung;   │   │
│ regeln   │  │   b. unabhängige Berufsausübung;    │   │
│          │  └────────────────────────────────────┘   │
│ ──────── │                                           │
│ GESETZ   │  ÜBERSICHT  Doktrin  Rechtsprechung      │
│ BGFA     │  ──────────────────────────────────────   │
│ SR 935.61│                                           │
│          │  [Body text in Source Serif 4, 14px,       │
│ ──────── │   line-height 1.85, max-width 600px]      │
│ AKTUALI- │                                           │
│ SIERT    │  N. 1 Art. 12 BGFA enthält den ab-       │
│ 6.4.2026 │  schliessenden Katalog der Berufsregeln  │
│          │  für im Register eingetragene Anwältin-   │
│ ──────── │  nen und Anwälte...                       │
│ QUERVER- │                                           │
│ WEIS     │  N. 2 Das Bundesgericht hat in BGE 130   │
│ → Art.13 │  II 270 bestätigt, dass der Katalog      │
│ → Art. 8 │  bundesrechtlich abschliessend ist.       │
│          │                                           │
│ ──────── │  ← Art. 11              Art. 13 →        │
│ FEDLEX   │                                           │
│ Original │                                           │
└──────────┴──────────────────────────────────────────┘
```

- Breadcrumb: minimal, inline, light text
- Left column: article number (48px bold), metadata stack with micro-labels and rules
- Gesetzestext: bordered box, no background fill, micro-label header
- Tabs: uppercase, 2px black underline on active, no background
- Body: Source Serif 4, 14px, 1.85 line-height, 600px max-width
- Randziffern: Helvetica bold, inline with text
- BGE citations: bold
- Blockquotes: 2px left border, slightly smaller, italic
- Cross-reference links: plain text with → prefix
- Pagination: rules, arrows, article title in muted gray

### Law Index Page

```
┌─────────────────────────────────────────────────────┐
│  openlegalcommentary    Gesetze  ...                 │
├─────────────────────────────────────────────────────┤
│  BGFA → Inhaltsverzeichnis                          │
├──────────┬──────────────────────────────────────────┤
│          │                                           │
│ BGFA     │  1. KAPITEL: ALLGEMEINE BESTIMMUNGEN     │
│ Anwalts- │  ─────────────────────────────────────   │
│ gesetz   │  Art. 1    Gegenstand                    │
│          │  Art. 2    Geltungsbereich               │
│ SR 935.61│  Art. 3    Verhältnis zum kantonalen     │
│          │            Recht                          │
│ 38 Art.  │                                           │
│          │  2. KAPITEL: FREIZÜGIGKEIT                │
│          │  ─────────────────────────────────────   │
│          │  Art. 4    Grundsatz                      │
│          │  Art. 5    Kantonales Anwaltsregister     │
│          │  ...                                      │
└──────────┴──────────────────────────────────────────┘
```

Same asymmetric grid. Left column: law abbreviation, title, SR number, article count. Right: structured table of contents with chapter headings as uppercase rules.

### Concept & Contested Pages

Follow the same grid. Left column: concept/question metadata (type, confidence, related provisions). Right column: prose in Source Serif 4.

## Components

### Header

```css
.site-header {
  border-bottom: 1px solid var(--color-rule);
  background: var(--color-bg);  /* Solid, no blur */
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 var(--space-6);
}

.site-name {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--color-text);
  text-decoration: none;
}
```

No logo mark (the green square). The name IS the logo — typographic identity. No backdrop blur. Solid background. Black rule below.

### Search

Same modal overlay approach, but styled to match: no rounded corners, no shadows. Simple bordered box, white/black bg, Helvetica input.

### Footer

Single rule on top. One line: source attribution left, site name right. Minimal.

```css
.site-footer {
  border-top: 1px solid var(--color-rule);
  padding: 24px var(--space-6);
  font-size: 11px;
  color: var(--color-text-muted);
}
```

### Tabs

```css
.tab {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 12px;
  font-weight: 400;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 10px 0;
  margin-right: 24px;
  color: var(--color-text-muted);
  border-bottom: 2px solid transparent;
  cursor: pointer;
}

.tab.active {
  font-weight: 700;
  color: var(--color-text);
  border-bottom-color: var(--color-text);
}
```

### Gesetzestext Box

```css
.gesetzestext {
  border: 1px solid var(--color-border);
  padding: 20px 24px;
  margin-bottom: 32px;
}

.gesetzestext-label {
  /* micro-label pattern */
  font-size: 10px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  margin-bottom: 12px;
}

.gesetzestext-body {
  font-family: 'Source Serif 4', Georgia, serif;
  font-size: 13px;
  line-height: 1.8;
}
```

No background fill. No rounded corners. No icon. Just a bordered container with a micro-label.

### Breadcrumb

```css
.breadcrumb {
  font-size: 11px;
  color: var(--color-text-muted);
  padding: 12px 0;
  border-bottom: 1px solid var(--color-rule-light);
}
```

Inline, separated by →, no decorative elements.

## Spacing

8px baseline grid (unchanged from current):

```css
--space-1:  8px;
--space-2:  16px;
--space-3:  24px;
--space-4:  32px;
--space-5:  48px;
--space-6:  48px;   /* Page padding */
--space-8:  64px;
```

## Responsive

### Breakpoints

```css
@media (max-width: 768px) {
  .page-grid {
    grid-template-columns: 1fr;  /* Single column */
  }

  .left-column {
    border-right: none;
    border-bottom: 1px solid var(--color-rule-light);
    padding-bottom: var(--space-3);
    margin-bottom: var(--space-3);
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-3);
    align-items: baseline;
  }

  /* Article number inline with title on mobile */
  .article-number {
    font-size: 36px;
  }

  /* Laws grid: 2 columns on tablet, 1 on phone */
  .laws-grid {
    grid-template-columns: 1fr 1fr;
  }

  /* Hero: stack, no stats grid */
  .hero-grid {
    grid-template-columns: 1fr;
  }

  .hero-title {
    font-size: 36px;
  }

  /* Full-width tabs */
  .tabs {
    overflow-x: auto;
  }

  /* Page padding reduced */
  --space-6: 24px;
}

@media (max-width: 480px) {
  .laws-grid {
    grid-template-columns: 1fr;
  }

  .hero-title {
    font-size: 28px;
  }
}
```

On mobile, the left metadata column becomes a horizontal bar above the content — article number, title, and key metadata flow inline. The grid becomes a single column.

## Transitions

Minimal. No entrance animations. Only functional transitions:

```css
a { transition: color 150ms ease-out; }
.tab { transition: color 150ms ease-out, border-color 150ms ease-out; }
```

No `fadeUp`, no `scaleIn`, no `slideInLeft`, no staggered delays. The page loads, the content is there.

## Accessibility

All existing accessibility features preserved:
- Skip link
- Focus-visible outlines (2px solid var(--color-text))
- Touch targets (44px minimum)
- Reduced motion media query
- Screen reader text (.sr-only)
- Selection styling

Focus outlines change from green to black/white to match the new palette.

## Font Loading

Remove the current Google Fonts import (4 families). Replace with:

```css
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&display=swap');
```

One font loaded. Helvetica is a system font — no loading needed. This significantly improves page load performance.

## Files Changed

| File | Change |
|------|--------|
| `site/src/styles/global.css` | **Rewrite** — new color vars, typography, remove all decorative styles |
| `site/src/layouts/Base.astro` | **Modify** — remove paper texture, accent line, update font import |
| `site/src/components/Header.astro` | **Rewrite** — remove glass blur, logo mark, simplify to text + rule |
| `site/src/components/Footer.astro` | **Rewrite** — single rule, one line |
| `site/src/components/ArticleTabs.astro` | **Modify** — remove tab indicator animation, simplify to uppercase + underline |
| `site/src/components/Gesetzestext.astro` | **Modify** — remove icon, background, radius; keep bordered box |
| `site/src/components/SearchModal.astro` | **Modify** — remove blur, radius, shadows; plain bordered modal |
| `site/src/components/Breadcrumb.astro` | **Simplify** — inline text only |
| `site/src/components/CrossReferences.astro` | **Remove** — metadata moves to left column |
| `site/src/components/ArticlePagination.astro` | **Simplify** — ruled line, arrows, text |
| `site/src/pages/[lang]/index.astro` | **Rewrite** — new hero, stats grid, law grid |
| `site/src/pages/[lang]/[law]/index.astro` | **Modify** — asymmetric grid layout |
| `site/src/pages/[lang]/[law]/[article].astro` | **Modify** — asymmetric grid, left metadata column |
| `site/src/pages/[lang]/concepts/*.astro` | **Modify** — same grid treatment |
| `site/src/pages/[lang]/contested/*.astro` | **Modify** — same grid treatment |
| `site/src/lib/markdown.ts` | **Modify** — update Randziffern styling (remove green, use bold black) |
| `site/src/components/LawCard.astro` | **Remove** — replaced by ruled grid cells |

## Success Criteria

1. Only 2 typefaces load: system Helvetica (0 bytes) + Source Serif 4 (one Google Font)
2. Zero box shadows in the entire CSS
3. Zero border-radius values above 2px
4. Zero gradient declarations
5. Zero decorative animations (only functional transitions on interactive elements)
6. Every page uses the asymmetric 2-column grid (200px + fluid) on desktop
7. Dark mode is pure polarity inversion — same grid, same rules, same hierarchy
8. Lighthouse performance score improves (fewer fonts, no blur, no texture)
