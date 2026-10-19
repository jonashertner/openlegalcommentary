import type { APIRoute } from 'astro';
import { LANGS } from '@/lib/i18n';
import { LAWS } from '@/lib/laws';
import { listArticles, listConcepts, listCantonalLawSlugs } from '@/lib/content';

const SITE_URL = 'https://openlegalcommentary.ch';

function escapeXml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

export const GET: APIRoute = () => {
  // Language-independent paths; every one exists in all four languages.
  const paths: string[] = ['/', '/about/', '/methodology/', '/changelog/', '/concepts/'];
  for (const concept of listConcepts()) paths.push(`/concepts/${concept.slug}/`);

  for (const law of LAWS) {
    paths.push(`/${law.slug}/`);
    // Only articles with commentary; the rest are noindex until written.
    for (const art of listArticles(law.slug)) {
      if (art.hasCommentary) paths.push(`/${law.slug}/${art.slug}/`);
    }
  }
  for (const slug of listCantonalLawSlugs()) paths.push(`/${slug}/`);

  const entries = paths.flatMap((pagePath) =>
    LANGS.map((lang) => {
      const alternates = [...LANGS, 'x-default' as const].map((l) =>
        `    <xhtml:link rel="alternate" hreflang="${l}" href="${SITE_URL}/${l === 'x-default' ? 'de' : l}${pagePath}" />`
      ).join('\n');
      return `  <url>
    <loc>${escapeXml(`${SITE_URL}/${lang}${pagePath}`)}</loc>
${alternates}
  </url>`;
    })
  );

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
${entries.join('\n')}
</urlset>`;

  return new Response(xml, {
    headers: { 'Content-Type': 'application/xml; charset=utf-8' },
  });
};
