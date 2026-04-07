# Consolidation: BGFA Commentary, Concept/Contested Pages, Site Integration

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate BGFA Art. 12/13 commentary, build Astro routes for concept/contested pages, add cross-reference sidebar, integrate BGFA into site, and archive the prototype repo.

**Architecture:** Content-first approach. Generate the BGFA article commentary following existing 3-layer conventions. Extend the Astro site with new dynamic routes for concepts/contested content types. Add cross-reference scanning in the content library. Keep all changes additive — no modifications to existing law content or pipeline code.

**Tech Stack:** Astro (site), TypeScript (lib), Python (schema/tests), Markdown/YAML (content)

---

## File Structure

### Files to Create
- `content/bgfa/art-012/summary.md` — BGFA Art. 12 summary layer
- `content/bgfa/art-012/doctrine.md` — BGFA Art. 12 doctrine layer
- `content/bgfa/art-012/caselaw.md` — BGFA Art. 12 caselaw layer
- `content/bgfa/art-013/summary.md` — BGFA Art. 13 summary layer
- `content/bgfa/art-013/doctrine.md` — BGFA Art. 13 doctrine layer
- `content/bgfa/art-013/caselaw.md` — BGFA Art. 13 caselaw layer
- `site/src/pages/[lang]/concepts/[slug].astro` — concept page renderer
- `site/src/pages/[lang]/concepts/index.astro` — concept index page
- `site/src/pages/[lang]/contested/[slug].astro` — contested page renderer
- `site/src/pages/[lang]/contested/index.astro` — contested index page
- `site/src/components/CrossReferences.astro` — cross-reference sidebar component

### Files to Modify
- `content/bgfa/art-012/meta.yaml` — add layer metadata after generation
- `content/bgfa/art-013/meta.yaml` — add layer metadata after generation
- `site/src/lib/laws.ts` — add BGFA to LAWS array
- `site/src/lib/content.ts` — add concept/contested loading functions, cross-reference scanner
- `site/src/lib/i18n.ts` — add i18n keys for concepts, contested, new nav items
- `site/src/pages/[lang]/[law]/[article].astro` — add 'bgfa' to laws list, add CrossReferences component
- `site/src/pages/[lang]/[law]/index.astro` — add 'bgfa' to laws list
- `site/src/pages/[lang]/index.astro` — integrate BGFA into homepage (currently only BV featured + others forthcoming)
- `site/src/components/Header.astro` — add Konzepte/Streitfragen nav links

### Files to Create (prototype archival)
- `~/Projects/open-legal-commentary/README.md` — archival notice

---

## Task 1: Add BGFA to Site Infrastructure

**Files:**
- Modify: `site/src/lib/laws.ts:139` (after VwVG entry)
- Modify: `site/src/pages/[lang]/[law]/[article].astro:15` (laws array)
- Modify: `site/src/pages/[lang]/[law]/index.astro:13` (laws array)

- [ ] **Step 1: Add BGFA to LAWS array in laws.ts**

Add after the VwVG entry (line 138):

```typescript
  {
    abbr: 'BGFA',
    sr: '935.61',
    name: {
      de: 'Anwaltsgesetz',
      fr: 'Loi sur les avocats',
      it: 'Legge sugli avvocati',
      en: 'Lawyers Act',
    },
    description: {
      de: 'Freizügigkeit, Berufsregeln, Berufsgeheimnis, Disziplinaraufsicht',
      fr: 'Libre circulation, règles professionnelles, secret professionnel, surveillance disciplinaire',
      it: 'Libera circolazione, regole professionali, segreto professionale, vigilanza disciplinare',
      en: 'Freedom of movement, professional rules, professional secret, disciplinary supervision',
    },
  },
```

- [ ] **Step 2: Add 'bgfa' to article page getStaticPaths**

In `site/src/pages/[lang]/[law]/[article].astro`, line 15, change:
```typescript
const laws = ['bv', 'zgb', 'or', 'zpo', 'stgb', 'stpo', 'schkg', 'vwvg'];
```
to:
```typescript
const laws = ['bv', 'zgb', 'or', 'zpo', 'stgb', 'stpo', 'schkg', 'vwvg', 'bgfa'];
```

- [ ] **Step 3: Add 'bgfa' to law index page getStaticPaths**

In `site/src/pages/[lang]/[law]/index.astro`, line 13, change:
```typescript
const laws = ['bv', 'zgb', 'or', 'zpo', 'stgb', 'stpo', 'schkg', 'vwvg'];
```
to:
```typescript
const laws = ['bv', 'zgb', 'or', 'zpo', 'stgb', 'stpo', 'schkg', 'vwvg', 'bgfa'];
```

- [ ] **Step 4: Verify site builds**

Run: `cd /Users/jonashertner/Projects/openlegalcommentary/site && npm run build`
Expected: Build succeeds. BGFA law pages are generated (38 article pages × 4 langs = 152 pages).

- [ ] **Step 5: Commit**

```bash
git add site/src/lib/laws.ts site/src/pages/\[lang\]/\[law\]/\[article\].astro site/src/pages/\[lang\]/\[law\]/index.astro
git commit -m "feat(site): add BGFA to law registry and route generation"
```

---

## Task 2: Generate BGFA Art. 12 Commentary

**Files:**
- Create: `content/bgfa/art-012/summary.md`
- Create: `content/bgfa/art-012/doctrine.md`
- Create: `content/bgfa/art-012/caselaw.md`
- Modify: `content/bgfa/art-012/meta.yaml`

Use the opencaselaw MCP tools to research current BGE decisions. Consult:
- `guidelines/global.md` for layer specifications (summary: B1, 150-300 words; doctrine: Randziffern N.1+, Pflichtsektionen; caselaw: grouped by theme)
- `guidelines/bgfa.md` for BGFA-specific context
- The prototype draft at `~/Projects/open-legal-commentary/commentary/provisions/bgfa-art-12.md` for analytical framework (do NOT copy verbatim — rewrite in OLC format)
- `content/bv/art-027/summary.md`, `doctrine.md`, `caselaw.md` as format exemplars

