# Beta tag — design

Add a site-wide top bar that marks openlegalcommentary as being in active
development. The bar appears above the existing sticky header and carries a
single, translated sentence; no explanatory link, no click target.

## Rationale

The site is deploying AI-generated legal commentary at increasing visibility.
First-time visitors need an unambiguous, persistent signal that the content is
evolving and should be treated as a starting point rather than settled doctrine.
A top bar is the most direct instrument: it sits above the fold, is part of the
sticky chrome, and cannot be missed.

## Placement

**Top bar inside the existing `<header class="site-header">`**, as the first
child before `.header-inner`. The bar is part of the sticky header so it stays
visible while scrolling. Total sticky height grows from 48px to ~72px.

```
┌──────────────────────────────────────────────────┐
│ openlegalcommentary befindet sich in aktiver …   │  ← .beta-bar, ~24px
├──────────────────────────────────────────────────┤
│ [logo]  [nav]              [⌘K] [☀] [DE]         │  ← .header-inner, 48px
└──────────────────────────────────────────────────┘
```

## Copy

A single sentence, translated per language, no "BETA" label, no link:

- **DE:** openlegalcommentary befindet sich in aktiver Entwicklung.
- **FR:** openlegalcommentary est en développement actif.
- **IT:** openlegalcommentary è in sviluppo attivo.
- **EN:** openlegalcommentary is in active development.

The sentence is deliberately terse. The word "openlegalcommentary" appears
again as the logo directly below; the visual distinction (muted 11px vs bold
14px) keeps it from reading as duplication.

## Styling

- `font-size: 11px`
- `font-weight: 700` (bold)
- `color: #DC2626` (strong red, for warning/status signal)
- `line-height: 1`
- `padding: 6px 0`
- `border-bottom: 1px solid var(--color-rule-light)`
- Centered horizontally within `.page-wrapper`
- No background fill, no radius, no shadow

The red-on-white (or red-on-dark) bold treatment is the one chromatic
exception to the otherwise monochrome Swiss redesign. It's load-bearing:
the notice must be unambiguous and impossible to mistake for metadata or
footer chrome. Red+bold is the universal convention for "status: beta /
work in progress" and earns its break from the palette.

Height breakdown: 11 (text) + 12 (padding) + 1 (border) = 24px.
New total sticky header height: 48 + 24 = 72px.

## Knock-on updates

Changing the sticky header height from 48px to 72px affects three CSS values
that currently hardcode the 48px assumption:

1. `Header.astro` — `.mobile-nav .nav-list { top: 48px }` → `72px`
2. `Header.astro` — `.mobile-nav .nav-list { height: calc(100vh - 48px) }` → `calc(100vh - 72px)` (both `100vh` and `100dvh` lines)
3. `global.css` — `.prose .randziffer { scroll-margin-top: 4rem }` → `5rem`
   (4rem = 64px was chosen to clear the old 48px sticky header; 5rem = 80px
   comfortably clears the new 72px.)

Other `48px` references in the codebase (`--page-pad`, unrelated `font-size: 48px`
headings, mobile-nav link `min-height` tap target) are unrelated and stay.

## Files touched

1. `site/src/components/Header.astro` — add beta bar markup and CSS,
   update three mobile-nav hardcoded heights
2. `site/src/lib/i18n.ts` — add `header.beta_notice` key with four languages
3. `site/src/styles/global.css` — bump `.prose .randziffer` scroll-margin-top
4. `site/src/pages/[lang]/about.astro` — **not touched** (no click target)

## Verification

1. `cd site && npm run build` — static build must succeed
2. Spot-check all four language roots render the translated sentence
3. Spot-check that clicking a Randziffer anchor in an article page lands with
   the target comfortably below the sticky header (not clipped)
4. Spot-check mobile menu dropdown: open hamburger on narrow viewport, verify
   the menu flush aligns with the bottom of the sticky header (no gap, no
   overlap)

## Out of scope

- A dedicated `/beta` page or `/about#beta` section — the bar is self-contained
- "BETA" label/badge inside the bar — user specified the sentence alone
- Dismissible / localStorage-remembered beta notice — permanent until removed
- Additional i18n strings for aria-label on the bar itself — it's a `<p>`, not
  a link or button; the sentence is its own accessible content
