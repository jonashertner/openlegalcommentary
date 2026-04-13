import fs from 'node:fs';
import path from 'node:path';
import yaml from 'js-yaml';

const CONTENT_ROOT = path.resolve(import.meta.dirname, '../../..', 'content');
const ARTICLE_LISTS_PATH = path.resolve(import.meta.dirname, '../../..', 'scripts', 'article_lists.json');
const ARTICLE_TITLES_I18N_PATH = path.resolve(import.meta.dirname, '../../..', 'scripts', 'article_titles_i18n.json');
const CANTONAL_DIR = path.resolve(import.meta.dirname, '../../..', 'scripts', 'cantonal');

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

interface CantonalLawData {
  canton: string;
  law_key: string;
  sr_number: string;
  language: string;
  title: string;
  lexfind_id: number;
  fetched_at: string;
  article_count: number;
  articles: { number: number; suffix: string; raw: string; title: string }[];
  article_texts: Record<string, ArticleTextParagraph[]>;
}

const _cantonalCache: Record<string, CantonalLawData> = {};

function loadCantonalLaw(slug: string): CantonalLawData | null {
  if (_cantonalCache[slug]) return _cantonalCache[slug];
  const filePath = path.join(CANTONAL_DIR, `${slug}.json`);
  try {
    const raw = fs.readFileSync(filePath, 'utf-8');
    const data = JSON.parse(raw) as CantonalLawData;
    _cantonalCache[slug] = data;
    return data;
  } catch {
    return null;
  }
}

export function listCantonalLawSlugs(): string[] {
  try {
    return fs.readdirSync(CANTONAL_DIR)
      .filter(f => f.endsWith('.json'))
      .map(f => f.replace('.json', ''));
  } catch {
    return [];
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
  // Check cantonal JSON first
  const cantonal = loadCantonalLaw(law.toLowerCase());
  if (cantonal) {
    return cantonal.article_texts[articleRaw] || [];
  }

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
  isFallback: boolean;
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

  let isFallback = false;
  function loadLayer(layer: string): string {
    if (lang === 'de') {
      return readFileIfExists(path.join(artDir, `${layer}.md`));
    }
    const langFile = readFileIfExists(path.join(artDir, `${layer}.${lang}.md`));
    if (langFile.trim().length > 0) return langFile;
    // Fallback to German
    const deFile = readFileIfExists(path.join(artDir, `${layer}.md`));
    if (deFile.trim().length > 0) isFallback = true;
    return deFile;
  }

  const summary = loadLayer('summary');
  const doctrine = loadLayer('doctrine');
  const caselaw = loadLayer('caselaw');
  return { meta, summary, doctrine, caselaw, dirName, slug: dirNameToSlug(dirName), isFallback };
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

  // Check cantonal JSON
  const cantonal = loadCantonalLaw(law.toLowerCase());
  if (cantonal) {
    return cantonal.articles.map((entry) => {
      const num = entry.number;
      const suffix = entry.suffix || '';
      const dirName = `art-${String(num).padStart(3, '0')}${suffix}`;
      const slug = `art-${num}${suffix}`;
      const meta: ArticleMeta = {
        law: cantonal.law_key.toUpperCase(),
        article: num,
        article_suffix: suffix,
        title: entry.title || '',
        sr_number: cantonal.sr_number,
        absatz_count: 1,
        fedlex_url: '',
        lexfind_url: '',
        in_force_since: '',
        layers: {},
      };
      return { meta, dirName, slug };
    });
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
    // Check cantonal JSON
    const cantonal = loadCantonalLaw(law.toLowerCase());
    if (cantonal) {
      return { totalArticles: cantonal.article_count, completedArticles: 0, withContent: 0 };
    }
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

  if (dirs.length === 0) {
    // Use listArticles fallback (covers both article_lists.json and cantonal JSON)
    const articles = listArticles(law);
    const currentSlug = dirNameToSlug(currentDirName);
    const idx = articles.findIndex(a => a.slug === currentSlug);
    return {
      prev: idx > 0 ? { slug: articles[idx - 1].slug, title: articles[idx - 1].meta.title } : null,
      next: idx >= 0 && idx < articles.length - 1 ? { slug: articles[idx + 1].slug, title: articles[idx + 1].meta.title } : null,
    };
  }

  // Existing content-dir logic (unchanged)
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
  } catch {
    return [];
  }
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
  } catch {
    return [];
  }
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