Key BGE decisions to include (verify via opencaselaw):
- **BGE 130 II 270** — independence, three dimensions
- **BGE 131 IV 154** — Sorgfaltspflicht
- **BGE 136 III 296** — advertising rules
- **BGE 140 II 102** — cantonal limitation

Key literature:
- BSK BGFA: Fellmann/Zindel, 2. Aufl. 2019
- Nater/Zindel, Kommentar zum Anwaltsgesetz, 2020
- BBl 1999 6013 (Botschaft)

- [ ] **Step 1: Research via opencaselaw MCP**

Use `get_doctrine` for BGFA Art. 12 to get leading cases and doctrine.
Use `search_decisions` for additional relevant BGE.
Use `get_law` for the current statutory text of Art. 12 BGFA.

- [ ] **Step 2: Write summary.md**

Create `content/bgfa/art-012/summary.md` following `guidelines/global.md` Ebene 1 spec:
- German B1 level
- 150–300 words
- Must cover: Was regelt die Norm? Wer ist betroffen? Was sind die Rechtsfolgen? Konkretes Beispiel.
- No citations, no Randziffern
- Max sentence length: 25 words

Structure the summary around: Art. 12 BGFA lists 10 professional rules (lit. a–j) binding all registered lawyers. Cover diligence (lit. a), independence (lit. b), conflict avoidance (lit. c), advertising (lit. d), and the practical consequences of violation (→ Art. 17 BGFA disciplinary measures).

- [ ] **Step 3: Write doctrine.md**

Create `content/bgfa/art-012/doctrine.md` following `guidelines/global.md` Ebene 2 spec:
- Randziffern as **N. 1**, **N. 2** etc.
- Pflichtsektionen: Entstehungsgeschichte, Systematische Einordnung, Tatbestandsmerkmale/Norminhalt, Rechtsfolgen, Streitstände, Praxishinweise
- Minimum 3 secondary sources
- Must cite the Botschaft (BBl 1999 6013)
- Querverweise with → and ↔ notation
- BSK citations: Fellmann, BSK BGFA, Art. 12 N. X
- Own analysis citing specific positions, no paraphrasing

Content must cover all 10 literals (a–j) with emphasis on:
- Lit. a (Sorgfalt): BGE 131 IV 154
- Lit. b (Unabhängigkeit): BGE 130 II 270 — three dimensions
- Lit. c (Interessenkonflikt): case law on Doppelvertretung
- Lit. d (Werbung): BGE 136 III 296 — scholarship vs. advertising distinction
- Relationship to Art. 8 BGFA (persönliche Voraussetzungen — Unabhängigkeit as both entry requirement and ongoing duty)
- The open-source question: Art. 12 presents no categorical obstacle (see ↔ contested page)

- [ ] **Step 4: Write caselaw.md**

Create `content/bgfa/art-012/caselaw.md` following `guidelines/global.md` Ebene 3 spec:
- Grouped by theme, within theme by importance then chronologically
- Per decision: **BGE reference** bold, date, Leitsatz 1-2 sentences, relevance 1 sentence, blockquote of decisive passage
- Use all BGE available via opencaselaw

Themes:
1. Sorgfaltspflicht (lit. a)
2. Unabhängigkeit (lit. b)
3. Interessenkonflikte (lit. c)
4. Werbung (lit. d)
5. Disziplinarmassnahmen (→ Art. 17)

- [ ] **Step 5: Update meta.yaml**

Update `content/bgfa/art-012/meta.yaml` to add layer metadata:

```yaml
law: BGFA
article: 12
article_suffix: ''
title: Berufsregeln
sr_number: '935.61'
absatz_count: 1
fedlex_url: https://www.fedlex.admin.ch/eli/cc/2002/153/de#art_12
lexfind_url: ''
in_force_since: ''
layers:
  summary:
    last_generated: '2026-04-06'
    version: 1
  doctrine:
    last_generated: '2026-04-06'
    version: 1
  caselaw:
    last_generated: '2026-04-06'
    version: 1
```

- [ ] **Step 6: Commit**

```bash
git add content/bgfa/art-012/
git commit -m "content(bgfa): add Art. 12 commentary — Berufsregeln (summary, doctrine, caselaw)"
```

---

## Task 3: Generate BGFA Art. 13 Commentary

**Files:**
- Create: `content/bgfa/art-013/summary.md`
- Create: `content/bgfa/art-013/doctrine.md`
- Create: `content/bgfa/art-013/caselaw.md`
- Modify: `content/bgfa/art-013/meta.yaml`

Same approach as Task 2. Consult:
- The prototype draft at `~/Projects/open-legal-commentary/commentary/provisions/bgfa-art-13.md`
- `content/concepts/berufsgeheimnis/content.md` for the cross-cutting concept analysis

Key BGE decisions:
- **BGE 130 II 193** — scope of privilege, Tatsache des Mandats
- **BGE 117 Ia 341** — Durchsuchung, Entsiegelungsverfahren
- **BGE 112 Ib 606** — distinction: client-entrusted vs. independently developed information
- **BGE 145 II 229** — in-house counsel (Unternehmensanwalt), narrower scope
- **BGE 143 IV 462** — testimony rights

Key literature:
- BSK BGFA: Fellmann/Zindel, Art. 13 N. 1 ff.
- Nater/Zindel, Kommentar zum Anwaltsgesetz, Art. 13
- BBl 1999 6013

- [ ] **Step 1: Research via opencaselaw MCP**

Use `get_doctrine` for BGFA Art. 13.
Use `get_decision` or `get_case_brief` for each key BGE.
Use `get_law` for statutory text.

- [ ] **Step 2: Write summary.md**

