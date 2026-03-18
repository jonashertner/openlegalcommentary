import type { Lang } from './i18n';

export interface LawInfo {
  abbr: string;
  sr: string;
  name: Record<Lang, string>;
  description: Record<Lang, string>;
}

export const LAWS: LawInfo[] = [
  {
    abbr: 'BV',
    sr: '101',
    name: {
      de: 'Bundesverfassung',
      fr: 'Constitution fédérale',
      it: 'Costituzione federale',
      en: 'Federal Constitution',
    },
    description: {
      de: 'Grundrechte, Staatsorganisation, Kompetenzverteilung',
      fr: 'Droits fondamentaux, organisation de l\'État, répartition des compétences',
      it: 'Diritti fondamentali, organizzazione dello Stato, ripartizione delle competenze',
      en: 'Fundamental rights, state organization, distribution of powers',
    },
  },
  {
    abbr: 'ZGB',
    sr: '210',
    name: {
      de: 'Zivilgesetzbuch',
      fr: 'Code civil',
      it: 'Codice civile',
      en: 'Civil Code',
    },
    description: {
      de: 'Personenrecht, Familienrecht, Erbrecht, Sachenrecht',
      fr: 'Droit des personnes, droit de la famille, droit des successions, droits réels',
      it: 'Diritto delle persone, diritto di famiglia, diritto successorio, diritti reali',
      en: 'Law of persons, family law, inheritance law, property law',
    },
  },
  {
    abbr: 'OR',
    sr: '220',
    name: {
      de: 'Obligationenrecht',
      fr: 'Code des obligations',
      it: 'Codice delle obbligazioni',
      en: 'Code of Obligations',
    },
    description: {
      de: 'Vertragsrecht, Haftpflicht, Gesellschaftsrecht',
      fr: 'Droit des contrats, responsabilité civile, droit des sociétés',
      it: 'Diritto contrattuale, responsabilità civile, diritto societario',
      en: 'Contract law, tort law, corporate law',
    },
  },
  {
    abbr: 'ZPO',
    sr: '272',
    name: {
      de: 'Zivilprozessordnung',
      fr: 'Code de procédure civile',
      it: 'Codice di procedura civile',
      en: 'Civil Procedure Code',
    },
    description: {
      de: 'Zivilverfahren, Schlichtung, Beweisrecht',
      fr: 'Procédure civile, conciliation, droit de la preuve',
      it: 'Procedura civile, conciliazione, diritto probatorio',
      en: 'Civil procedure, conciliation, law of evidence',
    },
  },
  {
    abbr: 'StGB',
    sr: '311.0',
    name: {
      de: 'Strafgesetzbuch',
      fr: 'Code pénal',
      it: 'Codice penale',
      en: 'Criminal Code',
    },
    description: {
      de: 'Straftatbestände, Sanktionen, Allgemeiner Teil',
      fr: 'Infractions, sanctions, partie générale',
      it: 'Reati, sanzioni, parte generale',
      en: 'Criminal offences, sanctions, general part',
    },
  },
  {
    abbr: 'StPO',
    sr: '312.0',
    name: {
      de: 'Strafprozessordnung',
      fr: 'Code de procédure pénale',
      it: 'Codice di procedura penale',
      en: 'Criminal Procedure Code',
    },
    description: {
      de: 'Strafverfahren, Ermittlung, Hauptverhandlung',
      fr: 'Procédure pénale, enquête, débats',
      it: 'Procedura penale, indagine, dibattimento',
      en: 'Criminal procedure, investigation, trial',
    },
  },
  {
    abbr: 'SchKG',
    sr: '281.1',
    name: {
      de: 'SchKG',
      fr: 'LP',
      it: 'LEF',
      en: 'DCBA',
    },
    description: {
      de: 'Betreibung, Konkurs, Pfändung, Nachlass',
      fr: 'Poursuite, faillite, saisie, concordat',
      it: 'Esecuzione, fallimento, pignoramento, concordato',
      en: 'Debt enforcement, bankruptcy, seizure, composition',
    },
  },
  {
    abbr: 'VwVG',
    sr: '172.021',
    name: {
      de: 'VwVG',
      fr: 'PA',
      it: 'PA',
      en: 'APA',
    },
    description: {
      de: 'Verwaltungsverfahren, Verfügungen, Rechtsmittel',
      fr: 'Procédure administrative, décisions, voies de droit',
      it: 'Procedura amministrativa, decisioni, rimedi giuridici',
      en: 'Administrative procedure, decisions, legal remedies',
    },
  },
];

export function getLawByAbbr(abbr: string): LawInfo | undefined {
  return LAWS.find((l) => l.abbr.toLowerCase() === abbr.toLowerCase());
}

export function getLawAbbrList(): string[] {
  return LAWS.map((l) => l.abbr.toLowerCase());
}
