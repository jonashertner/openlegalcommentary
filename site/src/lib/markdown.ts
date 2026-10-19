import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkRehype from 'remark-rehype';
import rehypeStringify from 'rehype-stringify';
import rehypeSlug from 'rehype-slug';
import rehypeAutolinkHeadings from 'rehype-autolink-headings';
import { visit } from 'unist-util-visit';
import type { Root as HastRoot, Element, Text, ElementContent } from 'hast';
import { langBase } from './base';
import { t, type Lang } from './i18n';
import { LAWS } from './laws';

export interface TocEntry {
  level: number;
  text: string;
  id: string;
}

// ── Umlaut-aware slugifier matching the old mdToHtml ──────────────
function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[äöüéèêàâîôûç]/g, (c) => {
      const map: Record<string, string> = {
        ä: 'ae', ö: 'oe', ü: 'ue', é: 'e', è: 'e', ê: 'e',
        à: 'a', â: 'a', î: 'i', ô: 'o', û: 'u', ç: 'c',
      };
      return map[c] || c;
    })
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

// ── BGE citation URL builder ──────────────────────────────────────
function bgeUrl(vol: string, part: string, page: string): string {
  const docid = encodeURIComponent(`atf://${vol}-${part}-${page}:de`);
  const query = encodeURIComponent(`BGE ${vol} ${part} ${page}`);
  return `https://search.bger.ch/ext/eurospider/live/de/php/clir/http/index.php?lang=de&type=highlight_simple_query&query_words=${query}&part=all&top_subcollection_clir=bge&highlight_docid=${docid}&azaclir=clir`;
}

// ── rehype plugin: style Randziffern ──────────────────────────────
// Finds <strong>N. X</strong> and wraps in anchor with class
function rehypeRandziffern() {
  return (tree: HastRoot) => {
    visit(tree, 'element', (node: Element, index, parent) => {
      if (node.tagName !== 'strong') return;
      // Check if the only child is a text node matching N. X
      if (node.children.length !== 1 || node.children[0].type !== 'text') return;
      const text = (node.children[0] as Text).value;
      const m = text.match(/^N\.\s*(\d+)$/);
      if (!m) return;
      const num = m[1];
      const label = text;
      // Replace the <strong> with <strong class="randziffer" id="n-X"><a ...>
      node.properties = {
        ...node.properties,
        className: ['randziffer'],
        id: `n-${num}`,
      };
      node.children = [
        {
          type: 'element',
          tagName: 'a',
          properties: {
            href: `#n-${num}`,
            className: ['rz-link'],
            title: label,
          },
          children: [{ type: 'text', value: label }],
        },
      ];
      // A paragraph that opens with its Randziffer gets class "rz" so the
      // number can hang in the margin.
      const p = parent as Element | undefined;
      if (p?.type === 'element' && p.tagName === 'p' && index !== undefined) {
        const before = p.children.slice(0, index);
        if (before.every((c) => c.type === 'text' && !c.value.trim())) {
          const cls = p.properties?.className;
          p.properties = { ...p.properties, className: [...(Array.isArray(cls) ? cls : []), 'rz'] };
        }
      }
    });
  };
}

// ── rehype plugin: link BGE citations ─────────────────────────────
function rehypeBgeCitations() {
  const BGE_RE = /(BGE)\s+(\d+)\s+([IVX]+)\s+(\d+)(\s+E\.\s*[\d.]+)?/g;

  return (tree: HastRoot) => {
    visit(tree, 'text', (node: Text, index, parent) => {
      if (!parent || index === undefined) return;
      // Skip if already inside an <a> tag
      if ((parent as Element).tagName === 'a') return;

      const text = node.value;
      BGE_RE.lastIndex = 0;
      if (!BGE_RE.test(text)) return;

      // Split text around BGE citations and build replacement nodes
      BGE_RE.lastIndex = 0;
      const parts: ElementContent[] = [];
      let lastIndex = 0;
      let match;
      while ((match = BGE_RE.exec(text)) !== null) {
        if (match.index > lastIndex) {
          parts.push({ type: 'text', value: text.slice(lastIndex, match.index) });
        }
        const cite = match[0];
        const [, , vol, romanPart, page] = match;
        const url = bgeUrl(vol, romanPart, page);

        const linkNode: Element = {
          type: 'element',
          tagName: 'a',
          properties: {
            href: url,
            target: '_blank',
            rel: 'noopener',
            className: ['cite-bge'],
          },
          children: [{ type: 'text', value: cite }],
        };
        parts.push(linkNode);
        lastIndex = match.index + cite.length;
      }
      if (lastIndex < text.length) {
        parts.push({ type: 'text', value: text.slice(lastIndex) });
      }

      // Replace the text node with the new nodes
      (parent as Element).children.splice(index, 1, ...parts);
      return index + parts.length; // skip newly inserted nodes
    });
  };
}

