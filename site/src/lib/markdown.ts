import { unified } from 'unified';
import remarkParse from 'remark-parse';
import remarkRehype from 'remark-rehype';
import rehypeStringify from 'rehype-stringify';
import rehypeSlug from 'rehype-slug';
import rehypeAutolinkHeadings from 'rehype-autolink-headings';
import { visit } from 'unist-util-visit';
import type { Root as HastRoot, Element, Text, ElementContent } from 'hast';
import { langBase } from './base';
import type { Lang } from './i18n';

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
    visit(tree, 'element', (node: Element) => {
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
function rehypeCrossReferences(lang: string) {
  const XREF_RE = /([→↔])\s*Art\.\s*(\d+)([a-z]*)\s+(BV|ZGB|OR|ZPO|StGB|StPO|SchKG|VwVG)/g;

  return () => (tree: HastRoot) => {
    visit(tree, 'text', (node: Text, index, parent) => {
      if (!parent || index === undefined) return;
      if ((parent as Element).tagName === 'a') return;

      const text = node.value;
      XREF_RE.lastIndex = 0;
      if (!XREF_RE.test(text)) return;

      XREF_RE.lastIndex = 0;
      const parts: ElementContent[] = [];
      let lastIndex = 0;
      let match;
      while ((match = XREF_RE.exec(text)) !== null) {
        if (match.index > lastIndex) {
          parts.push({ type: 'text', value: text.slice(lastIndex, match.index) });
        }
        const fullMatch = match[0];
        const [, , num, suffix, law] = match;
        const base = langBase(lang as Lang);
        const href = `${base}/${law.toLowerCase()}/art-${parseInt(num)}${suffix}`;
        const linkNode: Element = {
          type: 'element',
          tagName: 'a',
          properties: {
            href,
            className: ['cite-cross'],
          },
          children: [{ type: 'text', value: fullMatch }],
        };
        parts.push(linkNode);
        lastIndex = match.index + fullMatch.length;
      }
      if (lastIndex < text.length) {
        parts.push({ type: 'text', value: text.slice(lastIndex) });
      }

      (parent as Element).children.splice(index, 1, ...parts);
      return index + parts.length;
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
  lang: string
): { html: string; toc: TocEntry[] } {
  if (!md.trim()) {
    return {
      html: '<p class="text-muted">Noch kein Inhalt verfügbar.</p>',
      toc: [],
    };
  }

  let toc: TocEntry[] = [];

  const processor = unified()
    .use(remarkParse)
    .use(remarkRehype)
    // Custom slug must run before rehype-slug to set IDs first
    .use(rehypeCustomSlug)
    // rehype-slug will not overwrite existing IDs
    .use(rehypeSlug)
    .use(rehypeAutolinkHeadings, {
      behavior: 'prepend',
      properties: {
        className: ['heading-anchor'],
        ariaHidden: 'true',
      },
      content: {
        type: 'text',
        value: '#',
      },
      test: ['h2', 'h3'],
    })
    .use(rehypeRandziffern)
    .use(rehypeBgeCitations)
    .use(rehypeCrossReferences(lang))
    // Extract TOC before stringifying
    .use(() => (tree: HastRoot) => {
      toc = extractTocFromHast(tree);
    })
    .use(rehypeStringify);

  const result = processor.processSync(md);
  return { html: String(result), toc };
}
