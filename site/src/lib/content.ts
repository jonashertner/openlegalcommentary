import fs from 'node:fs';
import path from 'node:path';
import yaml from 'js-yaml';

const CONTENT_ROOT = path.resolve(import.meta.dirname, '../../..', 'content');
const ARTICLE_LISTS_PATH = path.resolve(import.meta.dirname, '../../..', 'scripts', 'article_lists.json');

let _articleListsCache: Record<string, { sr_number: string; article_count: number }> | null = null;

function getArticleLists(): Record<string, { sr_number: string; article_count: number }> {
  if (_articleListsCache) return _articleListsCache;
  try {
    const raw = fs.readFileSync(ARTICLE_LISTS_PATH, 'utf-8');
    _articleListsCache = JSON.parse(raw);
    return _articleListsCache!;
  } catch {
    return {};
  }
}

export interface LayerMeta {
  last_generated: string;
  version: number;
  quality_score?: number;
  trigger?: string;
  last_reviewed?: string;
  total_decisions?: number;
  new_decisions_count?: number;
}

export interface ArticleMeta {
  law: string;
  article: number;
  article_suffix: string;
  title: string;
  sr_number: string;
  absatz_count: number;
  fedlex_url: string;
  lexfind_id?: number;
  lexfind_url: string;
  in_force_since: string;
  layers: Record<string, LayerMeta>;
}

export interface ArticleContent {
  meta: ArticleMeta;
  summary: string;
  doctrine: string;
  caselaw: string;
  dirName: string;
  slug: string;
  translations: {
    summary?: { fr?: string; it?: string };
    doctrine?: { fr?: string; it?: string };
    caselaw?: { fr?: string; it?: string };
  };
}

export interface LawStats {
  totalArticles: number;
  completedArticles: number;
  withContent: number;
}

function dirNameToSlug(dirName: string): string {
  const match = dirName.match(/^art-(\d+)([a-z]*)$/);
  if (!match) return dirName;
  const num = parseInt(match[1], 10);
  const suffix = match[2] || '';
  return `art-${num}${suffix}`;
}

export function slugToDirName(slug: string): string {
  const match = slug.match(/^art-(\d+)([a-z]*)$/);
  if (!match) return slug;
  const num = match[1].padStart(3, '0');
  const suffix = match[2] || '';
  return `art-${num}${suffix}`;
}

function readFileIfExists(filePath: string): string {
  try {
    return fs.readFileSync(filePath, 'utf-8');
  } catch {
    return '';
  }
}

function isPlaceholder(content: string): boolean {
  const lines = content.trim().split('\n').filter((l) => l.trim().length > 0);
  return lines.length <= 2;
}

export function loadArticleMeta(law: string, dirName: string): ArticleMeta | null {
  const metaPath = path.join(CONTENT_ROOT, law.toLowerCase(), dirName, 'meta.yaml');
  try {
    const raw = fs.readFileSync(metaPath, 'utf-8');
    return yaml.load(raw) as ArticleMeta;
  } catch {
    return null;
  }
}

export function loadArticle(law: string, dirName: string): ArticleContent | null {
  const artDir = path.join(CONTENT_ROOT, law.toLowerCase(), dirName);
  if (!fs.existsSync(artDir)) return null;
  const meta = loadArticleMeta(law, dirName);
  if (!meta) return null;
  const summary = readFileIfExists(path.join(artDir, 'summary.md'));
  const doctrine = readFileIfExists(path.join(artDir, 'doctrine.md'));
  const caselaw = readFileIfExists(path.join(artDir, 'caselaw.md'));
  const translations: ArticleContent['translations'] = {};
  for (const layer of ['summary', 'doctrine', 'caselaw'] as const) {
    const fr = readFileIfExists(path.join(artDir, `${layer}.fr.md`));
    const it = readFileIfExists(path.join(artDir, `${layer}.it.md`));
    if (fr || it) {
      translations[layer] = {};
      if (fr) translations[layer]!.fr = fr;
      if (it) translations[layer]!.it = it;
    }
  }
  return { meta, summary, doctrine, caselaw, dirName, slug: dirNameToSlug(dirName), translations };
}

export function listArticleDirs(law: string): string[] {
  const lawDir = path.join(CONTENT_ROOT, law.toLowerCase());
  try {
    const entries = fs.readdirSync(lawDir, { withFileTypes: true });
    return entries
      .filter((e) => e.isDirectory() && e.name.startsWith('art-'))
      .map((e) => e.name)
      .sort((a, b) => {
        const matchA = a.match(/^art-(\d+)([a-z]*)$/);
        const matchB = b.match(/^art-(\d+)([a-z]*)$/);
        if (!matchA || !matchB) return a.localeCompare(b);
        const numA = parseInt(matchA[1], 10);
        const numB = parseInt(matchB[1], 10);
        if (numA !== numB) return numA - numB;
        return (matchA[2] || '').localeCompare(matchB[2] || '');
      });
  } catch {
    return [];
  }
}

export function listArticles(law: string): { meta: ArticleMeta; dirName: string; slug: string }[] {
  const dirs = listArticleDirs(law);
  const articles: { meta: ArticleMeta; dirName: string; slug: string }[] = [];
  for (const dirName of dirs) {
    const meta = loadArticleMeta(law, dirName);
    if (meta) {
      articles.push({ meta, dirName, slug: dirNameToSlug(dirName) });
    }
  }
  return articles;
}

export function getLawStats(law: string): LawStats {
  const dirs = listArticleDirs(law);
  if (dirs.length === 0) {
    const lists = getArticleLists();
    const count = lists[law.toUpperCase()]?.article_count ?? 0;
    return { totalArticles: count, completedArticles: 0, withContent: 0 };
  }
  let withContent = 0;
  for (const dirName of dirs) {
    const artDir = path.join(CONTENT_ROOT, law.toLowerCase(), dirName);
    const summary = readFileIfExists(path.join(artDir, 'summary.md'));
    if (!isPlaceholder(summary)) {
      withContent++;
    }
  }
  return { totalArticles: dirs.length, completedArticles: withContent, withContent };
}

export function getArticleNav(
  law: string,
  currentDirName: string
): { prev: { slug: string; title: string } | null; next: { slug: string; title: string } | null } {
  const dirs = listArticleDirs(law);
  const idx = dirs.indexOf(currentDirName);
  let prev: { slug: string; title: string } | null = null;
  let next: { slug: string; title: string } | null = null;
  if (idx > 0) {
    const meta = loadArticleMeta(law, dirs[idx - 1]);
    if (meta) prev = { slug: dirNameToSlug(dirs[idx - 1]), title: meta.title };
  }
  if (idx >= 0 && idx < dirs.length - 1) {
    const meta = loadArticleMeta(law, dirs[idx + 1]);
    if (meta) next = { slug: dirNameToSlug(dirs[idx + 1]), title: meta.title };
  }
  return { prev, next };
}
