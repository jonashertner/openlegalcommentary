# Full-text Search + Visual Design Elevation

**Date:** 2026-03-17
**Status:** Approved

## Goal

1. Add full-text search with citation matching using Pagefind, with a visually stunning search experience
2. Elevate the entire site to world-class Swiss modernist design across all screen sizes

## Part 1: Search

### Engine: Pagefind

Pagefind runs post-build, generates a static search index, and provides a client-side JS API. No server needed.

### Search scope

- Full article commentary text (summary, doctrine, caselaw — all languages)
- Article titles and numbers
- BGE citations (e.g., "BGE 130 III 182") as searchable text within content
- Law abbreviations

### Index configuration

Pagefind indexes all static HTML. To control what's indexed:
- Add `data-pagefind-body` to the article content area in `[article].astro`
- Add `data-pagefind-meta` attributes for law, article number, language
- Add `data-pagefind-filter` for law and language faceting
- Exclude nav/footer/chrome with `data-pagefind-ignore`

### Search UI — "Command palette" style

Replace the current search bar with a full-screen modal search (cmd+K / ctrl+K trigger):

**Visual design:**
- Overlay: frosted glass backdrop (`backdrop-filter: blur(20px)`, semi-transparent warm background)
- Modal: centered, max-width 640px, rounded-lg, elevated shadow-xl
- Input: large (text-xl), no border, full-width, with magnifying glass icon and keyboard shortcut badge
- Results: scrollable list below input, max-height 60vh
- Each result shows:
  - Law badge (e.g., "BV") in accent color, monospace
  - Article number and title
  - Content snippet with highlighted match terms
  - Language indicator if not current language
- Empty state: subtle hint text ("Search articles, citations, or legal concepts...")
- Loading state: minimal skeleton pulse animation

**Interactions:**
- Opens: cmd+K / ctrl+K, or clicking search icon in header
- Navigation: arrow keys to move, Enter to select, Escape to close
- Click outside to close
- Auto-focus input on open
- Debounced search (150ms)
- Results grouped by law with subtle section dividers

**Mobile:**
- Full-screen takeover (no modal, slides up from bottom)
- Sticky input at top
- Touch-friendly result items (min 48px tap target)

### Citation search

BGE references like "BGE 130 III 182" naturally appear in caselaw layer content. Pagefind indexes this text, so searching "BGE 130 III 182" returns all articles that cite that decision. No special handling needed beyond ensuring caselaw content is indexed.

### Multilingual search

Pagefind supports multilingual indexing. Each language version of an article page is a separate static page with `<html lang={lang}>`, so Pagefind creates per-language index segments.

**Language filtering:** Pagefind does NOT auto-filter by page language. The `SearchModal` JS must explicitly:
1. Read `document.documentElement.lang` to get the current language
2. Pass `{ filters: { language: currentLang } }` to `pagefind.search()` calls
3. Provide a toggle to "search all languages" which removes the filter

Each indexed page must emit `data-pagefind-filter="language:{lang}"` on the content area (e.g., `<article data-pagefind-body data-pagefind-filter="language:de">`).

### Integration

- Add `pagefind` as a pinned dev dependency in `site/package.json` (e.g., `"pagefind": "^1.3.0"`)
- Add post-build step: `"postbuild": "pagefind --site dist"`
- **Important:** always use `npm run build` (not `astro build` directly) to ensure postbuild runs
- Replace `SearchBar.astro` with new `SearchModal.astro` component
- Add search trigger button in `Header.astro` (magnifying glass icon + "⌘K" badge)
- Remove `scripts/generate_search_index.py` and the `prebuild` step (Pagefind replaces it)
- Remove `site/public/search-index.json`

### Dev mode

Pagefind only works post-build — the index doesn't exist during `npm run dev`. The `SearchModal` must handle this gracefully:
- Attempt to load the Pagefind JS bundle dynamically (`import('/pagefind/pagefind.js')`)
- If the import fails, show a message: "Search available after build" (translated via `t()`)
- No fallback to the old JSON search — keep it simple

## Part 2: Visual Design Elevation

### Design philosophy

Swiss International Typographic Style, adapted for screens:
- **Grid discipline** — strict alignment, mathematical spacing
- **Typography as primary design element** — size, weight, and spacing create hierarchy, not decoration
- **Purposeful whitespace** — generous breathing room, content doesn't feel cramped
- **Restrained color** — Swiss Red as the singular accent, everything else in warm neutrals
- **Micro-interactions** — subtle, purposeful motion that feels alive without being distracting
- **Print-quality typography** — careful kerning, optical sizing, hanging punctuation where possible

### Typography refinements

Keep the current font stack (Instrument Serif, Manrope, Source Serif 4) — it's excellent. Refine:

- **Hero text:** Add subtle letter-spacing: -0.03em for large display text (tighter = more premium)
- **Body text:** Increase line-height from 1.7 to 1.75 for better readability at longer measures
- **Paragraph spacing:** Use `margin-bottom: 1.5em` instead of `1em` for more breathing room in prose
- **Blockquotes (Guillemets):** Left border in accent color, italic Source Serif, slightly indented
- **Footnote-style citations:** Smaller text, muted color, tight leading

### Color refinements