150-300 words, B1 level. Cover:
- What Art. 13 protects (lawyer's professional secret)
- Three scope dimensions: temporal (unlimited), personal (against everyone), material (everything entrusted by clients)
- Duty extends to auxiliary persons (Abs. 2)
- Waiver possible but does not compel disclosure
- Concrete example: A client tells their lawyer about a business problem. The lawyer may not share this information with anyone, not even after the case is over.

- [ ] **Step 3: Write doctrine.md**

Randziffern, Pflichtsektionen. Key content:
- Entstehungsgeschichte: BBl 1999 6013, relationship to pre-existing cantonal rules
- Systematische Einordnung: position within BGFA, relationship to Art. 321 StGB, Art. 171 StPO, Art. 160 ZPO, Art. 13 BV
- Tatbestandsmerkmale: Three-dimensional scope analysis (temporal, personal, material). The critical "anvertraut" analysis.
- Three-category taxonomy (client-specific, methodology, anonymised patterns) — reference → contested page
- Abs. 2: Hilfspersonen duty
- Waiver (Entbindung): informed, voluntary, specific; does not compel
- Rechtsfolgen: Art. 321 StGB criminal liability, Art. 17 BGFA disciplinary, procedural protections
- Streitstände: scope of "anvertraut" (→ contested page open-methodology-bgfa), in-house counsel scope, internal investigations
- Praxishinweise: practical guidance on what can and cannot be shared

- [ ] **Step 4: Write caselaw.md**

Themes:
1. Sachlicher Geltungsbereich (material scope): BGE 130 II 193, BGE 112 Ib 606
2. Durchsuchung und Beschlagnahme: BGE 117 Ia 341
3. Unternehmensanwälte: BGE 145 II 229
4. Zeugnisverweigerung: BGE 143 IV 462
5. Waiver und Grenzen

- [ ] **Step 5: Update meta.yaml**

Same structure as Task 2, Step 5, but for Art. 13.

- [ ] **Step 6: Commit**

```bash
git add content/bgfa/art-013/
git commit -m "content(bgfa): add Art. 13 commentary — Berufsgeheimnis (summary, doctrine, caselaw)"
```

---

## Task 4: Add Concept/Contested Content Loading to Site Library

**Files:**
- Modify: `site/src/lib/content.ts`

- [ ] **Step 1: Add concept loading functions**

Add these functions at the end of `site/src/lib/content.ts`:

```typescript
// ── Concept pages ──────────────────────────────────────────────
export interface ConceptMeta {
  type: 'concept';
  slug: string;
  title: string;
  provisions: string[];
  confidence: 'settled' | 'contested' | 'evolving';
  author_status: 'draft' | 'reviewed' | 'contested';
  tags: string[];
  last_generated: string;
  quality_score: number | null;
}

export interface ConceptPage {
  meta: ConceptMeta;
  content: string;
  slug: string;
}

export function listConcepts(): ConceptPage[] {
  const conceptsDir = path.join(CONTENT_ROOT, 'concepts');
  try {
    const entries = fs.readdirSync(conceptsDir, { withFileTypes: true });
    return entries
      .filter((e) => e.isDirectory())
      .map((e) => {
        const metaPath = path.join(conceptsDir, e.name, 'meta.yaml');
        const contentPath = path.join(conceptsDir, e.name, 'content.md');
        try {
          const meta = yaml.load(fs.readFileSync(metaPath, 'utf-8')) as ConceptMeta;
          const content = readFileIfExists(contentPath);
          return { meta, content, slug: e.name };
        } catch {
          return null;
        }
      })
      .filter((c): c is ConceptPage => c !== null);
}

export function loadConcept(slug: string): ConceptPage | null {
  const dir = path.join(CONTENT_ROOT, 'concepts', slug);
  if (!fs.existsSync(dir)) return null;
  try {
    const meta = yaml.load(fs.readFileSync(path.join(dir, 'meta.yaml'), 'utf-8')) as ConceptMeta;
    const content = readFileIfExists(path.join(dir, 'content.md'));
    return { meta, content, slug };
  } catch {
    return null;
  }
}

// ── Contested pages ──────────────────────────────────────────────
export interface ContestedPosition {
  label: string;
  summary: string;
}

export interface ContestedMeta {
  type: 'contested';
  slug: string;
  title: string;
  question: string;
  provisions: string[];
  positions: ContestedPosition[];
  author_status: 'draft' | 'reviewed' | 'contested';
  tags: string[];
  last_generated: string;
}

export interface ContestedPage {
  meta: ContestedMeta;
  content: string;
  slug: string;
}

export function listContested(): ContestedPage[] {
  const contestedDir = path.join(CONTENT_ROOT, 'contested');
  try {
    const entries = fs.readdirSync(contestedDir, { withFileTypes: true });
    return entries
      .filter((e) => e.isDirectory())
      .map((e) => {
        const metaPath = path.join(contestedDir, e.name, 'meta.yaml');
        const contentPath = path.join(contestedDir, e.name, 'content.md');
        try {
          const meta = yaml.load(fs.readFileSync(metaPath, 'utf-8')) as ContestedMeta;
          const content = readFileIfExists(contentPath);
          return { meta, content, slug: e.name };
        } catch {
          return null;
        }
      })
      .filter((c): c is ContestedPage => c !== null);
}

export function loadContested(slug: string): ContestedPage | null {
  const dir = path.join(CONTENT_ROOT, 'contested', slug);
  if (!fs.existsSync(dir)) return null;
  try {
    const meta = yaml.load(fs.readFileSync(path.join(dir, 'meta.yaml'), 'utf-8')) as ContestedMeta;
    const content = readFileIfExists(path.join(dir, 'content.md'));
    return { meta, content, slug };
  } catch {
    return null;
  }
}

// ── Cross-references ──────────────────────────────────────────────
export interface CrossRef {
  type: 'concept' | 'contested';
  slug: string;
  title: string;
}

export function getCrossReferences(law: string, articleDirName: string): CrossRef[] {
  const provisionKey = `${law.toLowerCase()}/${articleDirName}`;
  const refs: CrossRef[] = [];

  for (const concept of listConcepts()) {
    if (concept.meta.provisions.some((p) => p === provisionKey)) {
      refs.push({ type: 'concept', slug: concept.slug, title: concept.meta.title });
    }
  }

  for (const contested of listContested()) {
    if (contested.meta.provisions.some((p) => p === provisionKey)) {
      refs.push({ type: 'contested', slug: contested.slug, title: contested.meta.title });
    }
  }

  return refs;
}
```

- [ ] **Step 2: Verify TypeScript compiles**

Run: `cd /Users/jonashertner/Projects/openlegalcommentary/site && npx tsc --noEmit`
Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add site/src/lib/content.ts
git commit -m "feat(site): add concept, contested, and cross-reference loading functions"
```

---

## Task 5: Add i18n Keys for New Content Types and Navigation

**Files:**
- Modify: `site/src/lib/i18n.ts`

- [ ] **Step 1: Add i18n translations**

Add these entries to the `translations` object in `site/src/lib/i18n.ts`, before the closing `};`:

```typescript
  // Concepts
  'nav.concepts': { de: 'Konzepte', fr: 'Concepts', it: 'Concetti', en: 'Concepts' },
  'concepts.title': { de: 'Konzepte', fr: 'Concepts', it: 'Concetti', en: 'Concepts' },
  'concepts.subtitle': { de: 'Rechtskonzepte über Gesetzesgrenzen hinweg', fr: 'Concepts juridiques transversaux', it: 'Concetti giuridici trasversali', en: 'Cross-cutting legal concepts' },
  'concepts.confidence': { de: 'Doktrineller Status', fr: 'Statut doctrinal', it: 'Stato dottrinale', en: 'Doctrinal status' },
  'concepts.settled': { de: 'Gefestigt', fr: 'Établi', it: 'Consolidato', en: 'Settled' },
  'concepts.contested': { de: 'Umstritten', fr: 'Contesté', it: 'Contestato', en: 'Contested' },
  'concepts.evolving': { de: 'In Entwicklung', fr: 'En évolution', it: 'In evoluzione', en: 'Evolving' },
  'concepts.provisions': { de: 'Betroffene Bestimmungen', fr: 'Dispositions concernées', it: 'Disposizioni interessate', en: 'Related provisions' },

  // Contested
  'nav.contested': { de: 'Streitfragen', fr: 'Questions disputées', it: 'Questioni controverse', en: 'Disputed Questions' },
  'contested.title': { de: 'Streitfragen', fr: 'Questions disputées', it: 'Questioni controverse', en: 'Disputed Questions' },
  'contested.subtitle': { de: 'Wo vernünftige Juristinnen und Juristen uneins sind', fr: 'Où les juristes raisonnables divergent', it: 'Dove i giuristi ragionevoli divergono', en: 'Where reasonable jurists disagree' },
  'contested.question': { de: 'Die Frage', fr: 'La question', it: 'La questione', en: 'The question' },
  'contested.positions': { de: 'Positionen', fr: 'Positions', it: 'Posizioni', en: 'Positions' },

  // Cross-references
  'crossref.title': { de: 'Querverweise', fr: 'Références croisées', it: 'Riferimenti incrociati', en: 'Cross-references' },
  'crossref.concepts': { de: 'Konzepte', fr: 'Concepts', it: 'Concetti', en: 'Concepts' },
  'crossref.contested': { de: 'Streitfragen', fr: 'Questions disputées', it: 'Questioni controverse', en: 'Disputed Questions' },
