export interface LawInfo {
  abbr: string;
  name: string;
  sr: string;
  fullTitle: string;
  description: string;
}

export const LAWS: LawInfo[] = [
  {
    abbr: 'BV',
    name: 'Bundesverfassung',
    sr: '101',
    fullTitle: 'Bundesverfassung der Schweizerischen Eidgenossenschaft',
    description: 'Grundrechte, Staatsorganisation, Kompetenzverteilung',
  },
  {
    abbr: 'ZGB',
    name: 'Zivilgesetzbuch',
    sr: '210',
    fullTitle: 'Schweizerisches Zivilgesetzbuch',
    description: 'Personenrecht, Familienrecht, Erbrecht, Sachenrecht',
  },
  {
    abbr: 'OR',
    name: 'Obligationenrecht',
    sr: '220',
    fullTitle: 'Bundesgesetz betreffend die Ergänzung des Schweizerischen Zivilgesetzbuches (Fünfter Teil: Obligationenrecht)',
    description: 'Vertragsrecht, Haftpflicht, Gesellschaftsrecht',
  },
  {
    abbr: 'ZPO',
    name: 'Zivilprozessordnung',
    sr: '272',
    fullTitle: 'Schweizerische Zivilprozessordnung',
    description: 'Zivilverfahren, Schlichtung, Beweisrecht',
  },
  {
    abbr: 'StGB',
    name: 'Strafgesetzbuch',
    sr: '311.0',
    fullTitle: 'Schweizerisches Strafgesetzbuch',
    description: 'Straftatbestände, Sanktionen, Allgemeiner Teil',
  },
  {
    abbr: 'StPO',
    name: 'Strafprozessordnung',
    sr: '312.0',
    fullTitle: 'Schweizerische Strafprozessordnung',
    description: 'Strafverfahren, Ermittlung, Hauptverhandlung',
  },
  {
    abbr: 'SchKG',
    name: 'SchKG',
    sr: '281.1',
    fullTitle: 'Bundesgesetz über Schuldbetreibung und Konkurs',
    description: 'Betreibung, Konkurs, Pfändung, Nachlass',
  },
  {
    abbr: 'VwVG',
    name: 'VwVG',
    sr: '172.021',
    fullTitle: 'Bundesgesetz über das Verwaltungsverfahren',
    description: 'Verwaltungsverfahren, Verfügungen, Rechtsmittel',
  },
];

export function getLawByAbbr(abbr: string): LawInfo | undefined {
  return LAWS.find((l) => l.abbr.toLowerCase() === abbr.toLowerCase());
}

export function getLawAbbrList(): string[] {
  return LAWS.map((l) => l.abbr.toLowerCase());
}