The warm palette is good. Additions:

- **Accent gradient** (subtle): `linear-gradient(135deg, #DC2626, #B91C1C)` for hero accent line and key CTAs
- **Glass tint** for elevated surfaces: `background: color-mix(in srgb, var(--color-bg-elevated) 80%, transparent)` with `backdrop-filter: blur(12px)`. In dark mode, use 65% opacity with a slightly lightened elevated color to preserve the frosted glass effect
- **Hover states:** Subtle warm tint (`background: color-mix(in srgb, var(--color-accent) 4%, var(--color-bg))`) instead of flat gray shifts
- **Dark mode polish:** Slightly warmer darks, accent red brightened for contrast

### Layout improvements

**Global:**
- Increase `--max-width` from 1200px to 1280px for more horizontal room
- Add a subtle top-of-page accent line (2px, full-width, gradient red) as a Swiss modernist signature element
- Sticky header: add a subtle bottom shadow on scroll (not visible at top)

**Home page:**
- Hero: larger vertical padding (add `--space-16: 12rem` token to `global.css`), let the typography breathe
- Laws grid: 3 columns on desktop (currently 2), each card gets a subtle top accent border on hover
- Stats: larger numbers, use Instrument Serif for the stat values (numbers in serif = premium feel)
- Add a subtle grid pattern or Swiss cross watermark at very low opacity in the hero background

**Law index page:**
- Progress bar: thinner (3px), accent gradient fill, rounded
- Structural headings (Titel/Kapitel): more vertical spacing, subtle left accent border
- Article list items: add hover animation — slight translateX(4px) shift with accent border reveal

**Article page:**
- Tab bar: bottom border becomes a thin accent underline that slides to the active tab (CSS transition on a pseudo-element)
- Gesetzestext panel: slightly elevated with shadow-sm, warm card background
- Reading progress bar: refine existing implementation (currently 3px) to 2px with accent gradient
- Randziffern (N. 1, N. 2): styled as elegant sidebar markers

**About/Changelog:**
- More generous section spacing
- Pull quotes or key statements in larger Instrument Serif

### Responsive excellence

**Breakpoints:**
- Mobile: < 640px
- Tablet: 640px – 1024px
- Desktop: > 1024px

**Mobile-specific:**
- Touch-friendly tap targets (min 44px)
- Horizontal scroll prevention on all elements
- Bottom-anchored navigation consideration for future
- Search: full-screen takeover
- Article tabs: horizontally scrollable if needed
- Gesetzestext: collapsible by default on mobile (currently always visible)
- Laws grid: single column, cards stack
- Typography: hero text scales down gracefully via clamp()

**Tablet:**
- Laws grid: 2 columns
- Article page: Gesetzestext as collapsible sidebar
- Header: all nav items visible (no hamburger unless < 640px)

**Desktop:**
- Laws grid: 3 columns
- Full header with search trigger, language switcher, theme toggle
- Article page: Gesetzestext as persistent sidebar

### Micro-interactions and motion

- **Page transitions:** Subtle fade (opacity 0→1, 200ms) on navigation via View Transitions API (Astro supports this natively)
- **Scroll-triggered animations:** Elements fade in as they enter viewport (IntersectionObserver), staggered for lists
- **Hover effects:** Smooth, 150ms ease-out. Cards lift slightly (translateY(-2px) + shadow increase)
- **Active tab indicator:** Slides horizontally to follow the active tab. Uses JS to measure each tab's `offsetLeft` and `width`, then sets `transform: translateX()` and `width` on a `::after` pseudo-element. Required because tab label widths vary across languages (DE "Übersicht" vs EN "Overview")
- **Search modal:** Scales in from 0.96 with opacity (200ms, ease-out)
- **Reduced motion:** All animations respect `prefers-reduced-motion: reduce`

### Accessibility

- All interactive elements: visible focus rings (2px accent, 2px offset)
- Color contrast: WCAG AA minimum on all text
- Skip-to-content link
- Proper heading hierarchy on every page
- ARIA labels on all interactive elements
- Keyboard navigation for search modal, tabs, language switcher

## Implementation notes

- No new CSS framework — extend the existing custom properties system
- No new JS framework — vanilla JS + Astro components
- Pagefind is the only new dependency
- View Transitions API via Astro's built-in `<ViewTransitions />` component
- All visual changes are CSS-only where possible

### View Transitions + Pagefind re-initialization

Astro's View Transitions performs client-side DOM swaps. Pagefind's JS needs to be re-initialized after each navigation because `DOMContentLoaded` does not re-fire. The `SearchModal` must:
- Listen for `astro:page-load` event (fires on initial load AND after each view transition)
- Re-initialize the Pagefind connection and modal event listeners on each `astro:page-load`
- Use `astro:page-load` consistently across all client-side scripts (theme toggle, search modal, tab indicator, etc.)

### Implementation order

These specs must be implemented in this order:
1. **i18n route restructure** — move pages under `[lang]/`, create `i18n.ts`, update all components
2. **Search** — add Pagefind and `SearchModal` (replaces old `SearchBar`)
3. **Visual design** — CSS refinements, animations, View Transitions

The i18n LanguageSwitcher redesign (from buttons to `<a>` tags) must be done before the header visual changes.