```

- [ ] **Step 2: Commit**

```bash
git add site/src/lib/i18n.ts
git commit -m "feat(site): add i18n keys for concepts, contested, and cross-references"
```

---

## Task 6: Create Concept Page Routes

**Files:**
- Create: `site/src/pages/[lang]/concepts/[slug].astro`
- Create: `site/src/pages/[lang]/concepts/index.astro`

- [ ] **Step 1: Create concept detail page**

Create `site/src/pages/[lang]/concepts/[slug].astro`:

```astro
---
import { LANGS, type Lang, t } from '@/lib/i18n';
import { langBase } from '@/lib/base';
import { renderMarkdown } from '@/lib/markdown';
import Base from '../../../layouts/Base.astro';
import Breadcrumb from '../../../components/Breadcrumb.astro';
import { listConcepts, loadConcept } from '../../../lib/content';

export function getStaticPaths() {
  const concepts = listConcepts();
  return LANGS.flatMap(lang =>
    concepts.map(c => ({ params: { lang, slug: c.slug } }))
  );
}

const { lang, slug } = Astro.params as { lang: Lang; slug: string };
const concept = loadConcept(slug!);
if (!concept) return Astro.redirect(`/${lang}/concepts`);

const { html: contentHtml, toc } = renderMarkdown(concept.content, lang);

const confidenceLabels: Record<string, string> = {
  settled: t('concepts.settled', lang),
  contested: t('concepts.contested', lang),
  evolving: t('concepts.evolving', lang),
};

function provisionToLink(prov: string): { href: string; label: string } {
  const [law, art] = prov.split('/');
  const num = art.replace('art-', '').replace(/^0+/, '');
  return {
    href: `${langBase(lang)}/${law}/art-${num}`,
    label: `Art. ${num} ${law.toUpperCase()}`,
  };
}
---

