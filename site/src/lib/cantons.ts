import type { Lang } from './i18n';

export interface Canton {
  code: string;
  language: 'de' | 'fr' | 'it';
  name: Record<Lang, string>;
}

export const CANTONS: Canton[] = [
  {
    code: 'ZH',
    language: 'de',
    name: {
      de: 'Zürich',
      fr: 'Zurich',
      it: 'Zurigo',
      en: 'Zurich',
    },
  },
  {
    code: 'BE',
    language: 'de',
    name: {
      de: 'Bern',
      fr: 'Berne',
      it: 'Berna',
      en: 'Bern',
    },
  },
  {
    code: 'LU',
    language: 'de',
    name: {
      de: 'Luzern',
      fr: 'Lucerne',
      it: 'Lucerna',
      en: 'Lucerne',
    },
  },
  {
    code: 'UR',
    language: 'de',
    name: {
      de: 'Uri',
      fr: 'Uri',
      it: 'Uri',
      en: 'Uri',
    },
  },
  {
    code: 'SZ',
    language: 'de',
    name: {
      de: 'Schwyz',
      fr: 'Schwyz',
      it: 'Svitto',
      en: 'Schwyz',
    },
  },
  {
    code: 'OW',
    language: 'de',
    name: {
      de: 'Obwalden',
      fr: 'Obwald',
      it: 'Obvaldo',
      en: 'Obwalden',
    },
  },
  {
    code: 'NW',
    language: 'de',
    name: {
      de: 'Nidwalden',
      fr: 'Nidwald',
      it: 'Nidvaldo',
      en: 'Nidwalden',
    },
  },
  {
    code: 'GL',
    language: 'de',
    name: {
      de: 'Glarus',
      fr: 'Glaris',
      it: 'Glarona',
      en: 'Glarus',
    },
  },
  {
    code: 'ZG',
    language: 'de',
    name: {
      de: 'Zug',
      fr: 'Zoug',
      it: 'Zugo',
      en: 'Zug',
    },
  },
  {
    code: 'FR',
    language: 'fr',
    name: {
      de: 'Freiburg',
      fr: 'Fribourg',
      it: 'Friburgo',
      en: 'Fribourg',
    },
  },
  {
    code: 'SO',
    language: 'de',
    name: {
      de: 'Solothurn',
      fr: 'Soleure',
      it: 'Soletta',
      en: 'Solothurn',
    },
  },
  {
    code: 'BS',
    language: 'de',
    name: {
      de: 'Basel-Stadt',
      fr: 'Bâle-Ville',
      it: 'Basilea Città',
      en: 'Basel-Stadt',
    },
  },
  {
    code: 'BL',
    language: 'de',
    name: {
      de: 'Basel-Landschaft',
      fr: 'Bâle-Campagne',
      it: 'Basilea Campagna',
      en: 'Basel-Landschaft',
    },
  },
  {
    code: 'SH',
    language: 'de',
    name: {
      de: 'Schaffhausen',
      fr: 'Schaffhouse',
      it: 'Sciaffusa',
      en: 'Schaffhausen',
    },
  },
  {
    code: 'AR',
    language: 'de',
    name: {
      de: 'Appenzell Ausserrhoden',
      fr: 'Appenzell Rhodes-Extérieures',
      it: 'Appenzello Esterno',
      en: 'Appenzell Ausserrhoden',
    },
  },
  {
    code: 'AI',
    language: 'de',
    name: {
      de: 'Appenzell Innerrhoden',
      fr: 'Appenzell Rhodes-Intérieures',
      it: 'Appenzello Interno',
      en: 'Appenzell Innerrhoden',
    },
  },
  {
    code: 'SG',
    language: 'de',
    name: {
      de: 'St. Gallen',
      fr: 'Saint-Gall',
      it: 'San Gallo',
      en: 'St. Gallen',
    },
  },
  {
    code: 'GR',
    language: 'de',
    name: {
      de: 'Graubünden',
      fr: 'Grisons',
      it: 'Grigioni',
      en: 'Graubünden',
    },
  },
  {
    code: 'AG',
    language: 'de',
    name: {
      de: 'Aargau',
      fr: 'Argovie',
      it: 'Argovia',
      en: 'Aargau',
    },
  },
  {
    code: 'TG',
    language: 'de',
    name: {
      de: 'Thurgau',
      fr: 'Thurgovie',
      it: 'Turgovia',
      en: 'Thurgau',
    },
  },
  {
    code: 'TI',
    language: 'it',
    name: {
      de: 'Tessin',
      fr: 'Tessin',
      it: 'Ticino',
      en: 'Ticino',
    },
  },
  {
    code: 'VD',
    language: 'fr',
    name: {
      de: 'Waadt',
      fr: 'Vaud',
      it: 'Vaud',
      en: 'Vaud',
    },
  },
  {
    code: 'VS',
    language: 'de',
    name: {
      de: 'Wallis',
      fr: 'Valais',
      it: 'Vallese',
      en: 'Valais',
    },
  },
  {
    code: 'NE',
    language: 'fr',
    name: {
      de: 'Neuenburg',
      fr: 'Neuchâtel',
      it: 'Neuchâtel',
      en: 'Neuchâtel',
    },
  },
  {
    code: 'GE',
    language: 'fr',
    name: {
      de: 'Genf',
      fr: 'Genève',
      it: 'Ginevra',
      en: 'Geneva',
    },
  },
  {
    code: 'JU',
    language: 'fr',
    name: {
      de: 'Jura',
      fr: 'Jura',
      it: 'Giura',
      en: 'Jura',
    },
  },
];

export function getCantonByCode(code: string): Canton | undefined {
  return CANTONS.find((c) => c.code.toUpperCase() === code.toUpperCase());
}
