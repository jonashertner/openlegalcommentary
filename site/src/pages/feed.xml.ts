import type { APIRoute } from 'astro';
import fs from 'node:fs';
import path from 'node:path';
import yaml from 'js-yaml';

const CONTENT_ROOT = path.resolve(import.meta.dirname, '../../..', 'content');
const SITE_URL = 'https://openlegalcommentary.ch';
const LAWS = ['bv', 'zgb', 'or', 'zpo', 'stgb', 'stpo', 'schkg', 'vwvg'];

interface FeedEntry {
  law: string;
  article: number;
  suffix: string;
  title: string;
  date: string;
  layer: string;
  version: number;
}

function collectEntries(): FeedEntry[] {
  const entries: FeedEntry[] = [];

  for (const law of LAWS) {
    const lawDir = path.join(CONTENT_ROOT, law);
    if (!fs.existsSync(lawDir)) continue;

    const dirs = fs.readdirSync(lawDir, { withFileTypes: true })
      .filter(d => d.isDirectory() && d.name.startsWith('art-'))
      .map(d => d.name);

    for (const dir of dirs) {
      const metaPath = path.join(lawDir, dir, 'meta.yaml');
      if (!fs.existsSync(metaPath)) continue;

      try {
        const meta = yaml.load(fs.readFileSync(metaPath, 'utf-8')) as any;
        if (!meta?.layers) continue;

        for (const [layerName, layerMeta] of Object.entries(meta.layers) as [string, any][]) {
          if (layerMeta?.last_generated) {
            entries.push({
              law: (meta.law || law).toUpperCase(),
              article: meta.article,
              suffix: meta.article_suffix || '',
              title: meta.title || `Art. ${meta.article}${meta.article_suffix || ''} ${law.toUpperCase()}`,
              date: layerMeta.last_generated,
              layer: layerName,
              version: layerMeta.version || 1,
            });
          }
        }
      } catch {
        // skip malformed meta
      }
    }
  }

  // Sort by date descending, take latest 100
  entries.sort((a, b) => b.date.localeCompare(a.date));
  return entries.slice(0, 100);
}

const layerLabel: Record<string, string> = {
  summary: 'Overview',
  doctrine: 'Doctrine',
  caselaw: 'Case Law',
};

function escapeXml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

export const GET: APIRoute = () => {
  const entries = collectEntries();

  const items = entries.map(e => {
    const num = e.article;
    const slug = `art-${num}${e.suffix}`;
    const display = `Art. ${num}${e.suffix} ${e.law}`;
    const layer = layerLabel[e.layer] || e.layer;
    const url = `${SITE_URL}/de/${e.law.toLowerCase()}/${slug}`;

    return `    <item>
      <title>${escapeXml(`${display} — ${e.title} (${layer} v${e.version})`)}</title>
      <link>${url}</link>
      <guid>${url}#${e.layer}-v${e.version}</guid>
      <pubDate>${new Date(e.date).toUTCString()}</pubDate>
      <description>${escapeXml(`${layer} layer updated for ${display}`)}</description>
    </item>`;
  }).join('\n');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Open Legal Commentary</title>
    <link>${SITE_URL}</link>
    <description>Open, AI-generated commentary on Swiss federal law. Updated daily.</description>
    <language>de</language>
    <atom:link href="${SITE_URL}/feed.xml" rel="self" type="application/rss+xml" />
${items}
  </channel>
</rss>`;

  return new Response(xml, {
    headers: { 'Content-Type': 'application/xml; charset=utf-8' },
  });
};