<Base title={concept.meta.title} lang={lang} pagePath={`/concepts/${slug}`}>
  <Breadcrumb
    lang={lang}
    items={[
      { label: t('nav.concepts', lang), href: `${langBase(lang)}/concepts` },
      { label: concept.meta.title },
    ]}
  />

  <article class="concept-page content-column" data-pagefind-body data-pagefind-filter={`language:${lang}`}>
    <header class="concept-header">
      <h1>{concept.meta.title}</h1>
      <div class="concept-meta text-sm">
        <span class:list={['confidence-badge', `confidence-${concept.meta.confidence}`]}>
          {confidenceLabels[concept.meta.confidence]}
        </span>
        <span class="author-status text-muted">{concept.meta.author_status}</span>
      </div>
    </header>

    <div class="concept-provisions">
      <h2 class="text-sm font-heading">{t('concepts.provisions', lang)}</h2>
      <ul class="provision-links">
        {concept.meta.provisions.map(prov => {
          const link = provisionToLink(prov);
          return <li><a href={link.href}>{link.label}</a></li>;
        })}
      </ul>
    </div>

    <div class="concept-content prose" set:html={contentHtml} />
  </article>
</Base>

<style>
  .concept-page {
    padding-top: var(--space-2);
  }

  .concept-header {
    margin-bottom: var(--space-3);
    padding-bottom: var(--space-2);
    border-bottom: 1px solid var(--color-border-light);
  }

  .concept-header h1 {
    margin-bottom: var(--space-1);
  }

  .concept-meta {
    display: flex;
    gap: var(--space-2);
    align-items: center;
  }

  .confidence-badge {
    font-family: var(--font-heading);
    font-size: var(--text-xs);
    font-weight: 600;
    padding: 2px 8px;
    border-radius: var(--radius-sm);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .confidence-settled {
    background: color-mix(in srgb, var(--color-accent) 15%, transparent);
    color: var(--color-accent);
  }

  .confidence-contested {
    background: color-mix(in srgb, #d97706 15%, transparent);
    color: #d97706;
  }

  .confidence-evolving {
    background: color-mix(in srgb, #6366f1 15%, transparent);
    color: #6366f1;
  }

  .concept-provisions {
    margin-bottom: var(--space-4);
    padding: var(--space-2) var(--space-3);
    background: var(--color-bg-alt);
    border-radius: var(--radius-md);
  }

  .concept-provisions h2 {
    margin: 0 0 var(--space-1);
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .provision-links {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-1);
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .provision-links a {
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    color: var(--color-accent);
    text-decoration: none;
    padding: 2px 8px;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    transition: border-color var(--transition-fast), background var(--transition-fast);
  }

  .provision-links a:hover {
    border-color: var(--color-accent);
    background: color-mix(in srgb, var(--color-accent) 8%, transparent);
  }

  .concept-content {
    line-height: 1.7;
  }
</style>
```

- [ ] **Step 2: Create concept index page**

Create `site/src/pages/[lang]/concepts/index.astro`:

```astro
---
import { LANGS, type Lang, t } from '@/lib/i18n';
import { langBase } from '@/lib/base';
import Base from '../../../layouts/Base.astro';
import Breadcrumb from '../../../components/Breadcrumb.astro';
import { listConcepts } from '../../../lib/content';

export function getStaticPaths() {
  return LANGS.map(lang => ({ params: { lang } }));
}

const { lang } = Astro.params as { lang: Lang };
const concepts = listConcepts();

const confidenceLabels: Record<string, string> = {
  settled: t('concepts.settled', lang),
  contested: t('concepts.contested', lang),
  evolving: t('concepts.evolving', lang),
};
---

<Base title={t('concepts.title', lang)} lang={lang} pagePath="/concepts">
  <Breadcrumb lang={lang} items={[{ label: t('nav.concepts', lang) }]} />

  <header class="page-header">
    <h1>{t('concepts.title', lang)}</h1>
    <p class="text-secondary">{t('concepts.subtitle', lang)}</p>
  </header>

  <section class="concepts-list">
    {concepts.map(concept => (
      <a href={`${langBase(lang)}/concepts/${concept.slug}`} class="concept-card">
        <div class="concept-card-top">
          <h2>{concept.meta.title}</h2>
          <span class:list={['confidence-badge', `confidence-${concept.meta.confidence}`]}>
            {confidenceLabels[concept.meta.confidence]}
          </span>
        </div>
        <div class="concept-card-tags text-xs text-muted">
          {concept.meta.provisions.length} {t('concepts.provisions', lang).toLowerCase()}
        </div>
      </a>
    ))}
  </section>
</Base>

<style>
  .page-header {
    margin-bottom: var(--space-4);
    padding-bottom: var(--space-3);
    border-bottom: 1px solid var(--color-border-light);
  }

  .page-header h1 {
    margin-bottom: var(--space-1);
  }

  .concepts-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .concept-card {
    display: block;
    padding: var(--space-3);
    background: var(--color-bg-card);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    text-decoration: none;
    color: var(--color-text);
    transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
  }

  .concept-card:hover {
    border-color: var(--color-accent);
    box-shadow: var(--shadow-md);
  }

  .concept-card-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--space-2);
  }

  .concept-card-top h2 {
    font-size: var(--text-md);
    margin: 0;
  }

  .confidence-badge {
    font-family: var(--font-heading);
    font-size: var(--text-xs);
    font-weight: 600;
    padding: 2px 8px;
    border-radius: var(--radius-sm);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    flex-shrink: 0;
  }

  .confidence-settled {
    background: color-mix(in srgb, var(--color-accent) 15%, transparent);
    color: var(--color-accent);
  }

  .confidence-contested {
    background: color-mix(in srgb, #d97706 15%, transparent);
    color: #d97706;
  }

  .confidence-evolving {
    background: color-mix(in srgb, #6366f1 15%, transparent);
    color: #6366f1;
  }

  .concept-card-tags {
    margin-top: var(--space-1);
  }
</style>
```

- [ ] **Step 3: Verify build**

Run: `cd /Users/jonashertner/Projects/openlegalcommentary/site && npm run build`
Expected: Build succeeds, concept pages generated at `/de/concepts/`, `/de/concepts/berufsgeheimnis/`, etc.

- [ ] **Step 4: Commit**

```bash
git add site/src/pages/\[lang\]/concepts/
git commit -m "feat(site): add concept page routes (index + detail)"
```

---

## Task 7: Create Contested Page Routes

**Files:**
- Create: `site/src/pages/[lang]/contested/[slug].astro`
- Create: `site/src/pages/[lang]/contested/index.astro`

- [ ] **Step 1: Create contested detail page**

Create `site/src/pages/[lang]/contested/[slug].astro`:

```astro
---
import { LANGS, type Lang, t } from '@/lib/i18n';
import { langBase } from '@/lib/base';
import { renderMarkdown } from '@/lib/markdown';
import Base from '../../../layouts/Base.astro';
import Breadcrumb from '../../../components/Breadcrumb.astro';
import { listContested, loadContested } from '../../../lib/content';

export function getStaticPaths() {
  const pages = listContested();
  return LANGS.flatMap(lang =>
    pages.map(p => ({ params: { lang, slug: p.slug } }))
  );
}

const { lang, slug } = Astro.params as { lang: Lang; slug: string };
const page = loadContested(slug!);
if (!page) return Astro.redirect(`/${lang}/contested`);

const { html: contentHtml } = renderMarkdown(page.content, lang);

function provisionToLink(prov: string): { href: string; label: string } {
  const [law, art] = prov.split('/');
  const num = art.replace('art-', '').replace(/^0+/, '');
  return {
    href: `${langBase(lang)}/${law}/art-${num}`,
    label: `Art. ${num} ${law.toUpperCase()}`,
  };
}
---

<Base title={page.meta.title} lang={lang} pagePath={`/contested/${slug}`}>
  <Breadcrumb
    lang={lang}
    items={[
      { label: t('nav.contested', lang), href: `${langBase(lang)}/contested` },
      { label: page.meta.title },
    ]}
  />

  <article class="contested-page content-column" data-pagefind-body data-pagefind-filter={`language:${lang}`}>
    <header class="contested-header">
      <h1>{page.meta.title}</h1>
      <span class="author-status text-sm text-muted">{page.meta.author_status}</span>
    </header>

    <div class="contested-question">
      <h2 class="text-sm font-heading text-muted">{t('contested.question', lang)}</h2>
      <p class="question-text">{page.meta.question}</p>
    </div>

    <div class="contested-positions">
      <h2 class="text-sm font-heading text-muted">{t('contested.positions', lang)}</h2>
      <div class="positions-grid">
        {page.meta.positions.map((pos, i) => (
          <div class="position-card">
            <div class="position-label">
              <span class="position-letter">{String.fromCharCode(65 + i)}</span>
              {pos.label}
            </div>
            <p class="position-summary">{pos.summary}</p>
          </div>
        ))}
      </div>
    </div>

    <div class="contested-provisions">
      <h2 class="text-sm font-heading text-muted">{t('concepts.provisions', lang)}</h2>
      <ul class="provision-links">
        {page.meta.provisions.map(prov => {
          const link = provisionToLink(prov);
          return <li><a href={link.href}>{link.label}</a></li>;
        })}
      </ul>
    </div>

    <div class="contested-content prose" set:html={contentHtml} />
  </article>
</Base>

<style>
  .contested-page {
    padding-top: var(--space-2);
  }

  .contested-header {
    margin-bottom: var(--space-3);
    padding-bottom: var(--space-2);
    border-bottom: 1px solid var(--color-border-light);
  }

  .contested-header h1 {
    margin-bottom: var(--space-1);
  }

  .contested-question {
    margin-bottom: var(--space-3);
    padding: var(--space-3);
    background: color-mix(in srgb, #d97706 8%, transparent);
    border-left: 3px solid #d97706;
    border-radius: 0 var(--radius-md) var(--radius-md) 0;
  }

  .contested-question h2 {
    margin: 0 0 var(--space-1);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .question-text {
    font-size: var(--text-md);
    font-style: italic;
    margin: 0;
    line-height: 1.6;
  }

  .contested-positions {
    margin-bottom: var(--space-3);
  }

  .contested-positions h2 {
    margin: 0 0 var(--space-2);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .positions-grid {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .position-card {
    padding: var(--space-2) var(--space-3);
    background: var(--color-bg-card);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
  }

  .position-label {
    font-family: var(--font-heading);
    font-weight: 600;
    font-size: var(--text-sm);
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: var(--space-1);
  }

  .position-letter {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    background: var(--color-bg-alt);
    border-radius: 50%;
    font-size: var(--text-xs);
    font-weight: 700;
    color: var(--color-text-muted);
    flex-shrink: 0;
  }

  .position-summary {
    font-size: var(--text-sm);
    color: var(--color-text-secondary);
    margin: 0;
    line-height: 1.5;
  }

  .contested-provisions {
    margin-bottom: var(--space-4);
    padding: var(--space-2) var(--space-3);
    background: var(--color-bg-alt);
    border-radius: var(--radius-md);
  }

  .contested-provisions h2 {
    margin: 0 0 var(--space-1);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .provision-links {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-1);
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .provision-links a {
    font-family: var(--font-mono);
    font-size: var(--text-xs);
    color: var(--color-accent);
    text-decoration: none;
    padding: 2px 8px;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    transition: border-color var(--transition-fast), background var(--transition-fast);
  }

  .provision-links a:hover {
    border-color: var(--color-accent);
    background: color-mix(in srgb, var(--color-accent) 8%, transparent);
  }

  .contested-content {
    line-height: 1.7;
  }
</style>
```

- [ ] **Step 2: Create contested index page**

Create `site/src/pages/[lang]/contested/index.astro`:

```astro
---
import { LANGS, type Lang, t } from '@/lib/i18n';
import { langBase } from '@/lib/base';
import Base from '../../../layouts/Base.astro';
import Breadcrumb from '../../../components/Breadcrumb.astro';
import { listContested } from '../../../lib/content';

export function getStaticPaths() {
  return LANGS.map(lang => ({ params: { lang } }));
}

const { lang } = Astro.params as { lang: Lang };
const pages = listContested();
---

<Base title={t('contested.title', lang)} lang={lang} pagePath="/contested">
  <Breadcrumb lang={lang} items={[{ label: t('nav.contested', lang) }]} />

  <header class="page-header">
    <h1>{t('contested.title', lang)}</h1>
    <p class="text-secondary">{t('contested.subtitle', lang)}</p>
  </header>

  <section class="contested-list">
    {pages.map(page => (
      <a href={`${langBase(lang)}/contested/${page.slug}`} class="contested-card">
        <h2>{page.meta.title}</h2>
        <p class="contested-card-question">{page.meta.question}</p>
        <div class="contested-card-positions text-xs text-muted">
          {page.meta.positions.length} {t('contested.positions', lang).toLowerCase()}
        </div>
      </a>
    ))}
  </section>
</Base>

<style>
  .page-header {
    margin-bottom: var(--space-4);
    padding-bottom: var(--space-3);
    border-bottom: 1px solid var(--color-border-light);
  }

  .page-header h1 {
    margin-bottom: var(--space-1);
  }

  .contested-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
  }

  .contested-card {
    display: block;
    padding: var(--space-3);
    background: var(--color-bg-card);
    border: 1px solid var(--color-border);
    border-left: 3px solid #d97706;
    border-radius: var(--radius-md);
    text-decoration: none;
    color: var(--color-text);
    transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
  }

  .contested-card:hover {
    border-color: var(--color-accent);
    border-left-color: #d97706;
    box-shadow: var(--shadow-md);
  }

  .contested-card h2 {
    font-size: var(--text-md);
    margin: 0 0 var(--space-1);
  }

  .contested-card-question {
    font-size: var(--text-sm);
    color: var(--color-text-secondary);
    margin: 0 0 var(--space-1);
    line-height: 1.5;
  }
</style>
```

- [ ] **Step 3: Verify build**

Run: `cd /Users/jonashertner/Projects/openlegalcommentary/site && npm run build`
Expected: Build succeeds, contested pages generated.

- [ ] **Step 4: Commit**

```bash
git add site/src/pages/\[lang\]/contested/
git commit -m "feat(site): add contested question page routes (index + detail)"
```

---

## Task 8: Add Cross-Reference Sidebar to Article Pages

**Files:**
- Create: `site/src/components/CrossReferences.astro`
- Modify: `site/src/pages/[lang]/[law]/[article].astro`

- [ ] **Step 1: Create CrossReferences component**

Create `site/src/components/CrossReferences.astro`:

```astro
---
import { type Lang, t } from '@/lib/i18n';
import { langBase } from '@/lib/base';
import type { CrossRef } from '../lib/content';

export interface Props {
  lang: Lang;
  refs: CrossRef[];
}

const { lang, refs } = Astro.props;
const conceptRefs = refs.filter(r => r.type === 'concept');
const contestedRefs = refs.filter(r => r.type === 'contested');
---

{refs.length > 0 && (
  <aside class="cross-references">
    <h2 class="crossref-heading">{t('crossref.title', lang)}</h2>

    {conceptRefs.length > 0 && (
      <div class="crossref-group">
        <h3 class="crossref-label">{t('crossref.concepts', lang)}</h3>
        <ul>
          {conceptRefs.map(ref => (
            <li>
              <a href={`${langBase(lang)}/concepts/${ref.slug}`}>{ref.title}</a>
            </li>
          ))}
        </ul>
      </div>
    )}

    {contestedRefs.length > 0 && (
      <div class="crossref-group">
        <h3 class="crossref-label">{t('crossref.contested', lang)}</h3>
        <ul>
          {contestedRefs.map(ref => (
            <li>
              <a href={`${langBase(lang)}/contested/${ref.slug}`}>{ref.title}</a>
            </li>
          ))}
        </ul>
      </div>
    )}
  </aside>
)}

<style>
  .cross-references {
    margin-top: var(--space-4);
    padding: var(--space-3);
    background: var(--color-bg-alt);
    border-radius: var(--radius-md);
    border: 1px solid var(--color-border-light);
  }

  .crossref-heading {
    font-size: var(--text-sm);
    font-weight: 700;
    margin: 0 0 var(--space-2);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-text-muted);
  }

  .crossref-group {
    margin-bottom: var(--space-2);
  }

  .crossref-group:last-child {
    margin-bottom: 0;
  }

  .crossref-label {
    font-size: var(--text-xs);
    font-weight: 600;
    color: var(--color-text-muted);
    margin: 0 0 4px;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .crossref-group ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .crossref-group li {
    margin-bottom: 2px;
  }

  .crossref-group a {
    font-size: var(--text-sm);
    color: var(--color-accent);
    text-decoration: none;
    padding: 2px 0;
    display: inline-block;
    transition: color var(--transition-fast);
  }

  .crossref-group a:hover {
    text-decoration: underline;
  }
</style>
```

- [ ] **Step 2: Import and use CrossReferences in article page**

In `site/src/pages/[lang]/[law]/[article].astro`:

Add import (after existing imports, around line 10):
```typescript
import CrossReferences from '../../../components/CrossReferences.astro';
import { getCrossReferences } from '../../../lib/content';
```

Add cross-reference lookup (after `const nav = ...`, around line 49):
```typescript
const crossRefs = getCrossReferences(lawInfo.abbr, dirName);
```

Add the component in the template, after `<ArticlePagination ... />` (around line 175):
```astro
    <CrossReferences lang={lang} refs={crossRefs} />
```

- [ ] **Step 3: Verify build**

Run: `cd /Users/jonashertner/Projects/openlegalcommentary/site && npm run build`
Expected: Build succeeds. Article pages for provisions referenced in concept/contested meta.yaml show cross-references.

- [ ] **Step 4: Commit**

```bash
git add site/src/components/CrossReferences.astro site/src/pages/\[lang\]/\[law\]/\[article\].astro
git commit -m "feat(site): add cross-reference sidebar linking articles to concepts and contested questions"
```

---

## Task 9: Update Homepage and Navigation

**Files:**
- Modify: `site/src/pages/[lang]/index.astro`
- Modify: `site/src/components/Header.astro`

- [ ] **Step 1: Update homepage to include BGFA**

In `site/src/pages/[lang]/index.astro`, the homepage currently shows BV as featured and all others as "forthcoming" (non-clickable cards at 55% opacity). BGFA is now in the LAWS array, so it will automatically appear in the forthcoming grid. No code change needed for this — but BGFA article pages will work (they'll show "coming soon" until commentary has content, then become clickable).

However, once Art. 12 and 13 commentary is generated (Tasks 2-3), BGFA will have `withContent > 0` and the LawCard will render as a clickable link automatically. Verify this works.

- [ ] **Step 2: Add Konzepte and Streitfragen to navigation**

In `site/src/components/Header.astro`, add nav items after the "Gesetze" link (line 31). Change the nav list to:

```astro
      <ul id="nav-menu" class="nav-list" role="list">
        <li><a href={langHome(lang)} class:list={[{ active: currentPath === '/' || currentPath === langHome(lang) }]}>{t('nav.laws', lang)}</a></li>
        <li><a href={`${langBase(lang)}/concepts`} class:list={[{ active: currentPath.includes('/concepts') }]}>{t('nav.concepts', lang)}</a></li>
        <li><a href={`${langBase(lang)}/contested`} class:list={[{ active: currentPath.includes('/contested') }]}>{t('nav.contested', lang)}</a></li>
        <li><a href={`${langBase(lang)}/about`} class:list={[{ active: currentPath.includes('/about') }]}>{t('nav.about', lang)}</a></li>
        <li><a href={`${langBase(lang)}/methodology`} class:list={[{ active: currentPath.includes('/methodology') }]}>{t('nav.methodology', lang)}</a></li>
        <li><a href={`${langBase(lang)}/changelog`} class:list={[{ active: currentPath.includes('/changelog') }]}>{t('nav.changelog', lang)}</a></li>
        <li class="nav-lang-item">
          <LanguageSwitcher currentLang={lang} pagePath={pagePath} />
        </li>
      </ul>
```

- [ ] **Step 3: Verify build**

Run: `cd /Users/jonashertner/Projects/openlegalcommentary/site && npm run build`
Expected: Build succeeds. Nav shows Konzepte and Streitfragen links.

- [ ] **Step 4: Commit**

```bash
git add site/src/components/Header.astro site/src/pages/\[lang\]/index.astro
git commit -m "feat(site): add Konzepte and Streitfragen to navigation"
```

---

## Task 10: Run Tests and Verify

**Files:** None to create/modify — verification only.

- [ ] **Step 1: Run Python tests**

Run: `cd /Users/jonashertner/Projects/openlegalcommentary && uv run pytest`
Expected: All tests pass. The BGFA addition should be compatible since BGFA is already in `scripts/schema.py` LAWS tuple.

- [ ] **Step 2: Run linter**

Run: `cd /Users/jonashertner/Projects/openlegalcommentary && uv run ruff check .`
Expected: No errors (we didn't modify Python files).

- [ ] **Step 3: Run site build**

Run: `cd /Users/jonashertner/Projects/openlegalcommentary/site && npm run build`
Expected: Build succeeds. Verify output includes:
- `/de/bgfa/` — BGFA law index
- `/de/bgfa/art-12/` — Art. 12 article page
- `/de/bgfa/art-13/` — Art. 13 article page
- `/de/concepts/` — concepts index
- `/de/concepts/berufsgeheimnis/` — concept detail
- `/de/contested/` — contested index
- `/de/contested/open-methodology-bgfa/` — contested detail

- [ ] **Step 4: Spot-check generated HTML**

Run: `cat /Users/jonashertner/Projects/openlegalcommentary/site/dist/de/bgfa/art-12/index.html | head -50`
Expected: Valid HTML with article content.

Run: `cat /Users/jonashertner/Projects/openlegalcommentary/site/dist/de/concepts/berufsgeheimnis/index.html | head -50`
Expected: Valid HTML with concept content.

---

## Task 11: Archive Prototype Repo

**Files:**
- Create: `~/Projects/open-legal-commentary/README.md`

- [ ] **Step 1: Create archival README**

Create `~/Projects/open-legal-commentary/README.md`:

```markdown
# open-legal-commentary (Prototype — Archived)

This repository was a prototype wiki for the Open Legal Commentary project,
using the Karpathy LLM Wiki pattern adapted for legal commentary.

**Status: Archived.** All content has been migrated to the main repository:
https://github.com/jonashertner/openlegalcommentary

## What was migrated

- BGFA Art. 12 and Art. 13 commentary drafts → rewritten as OLC 3-layer commentary
- Berufsgeheimnis concept page → `content/concepts/berufsgeheimnis/`
- Open methodology contested page → `content/contested/open-methodology-bgfa/`
- AGENTS.md schema thinking → informed OLC guidelines

## What was NOT migrated

- Raw statute sources (BV, BGFA) — already available in the main repo via Fedlex
- firm/ and goodboard/ wiki structures — remain as future reference
- The AGENTS.md file itself — preserved here for historical reference

## Date of archival

2026-04-06
```

- [ ] **Step 2: Commit in prototype repo**

```bash
cd ~/Projects/open-legal-commentary
git add README.md
git commit -m "docs: archive notice — content migrated to openlegalcommentary"
```
