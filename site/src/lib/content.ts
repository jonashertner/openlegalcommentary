import fs from 'node:fs';
import path from 'node:path';
import yaml from 'js-yaml';

const CONTENT_ROOT = path.resolve(import.meta.dirname, '../../..', 'content');
const ARTICLE_LISTS_PATH = path.resolve(import.meta.dirname, '../../..', 'scripts', 'article_lists.json');
const ARTICLE_TITLES_I18N_PATH = path.resolve(import.meta.dirname, '../../..', 'scripts', 'article_titles_i18n.json');

interface ArticleListEntry {
  number: number;
  suffix: string;
  raw: string;
  title?: string;
}

interface ArticleListData {
  sr_number: string;
  article_count: number;
  articles: ArticleListEntry[];
}

let _articleListsCache: Record<string, ArticleListData> | null = null;

function getArticleLists(): Record<string, ArticleListData> {
  if (_articleListsCache) return _articleListsCache;
  try {
    const raw = fs.readFileSync(ARTICLE_LISTS_PATH, 'utf-8');
    _articleListsCache = JSON.parse(raw);
    return _articleListsCache!;
  } catch {
    return {};
  }
}

// Translated article titles (FR/IT from opencaselaw API)
type TitleI18nData = Record<string, Record<string, Record<string, string>>>;
let _titleI18nCache: TitleI18nData | null = null;

function getTitleI18n(): TitleI18nData {
  if (_titleI18nCache) return _titleI18nCache;
  try {
    const raw = fs.readFileSync(ARTICLE_TITLES_I18N_PATH, 'utf-8');
    _titleI18nCache = JSON.parse(raw);
    return _titleI18nCache!;
  } catch {
    return {};
  }
}

export function getTranslatedTitle(law: string, articleRaw: string, lang: string, fallback: string): string {
  if (lang === 'de') return fallback;
  const data = getTitleI18n();
  const lawTitles = data[lang]?.[law.toUpperCase()];
  if (!lawTitles) return fallback;
  return lawTitles[articleRaw] || fallback;
}

export interface ArticleTextParagraph {
  num?: string | null;
  text?: string;
  type?: 'list';
  items?: { letter: string; text: string }[];
}

type ArticleTextsData = Record<string, Record<string, ArticleTextParagraph[]>>;

const _articleTextsCache: Record<string, ArticleTextsData> = {};

function getArticleTexts(lang: string = 'de'): ArticleTextsData {
  if (_articleTextsCache[lang]) return _articleTextsCache[lang];
  const suffix = lang === 'de' ? '' : `_${lang}`;
  const textsPath = path.resolve(import.meta.dirname, '../../..', 'scripts', `article_texts${suffix}.json`);
  try {
    const raw = fs.readFileSync(textsPath, 'utf-8');
    _articleTextsCache[lang] = JSON.parse(raw);
    return _articleTextsCache[lang];
  } catch {
    return {};
  }
}

function _findLawKey(texts: ArticleTextsData, law: string): string | undefined {
  return Object.keys(texts).find((k) => k.toLowerCase() === law.toLowerCase());
}

function _findArticleKey(lawTexts: Record<string, ArticleTextParagraph[]>, articleRaw: string): string | undefined {
  if (articleRaw in lawTexts) return articleRaw;
  // article_texts.json uses "5_a" format, site uses "5a" — try underscore variant
  const underscored = articleRaw.replace(/(\d)([a-z])/g, '$1_$2');
  if (underscored in lawTexts) return underscored;
  return undefined;
}

export function getArticleText(law: string, articleRaw: string, lang: string = 'de'): ArticleTextParagraph[] {
  const texts = getArticleTexts(lang);
  const key = _findLawKey(texts, law);
  if (!key) return [];
  const artKey = _findArticleKey(texts[key], articleRaw);
  return artKey ? texts[key][artKey] : [];
}

export function getArticleTextI18n(
  law: string, articleRaw: string
): Record<string, ArticleTextParagraph[]> {
  const result: Record<string, ArticleTextParagraph[]> = {};
  for (const lang of ['de', 'fr', 'it', 'en']) {
    const texts = getArticleTexts(lang);
    const key = _findLawKey(texts, law);
    if (key) {
      const artKey = _findArticleKey(texts[key], articleRaw);
      const paragraphs = artKey ? texts[key][artKey] : [];
      if (paragraphs.length > 0) result[lang] = paragraphs;
    }
  }
  return result;
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
  return lines.length <= 3 && lines.reduce((sum, l) => sum + l.length, 0) <= 200;
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

export function loadArticle(law: string, dirName: string, lang: string = 'de'): ArticleContent | null {
  const artDir = path.join(CONTENT_ROOT, law.toLowerCase(), dirName);
  if (!fs.existsSync(artDir)) return null;
  const meta = loadArticleMeta(law, dirName);
  if (!meta) return null;

  function loadLayer(layer: string): string {
    if (lang === 'de') {
      return readFileIfExists(path.join(artDir, `${layer}.md`));
    }
    const langFile = readFileIfExists(path.join(artDir, `${layer}.${lang}.md`));
    if (langFile.trim().length > 0) return langFile;
    // Fallback to German
    return readFileIfExists(path.join(artDir, `${layer}.md`));
  }

  const summary = loadLayer('summary');
  const doctrine = loadLayer('doctrine');
  const caselaw = loadLayer('caselaw');
  return { meta, summary, doctrine, caselaw, dirName, slug: dirNameToSlug(dirName) };
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
  if (dirs.length > 0) {
    const articles: { meta: ArticleMeta; dirName: string; slug: string }[] = [];
    for (const dirName of dirs) {
      const meta = loadArticleMeta(law, dirName);
      if (meta) {
        articles.push({ meta, dirName, slug: dirNameToSlug(dirName) });
      }
    }
    return articles;
  }

  // Fallback: build article list from article_lists.json (no content dirs)
  const lists = getArticleLists();
  const lawData = lists[law.toUpperCase()];
  if (!lawData) return [];

  return lawData.articles.map((entry) => {
    const num = entry.number;
    const suffix = entry.suffix || '';
    const dirName = `art-${String(num).padStart(3, '0')}${suffix}`;
    const slug = `art-${num}${suffix}`;
    const title = entry.title || `Art. ${num}${suffix} ${law}`;
    const sr = lawData.sr_number;
    const meta: ArticleMeta = {
      law: law.toUpperCase(),
      article: num,
      article_suffix: suffix,
      title,
      sr_number: sr,
      absatz_count: 1,
      fedlex_url: '',
      lexfind_url: '',
      in_force_since: '',
      layers: {},
    };
    return { meta, dirName, slug };
  });
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
