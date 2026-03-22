import type { APIRoute } from 'astro';
import fs from 'node:fs';
import path from 'node:path';
import { LANGS } from '@/lib/i18n';

const SITE_URL = 'https://openlegalcommentary.ch';
const CONTENT_ROOT = path.resolve(import.meta.dirname, '../../..', 'content');
const LAWS = ['bv', 'zgb', 'or', 'zpo', 'stgb', 'stpo', 'schkg', 'vwvg'];

function escapeXml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

export const GET: APIRoute = () => {
  const urls: string[] = [];

  for (const lang of LANGS) {
    // Static pages
    urls.push(`${SITE_URL}/${lang}/`);
    urls.push(`${SITE_URL}/${lang}/about`);
    urls.push(`${SITE_URL}/${lang}/methodology`);
    urls.push(`${SITE_URL}/${lang}/changelog`);

    // Law index pages
    for (const law of LAWS) {
      urls.push(`${SITE_URL}/${lang}/${law}`);

      // Article pages
      const lawDir = path.join(CONTENT_ROOT, law);
      if (fs.existsSync(lawDir)) {
        const dirs = fs.readdirSync(lawDir, { withFileTypes: true })
          .filter(d => d.isDirectory() && d.name.startsWith('art-'))
          .map(d => d.name)
          .sort();

        for (const dir of dirs) {
          const match = dir.match(/^art-(\d+)([a-z]*)$/);
          if (match) {
            const slug = `art-${parseInt(match[1], 10)}${match[2] || ''}`;
            urls.push(`${SITE_URL}/${lang}/${law}/${slug}`);
          }
        }
      }
    }
  }

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
${urls.map(url => {
    // Extract lang and path for hreflang alternates
    const match = url.match(new RegExp(`^${SITE_URL}/(\\w+)(/.*)?$`));
    const pagePath = match?.[2] || '/';
    const alternates = LANGS.map(l =>
      `    <xhtml:link rel="alternate" hreflang="${l}" href="${SITE_URL}/${l}${pagePath}" />`
    ).join('\n');

    return `  <url>
    <loc>${escapeXml(url)}</loc>
${alternates}
  </url>`;
  }).join('\n')}
</urlset>`;

  return new Response(xml, {
    headers: { 'Content-Type': 'application/xml; charset=utf-8' },
  });
};
