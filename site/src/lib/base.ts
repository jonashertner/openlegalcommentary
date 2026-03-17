import type { Lang } from './i18n';

export const BASE = import.meta.env.BASE_URL?.replace(/\/$/, '') ?? '';

export function langBase(lang: Lang): string {
  return `${BASE}/${lang}`;
}

export function langHome(lang: Lang): string {
  return `${BASE}/${lang}/`;
}

// Keep HOME for the root redirect page
export const HOME = BASE || '/';