// ── rehype plugin: link cross-references ──────────────────────────
// Links "→ Art. 8 Abs. 2 BV" (and the French/Italian/English forms such as
// "→ art. 8 al. 2 Cst.") to the article page. Plain mentions without an arrow
// ("Art. 29 Abs. 2 BV") are linked too, except references to the page itself.
const ABBR_TO_SLUG: Record<string, string> = {};
for (const law of LAWS) {
  ABBR_TO_SLUG[law.abbr] = law.slug;
  for (const a of Object.values(law.abbrI18n || {})) ABBR_TO_SLUG[a!] = law.slug;
}
const ABBR_ALT = Object.keys(ABBR_TO_SLUG)
  .sort((a, b) => b.length - a.length)
  .map((a) => a.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
  .join('|');
// Paragraph/letter/number qualifiers between the article number and the act.
const QUALIFIER = String.raw`(?:\s+(?:Abs\.|al\.|cpv\.|para\.|lit\.|let\.|Ziff\.|ch\.|n\.|Satz|S\.|phrase|frase|sentence)\s*[0-9a-z]+(?:bis|ter|quater)?)*`;
const XREF_RE = new RegExp(
  String.raw`([→↔]\s*)?\b([Aa]rt\.)\s*(\d+)([a-z]*)(` + QUALIFIER + String.raw`)\s+(` + ABBR_ALT + String.raw`)(?![\p{L}\d])`,
  'gu',
);

export interface SelfRef {
  law: string;
  article: string;
}

function rehypeCrossReferences(lang: string, self?: SelfRef) {
  return () => (tree: HastRoot) => {
    visit(tree, 'text', (node: Text, index, parent) => {
      if (!parent || index === undefined) return;
      const tag = (parent as Element).tagName;
      if (tag === 'a' || /^h[1-6]$/.test(tag)) return;

      const text = node.value;
      XREF_RE.lastIndex = 0;
      if (!XREF_RE.test(text)) return;

      XREF_RE.lastIndex = 0;
      const parts: ElementContent[] = [];
      let lastIndex = 0;
      let match;
      while ((match = XREF_RE.exec(text)) !== null) {
        const [fullMatch, arrow, , num, suffix, , abbr] = match;
        const slug = ABBR_TO_SLUG[abbr];
        const artSlug = `art-${parseInt(num, 10)}${suffix}`;
        if (!slug || (self && self.law === slug && self.article === artSlug)) continue;
        if (match.index > lastIndex) {
          parts.push({ type: 'text', value: text.slice(lastIndex, match.index) });
        }
        const linkNode: Element = {
          type: 'element',
          tagName: 'a',
          properties: {
            href: `${langBase(lang as Lang)}/${slug}/${artSlug}/`,
            className: [arrow ? 'cite-cross' : 'cite-art'],
          },
          children: [{ type: 'text', value: fullMatch }],
        };
        parts.push(linkNode);
        lastIndex = match.index + fullMatch.length;
      }
      if (parts.length === 0) return;
      if (lastIndex < text.length) {
        parts.push({ type: 'text', value: text.slice(lastIndex) });
      }

      (parent as Element).children.splice(index, 1, ...parts);
      return index + parts.length;
    });
  };
}

// ── rehype plugin: repair repository-relative links ───────────────
// Concept pages were authored with links to sibling markdown files
// ("../provisions/bgfa-art-13.md"). Map those to site URLs and unwrap
// links to page types the site does not publish.
function rehypeRepoLinks(lang: string) {
  return () => (tree: HastRoot) => {
    visit(tree, 'element', (node: Element, index, parent) => {
      if (node.tagName !== 'a' || !parent || index === undefined) return;
      const href = String(node.properties?.href || '');
      if (/^(https?:|mailto:|#)/.test(href) || !/\.md(#|$)/.test(href)) return;
      const prov = href.match(/provisions\/([a-z]+)-art-(\d+[a-z]*)\.md(#.*)?$/);
      if (prov) {
        node.properties = { ...node.properties, href: `${langBase(lang as Lang)}/${prov[1]}/art-${prov[2]}/` };
        return;
      }
      const concept = href.match(/concepts\/([a-z0-9-]+)\.md/);
      if (concept) {
        node.properties = { ...node.properties, href: `${langBase(lang as Lang)}/concepts/${concept[1]}/` };
        return;
      }
      (parent as Element).children.splice(index, 1, ...node.children);
      return index;
    });
  };
}

// ── rehype plugin: normalise heading levels ───────────────────────
// Layer files differ in how they start ("# Art. 8 BV — …" + "## Doktrin",
// "# Doktrin", or straight into sections). The page already names the article
// and the tab names the layer, so drop that preamble and shift the remaining
// headings so the top level is always <h2>.
const LAYER_HEADINGS = new Set([
  'übersicht', 'uebersicht', 'aperçu', 'panoramica', 'overview', 'summary',
  'doktrin', 'doctrine', 'dottrina',
  'rechtsprechung', 'jurisprudence', 'giurisprudenza', 'case law',
]);

function rehypeNormalizeHeadings() {
  return (tree: HastRoot) => {
    const isHeading = (n: ElementContent | HastRoot['children'][number]) =>
      n.type === 'element' && /^h[1-6]$/.test((n as Element).tagName);
    // Strip leading title/layer headings (only before any body content).
    while (tree.children.length > 0) {
      const first = tree.children.find((n) => !(n.type === 'text' && !n.value.trim()));
      if (!first || !isHeading(first)) break;
      const el = first as Element;
      const text = getTextContent(el).trim().toLowerCase();
      if (el.tagName === 'h1' || LAYER_HEADINGS.has(text)) {
        tree.children.splice(tree.children.indexOf(first), 1);
        continue;
      }
      break;
    }
    let min = 7;
    visit(tree, 'element', (node: Element) => {
      const m = node.tagName.match(/^h([1-6])$/);
      if (m) min = Math.min(min, parseInt(m[1], 10));
    });
    if (min === 7 || min === 2) return;
    const shift = 2 - min;
    visit(tree, 'element', (node: Element) => {
      const m = node.tagName.match(/^h([1-6])$/);
      if (m) node.tagName = `h${Math.min(6, parseInt(m[1], 10) + shift)}`;
    });
  };
}

// ── rehype plugin: custom slug generation matching old slugify ─────
function rehypeCustomSlug() {
  return (tree: HastRoot) => {
    visit(tree, 'element', (node: Element) => {
      if (!/^h[1-6]$/.test(node.tagName)) return;
      const text = getTextContent(node);
      node.properties = node.properties || {};
      node.properties.id = slugify(text);
    });
  };
}

// ── Helper: extract text content from hast node ───────────────────
function getTextContent(node: Element | Text | ElementContent): string {
  if (node.type === 'text') return node.value;
  if (node.type === 'element') {
    const cls = node.properties?.className;
    if (Array.isArray(cls) && cls.includes('heading-anchor')) return '';
    return node.children.map(getTextContent).join('');
  }
  return '';
}

// ── TOC extraction from hast tree ─────────────────────────────────
function extractTocFromHast(tree: HastRoot): TocEntry[] {
  const entries: TocEntry[] = [];
  visit(tree, 'element', (node: Element) => {
    const m = node.tagName.match(/^h([2-3])$/);
    if (!m) return;
    const level = parseInt(m[1]);
    const id = (node.properties?.id as string) || '';
    const text = getTextContent(node);
    if (id && text) {
      entries.push({ level, text, id });
    }
  });
  return entries;
}

// ── Main render function ──────────────────────────────────────────
export function renderMarkdown(
  md: string,
  lang: string,
  self?: SelfRef,
): { html: string; toc: TocEntry[] } {
  if (!md.trim()) {
    return {
      html: `<p class="text-muted">${t('article.layer_empty', lang as Lang)}</p>`,
      toc: [],
    };
  }

  let toc: TocEntry[] = [];

  const processor = unified()
    .use(remarkParse)
    .use(remarkRehype)
    .use(rehypeNormalizeHeadings)
    // Custom slug must run before rehype-slug to set IDs first
    .use(rehypeCustomSlug)
    // rehype-slug will not overwrite existing IDs
    .use(rehypeSlug)
    .use(rehypeAutolinkHeadings, {
      behavior: 'prepend',
      properties: {
        className: ['heading-anchor'],
        ariaHidden: 'true',
        dataPagefindIgnore: '',
      },
      content: {
        type: 'text',
        value: '#',
      },
      test: ['h2', 'h3'],
    })
    .use(rehypeRandziffern)
    .use(rehypeBgeCitations)
    .use(rehypeRepoLinks(lang))
    .use(rehypeCrossReferences(lang, self))
    // Extract TOC before stringifying
    .use(() => (tree: HastRoot) => {
      toc = extractTocFromHast(tree);
    })
    .use(rehypeStringify);

  const result = processor.processSync(md);
  return { html: String(result), toc };
}
