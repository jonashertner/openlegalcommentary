/** Base URL path, stripped of trailing slash for safe concatenation. */
const raw = import.meta.env.BASE_URL.replace(/\/$/, '');
export const BASE = raw || '';

/** Home URL — always '/' at minimum. */
export const HOME = raw || '/';
