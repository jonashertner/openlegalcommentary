# Project Scaffold & Guidelines — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Set up the openlegalcommentary repository with all configuration, authoring guidelines, quality evaluation rubric, per-law guidelines, content schema validation, and a Fedlex article enumerator.

**Architecture:** Markdown-based guidelines that serve as the autonomous "editor-in-chief" for AI agents. A Python validation script enforces the content schema. A Fedlex SPARQL integration enumerates articles per law to scaffold the `content/` directory.

**Tech Stack:** Python 3.12+, pydantic (schema validation), httpx (Fedlex SPARQL), pytest, ruff (linting)

**Spec:** `docs/superpowers/specs/2026-03-10-openlegalcommentary-design.md`

---

## Chunk 1: Repository Foundation

### Task 1: Project configuration files

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.python-version`
- Create: `CLAUDE.md`
- Create: `LICENSE-CODE`
- Create: `LICENSE-CONTENT`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "openlegalcommentary"
version = "0.1.0"
description = "Open-access AI-generated legal commentary on Swiss federal law"
requires-python = ">=3.12"
license = "MIT"
dependencies = [
    "pydantic>=2.0",
    "httpx>=0.27",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "ruff>=0.9",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 2: Create .gitignore**

```gitignore
__pycache__/
*.pyc
.venv/
.env
dist/
*.egg-info/
.ruff_cache/
.pytest_cache/
node_modules/
.DS_Store
```

- [ ] **Step 3: Create .python-version**

```
3.12
```

- [ ] **Step 4: Create LICENSE-CODE (MIT)**

Standard MIT license text with "2026 openlegalcommentary.ch contributors".

- [ ] **Step 5: Create LICENSE-CONTENT (CC BY-SA 4.0)**

Standard CC BY-SA 4.0 legalcode text. First line should note:
```
The commentary content in the content/ directory is licensed under
Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
```

- [ ] **Step 6: Create CLAUDE.md**

```markdown
# openlegalcommentary

Open-access, AI-generated, daily-updated legal commentary on Swiss federal law.

## Project structure

- `guidelines/` — Authoring guidelines (global + per-law) and quality evaluation rubric
- `content/` — Generated commentary organized by law and article
- `agents/` — Agent pipeline (coordinator, law agents, evaluator, translator)
- `site/` — Astro static site
- `export/` — HuggingFace dataset export
- `scripts/` — Utility scripts (Fedlex fetcher, validation)
- `tests/` — Test suite

## Content schema

Each article lives in `content/{law}/art-{number}/` with:
- `meta.yaml` — Article metadata and per-layer state
- `summary.md` — Plain-language summary (B1 reading level)
- `doctrine.md` — Doctrinal analysis with Randziffern
- `caselaw.md` — Case law digest, daily updated
- `*.fr.md` / `*.it.md` — French/Italian translations

## Guidelines

All authoring is governed by `guidelines/global.md` (core standards) and
`guidelines/{law}.md` (law-specific context). Quality evaluation uses
`guidelines/evaluate.md`.

## Laws covered

BV (SR 101), ZGB (SR 210), OR (SR 220), ZPO (SR 272),
StGB (SR 311.0), StPO (SR 312.0), SchKG (SR 281.1), VwVG (SR 172.021)

## Commands

- `uv run pytest` — run tests
- `uv run ruff check .` — lint
- `uv run python scripts/validate_content.py` — validate content schema
- `uv run python scripts/fetch_articles.py` — fetch article lists from Fedlex
```

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml .gitignore .python-version LICENSE-CODE LICENSE-CONTENT CLAUDE.md
git commit -m "chore: project scaffolding — pyproject, licenses, CLAUDE.md"
```

---

### Task 2: Directory structure

**Files:**
- Create: `guidelines/.gitkeep`
- Create: `content/.gitkeep`
- Create: `agents/__init__.py`
- Create: `agents/tools/__init__.py`
- Create: `scripts/__init__.py`
- Create: `tests/__init__.py`
- Create: `site/.gitkeep`
- Create: `export/.gitkeep`

- [ ] **Step 1: Create all directories with placeholders**

```bash
mkdir -p guidelines content agents/tools scripts tests site export
touch guidelines/.gitkeep content/.gitkeep site/.gitkeep export/.gitkeep scripts/__init__.py
touch agents/__init__.py agents/tools/__init__.py tests/__init__.py
```

- [ ] **Step 2: Commit**

```bash
git add guidelines/.gitkeep content/.gitkeep site/.gitkeep export/.gitkeep scripts/__init__.py agents/__init__.py agents/tools/__init__.py tests/__init__.py
git commit -m "chore: create directory structure"
```

---

## Chunk 2: Global Guidelines & Evaluation Rubric

### Task 3: Global authoring guidelines

**Files:**
- Create: `guidelines/global.md`

- [ ] **Step 1: Write guidelines/global.md**

This is the most critical document in the project — the autonomous "editor-in-chief". It must be comprehensive, precise, and unambiguous. The full content:

```markdown
# Globale Redaktionsrichtlinien / Global Authoring Guidelines

> Dieses Dokument steuert die autonome Kommentarerzeugung für alle acht Gesetze.
> Es ist die oberste Autorität für Qualität, Stil und Methodik.

## Leitbild

Dieser Kommentar macht das Schweizer Recht zugänglich, verständlich und nützlich
für jede Person, die es betrifft — von der Bundesrichterin bis zum Bürger, der
zum ersten Mal seine Rechte nachliest. Er steht in der Tradition der Schweizer
Gesetzgebung, dass das Recht dem Volk gehört, nicht dem Berufsstand.

## I. Grundsätze

### 1. Akademische Exzellenz
- Jede Aussage muss auf eine Primärquelle zurückführbar sein
  (Botschaft, BGE, Gesetzestext, Verordnung)
- Doktrinäre Positionen werden präzise zugeordnet — kein «die herrschende Lehre»
  ohne namentliche Nennung der Autoren mit Fundstelle
- Mindermeinungen werden fair dargestellt, nicht abgetan
- Keine Vereinfachung, die die Richtigkeit opfert

### 2. Präzision
- Legalbegriffe werden exakt so verwendet, wie sie im Gesetz definiert sind
- Keine Synonyme, wo das Gesetz einen bestimmten Begriff verwendet
  (z.B. «Schaden» ist nicht «Nachteil», «Besitz» ist nicht «Eigentum»)
- Zitate vollständig und überprüfbar:
  - BGE: BGE [Band] [Abteilung] [Seite] E. [Erwägung] (z.B. BGE 130 III 182 E. 5.5.1)
  - BGer: Urteil [Nummer] vom [Datum] E. [Erwägung] (z.B. Urteil 4A_123/2024 vom 15.3.2024 E. 3.2)
  - Literatur: [Autor], [Kurztitel], [Auflage] [Jahr], [Randnote/Seite]
    (z.B. Gauch/Schluep/Schmid, OR AT, 11. Aufl. 2020, N 2850)
  - Botschaften: BBl [Jahr] [Seite] (z.B. BBl 2001 4202)
- Zeitlicher Geltungsbereich explizit — «seit der Revision 2020» statt «nach neuem Recht»

### 3. Konzision
- Jeder Satz muss seinen Platz verdienen — kein Füllmaterial, keine Wiederholung,
  kein Hedging
- Doktrin-Ebene: umfassend aber dicht, wie ein Basler Kommentar, nicht wie ein Lehrbuch
- Rechtsprechungs-Ebene: nur Leitsatz und Relevanz, keine Sachverhaltsdarstellungen
- Was mit weniger Worten gesagt werden kann, ohne Bedeutung zu verlieren, muss kürzer gefasst werden

### 4. Relevanz
- Das praktisch Wichtigste zuerst
- Theoretische Debatten nur, wenn sie Ergebnisse beeinflussen
- Historischer Kontext nur, wenn er die aktuelle Auslegung erhellt
- Überholte Lehrmeinungen klar markieren, nicht ausführen

### 5. Zugänglichkeit
- Übersichts-Ebene: Ein motivierter Gymnasiast muss alles verstehen können
- Fachbegriffe werden bei erster Verwendung erklärt — in Klammern, nicht in Fussnoten
- Konkrete Beispiele, wo abstrakte Regeln sonst undurchsichtig bleiben
- Struktur leitet den Leser: Wichtigstes zuerst

### 6. Professionalität
- Neutraler, sachlicher Ton — der Kommentar beschreibt das Recht, er plädiert nie
- Kein «ich», keine rhetorischen Fragen, keine Hervorhebungsmarker
- Einheitliche Terminologie innerhalb und über alle acht Gesetze
- Formatierung dient dem Verständnis: Tabellen für Vergleiche, Listen für Tatbestandsmerkmale

## II. Ebenen-Spezifikationen

### Ebene 1: Übersicht (Summary)

**Zielgruppe:** Allgemeine Öffentlichkeit, Jurastudenten im Grundstudium

**Sprachliches Niveau:** B1 Deutsch — kein unerklärter Fachjargon

**Länge:** 150–300 Wörter

**Pflichtinhalt:**
1. Was regelt dieser Artikel? (Kern der Norm in 1–2 Sätzen)
2. Wen betrifft er? (Normadressaten)
3. Was ist die wichtigste praktische Konsequenz?
4. Mindestens ein konkretes Alltagsbeispiel

**Verbotene Elemente:**
- Keine Zitate (gehören in die Doktrin-Ebene)
- Keine Randziffern
- Keine Verweise auf Streitstände
- Keine Relativierungen («grundsätzlich», «in der Regel»), es sei denn,
  das Gesetz selbst verwendet diese Formulierung

**Stil:**
- Aktiv, direkt, konkret
- Kurze Sätze (max. 25 Wörter)
- Ein Gedanke pro Satz

### Ebene 2: Doktrin (Doctrinal Analysis)

**Zielgruppe:** Juristen, Wissenschaftler, fortgeschrittene Studenten

**Struktur:** Nummerierte Randziffern (N.)

**Pflichtabschnitte:**

```
N. 1–X:    Entstehungsgeschichte (Materialien, Botschaft, Revisionen)
N. X–Y:    Systematische Einordnung (Stellung im Gesetz, Verhältnis zu Nachbarartikeln)
N. Y–Z:    Tatbestandsmerkmale / Norminhalt (Element für Element)
N. Z–W:    Rechtsfolgen
N. W–V:    Streitstände (offene Fragen, Mehrheits-/Minderheitspositionen)
N. V–U:    Praxishinweise (praktische Anwendung, häufige Fehler)
```

**Zitierregeln:**
- Mindestens 3 Sekundärquellen pro Artikel
- Botschaft muss zitiert werden, wo verfügbar
- Mindestens die 3 wichtigsten BGE zum Artikel
- Jede doktrinäre Position mit Autorennennung und Fundstelle

**Querverweise:**
- Verweise auf andere Artikel im Format: → Art. [Nr.] [Gesetz]
- Querverweise müssen bidirektional sein (wenn OR 41 auf ZGB 28 verweist,
  muss ZGB 28 auf OR 41 zurückverweisen)

### Ebene 3: Rechtsprechung (Case Law Digest)

**Zielgruppe:** Praktiker, Wissenschaftler

**Struktur:** Thematisch gruppiert, innerhalb jeder Gruppe nach Wichtigkeit
(Leitentscheide zuerst), dann chronologisch

**Pro Eintrag:**
```
### [Thema]

**BGE [Band] [Abteilung] [Seite]** — [Datum]
[Leitsatz in 1–2 Sätzen, Regeste-Stil]
Relevanz: [Warum dieser Entscheid für diesen Artikel wichtig ist, 1 Satz]
> «[Wörtliches Zitat der Kernerwägung]» (E. [Nr.])
```

**Vollständigkeitsanforderung:**
- Alle in opencaselaw für diesen Artikel verzeichneten BGE müssen erscheinen
- Entscheide der letzten 12 Monate müssen aufgenommen werden, wenn relevant
- Veraltete Rechtsprechung wird als «überholt durch BGE [...]» markiert

## III. Übersetzung

- Deutsch ist die massgebliche Fassung
- Französisch und Italienisch werden maschinell aus dem Deutschen übersetzt
- Legalbegriffe müssen die offiziellen Übersetzungen gemäss Fedlex/termdat verwenden
- Übersetzungen werden bei jeder Änderung der Quell-Ebene neu generiert

## IV. Formatierung

### Markdown-Konventionen
- Überschriften: `#` für Artikeltitel, `##` für Abschnitte, `###` für Unterabschnitte
- Randziffern: Fettgedruckt am Zeilenanfang: `**N. 1** Text...`
- BGE-Verweise: Fettgedruckt: `**BGE 130 III 182**`
- Querverweise: Pfeil-Notation: `→ Art. 41 OR`
- Zitate: Blockquote mit Guillemets: `> «Zitat» (E. 5.5.1)`
- Listen: Für Tatbestandsmerkmale, Voraussetzungen, Rechtsfolgen
- Tabellen: Für Vergleiche (z.B. Abgrenzung OR 41 / OR 97)

### Dateinamen
- Artikel-Verzeichnisse: `art-001`, `art-002`, ... (dreistellig, nullgepadded)
- Artikel mit Buchstaben: `art-006a`, `art-319b`
- Ebenen: `summary.md`, `doctrine.md`, `caselaw.md`
- Übersetzungen: `summary.fr.md`, `summary.it.md`, etc.
```

- [ ] **Step 2: Commit**

```bash
git add guidelines/global.md
git commit -m "docs: add global authoring guidelines — the autonomous editor-in-chief"
```

---

### Task 4: Quality evaluation rubric

**Files:**
- Create: `guidelines/evaluate.md`

- [ ] **Step 1: Write guidelines/evaluate.md**

```markdown
# Qualitätsbewertung / Quality Evaluation Rubric

> Dieses Dokument definiert die Qualitätskriterien für die automatische Bewertung
> generierter Kommentarinhalte. Es ist das Äquivalent zu `val_bpb` in autoresearch:
> der objektive Massstab, der über Veröffentlichung oder Verwerfung entscheidet.

## I. Unverhandelbare Kriterien (binär)

Ein einziger Verstoss führt zur Ablehnung. Keine Ausnahmen.

### 1. Keine unbelegten Rechtsaussagen
- JEDE rechtliche Aussage in der Doktrin-Ebene muss eine Quelle haben
- Akzeptierte Quellen: BGE, BGer-Urteil, Botschaft (BBl), Fachliteratur mit Fundstelle
- Rein deskriptive Wiedergabe des Gesetzestextes ist ausgenommen
- **Prüfmethode:** Jeder Satz, der eine Rechtsaussage enthält, muss auf eine
  Zitation verweisen oder direkt aus dem Gesetzestext ableitbar sein

### 2. Keine faktischen Fehler
- Leitsätze müssen den tatsächlichen Entscheidinhalt wiedergeben
- **Prüfmethode:** Stichprobenartige Verifizierung gegen opencaselaw —
  Entscheidnummer, Datum, zitierte Erwägung müssen übereinstimmen

### 3. Keine fehlenden Leitentscheide
- Alle für diesen Artikel in opencaselaw verzeichneten BGE müssen in der
  Rechtsprechungs-Ebene erscheinen
- **Prüfmethode:** `find_leading_cases` für den Artikel aufrufen und gegen
  die Rechtsprechungs-Ebene abgleichen

### 4. Korrekte Legalbegriffe
- Begriffe müssen exakt dem Gesetzestext entsprechen
- **Prüfmethode:** Schlüsselbegriffe gegen den SR-Text abgleichen

### 5. Strukturelle Vollständigkeit
- Alle Pflichtabschnitte gemäss Ebenen-Spezifikation müssen vorhanden sein
- **Prüfmethode:** Abschnittserkennung im Markdown

## II. Bewertete Dimensionen (Schwellenwerte)

Jede Dimension wird auf einer Skala von 0.0 bis 1.0 bewertet.
Ein Score unter dem Schwellenwert führt zur Ablehnung und Neugenerierung.

### Präzision (Schwellenwert: 0.95)
Kriterien:
- Zitationsgenauigkeit: BGE-Nummern, Erwägungen, Daten korrekt
- Terminologische Exaktheit: Legalbegriffe stimmen mit SR-Text überein
- Zeitliche Zuordnung: Geltungsbereich korrekt angegeben
- Keine Verwechslung ähnlicher Begriffe oder Institute

### Konzision (Schwellenwert: 0.90)
Kriterien:
- Kein Satz, der ohne Informationsverlust gestrichen werden könnte
- Keine Wiederholungen innerhalb oder zwischen Ebenen
- Übersichts-Ebene: 150–300 Wörter
- Keine Füllformulierungen («es ist festzuhalten, dass», «in diesem Zusammenhang»)

### Zugänglichkeit (Schwellenwert: 0.90)
Kriterien (nur Übersichts-Ebene):
- Kein unerklärter Fachjargon
- Satzlänge ≤ 25 Wörter im Durchschnitt
- Mindestens ein konkretes Beispiel
- Logischer Aufbau: Was → Wer → Konsequenz

### Relevanz (Schwellenwert: 0.90)
Kriterien:
- Praktisch wichtigste Aspekte stehen zuerst
- Überholte Lehre als solche markiert, nicht ausgeführt
- Theoretische Debatten nur bei praktischer Auswirkung
- Aktuelle Rechtsprechung (letzte 12 Monate) berücksichtigt

### Akademische Strenge (Schwellenwert: 0.95)
Kriterien:
- Mindestens 3 Sekundärquellen pro Artikel (Doktrin-Ebene)
- Botschaft zitiert, wo verfügbar
- Streitstände mit Mehrheits-/Minderheitspositionen und Autorennennung
- Querverweise auf verwandte Artikel vorhanden

## III. Bewertungsablauf

```
Eingabe: Generierte Ebene (summary.md / doctrine.md / caselaw.md)

Schritt 1: Unverhandelbare Kriterien prüfen
  → Eines nicht erfüllt? → ABLEHNUNG mit Begründung

Schritt 2: Dimensionen bewerten (0.0–1.0)
  → Eine Dimension unter Schwellenwert? → ABLEHNUNG mit Scores und Feedback

Schritt 3: Alle bestanden → FREIGABE
  → Scores in meta.yaml schreiben

Wiederholungsschleife:
  → Max. 3 Versuche pro Ebene
  → Nach 3 Fehlversuchen → Markierung für menschliche Überprüfung
```

## IV. Evaluator-Prompt-Vorlage

Der Evaluator-Agent erhält für jede Bewertung:

```
Du bewertest einen generierten Kommentar zu Art. {article} {law}.

GESETZESTEXT:
{article_text}

GENERIERTER INHALT:
{generated_content}

EBENE: {layer_type}

Prüfe anhand der folgenden Kriterien:

1. UNVERHANDELBAR (bestanden/nicht bestanden):
   - Unbelegte Rechtsaussagen?
   - Faktische Fehler?
   - Fehlende Leitentscheide? (Referenzliste: {leading_cases})
   - Falsche Legalbegriffe?
   - Fehlende Pflichtabschnitte?

2. DIMENSIONEN (0.0–1.0):
   - Präzision (≥ 0.95):
   - Konzision (≥ 0.90):
   - Zugänglichkeit (≥ 0.90, nur Übersicht):
   - Relevanz (≥ 0.90):
   - Akademische Strenge (≥ 0.95):

Ausgabeformat:
{
  "verdict": "FREIGABE" | "ABLEHNUNG",
  "non_negotiables": { ... },
  "scores": { ... },
  "feedback": "Konkretes Feedback für Verbesserung"
}
```
```

- [ ] **Step 2: Commit**

```bash
git add guidelines/evaluate.md
git commit -m "docs: add quality evaluation rubric — the autonomous quality gate"
```

---

## Chunk 3: Per-Law Guidelines

### Task 5: BV guidelines

**Files:**
- Create: `guidelines/bv.md`

- [ ] **Step 1: Write guidelines/bv.md**

```markdown
# Redaktionsrichtlinien BV (Bundesverfassung, SR 101)

> Ergänzt `global.md` mit verfassungsrechtsspezifischem Kontext.

## Charakter des Gesetzes

Die BV ist die oberste Rechtsquelle der Schweiz. Ihre Normen sind:
- **Programmatisch** (Sozialziele, Art. 41): nicht direkt einklagbar
- **Grundrechtlich** (Art. 7–36): individuell einklagbar, Schrankenprüfung erforderlich
- **Organisatorisch** (Art. 143ff.): Kompetenzverteilung Bund/Kantone
- **Kompetenzrechtlich** (Art. 54ff.): Bundeszuständigkeiten

Diese unterschiedlichen Normcharaktere erfordern angepasste Kommentierung:
- Grundrechte: Schutzbereich → Eingriff → Rechtfertigung (Art. 36)
- Kompetenznormen: Umfang → Ausübung → Verhältnis zu kantonalem Recht
- Sozialziele: Rechtsnatur → programmatischer Gehalt → Justiziabilität

## Massgebliche Literatur

### Kommentare (Primärquellen für Doktrin-Ebene)
- St. Galler Kommentar zur BV (Ehrenzeller/Schindler/Schweizer/Vallender), 4. Aufl. 2023
- Basler Kommentar BV (Waldmann/Belser/Epiney), 2. Aufl. 2024
- Berner Kommentar BV (Bearbeitung laufend)

### Lehrbücher
- Häfelin/Haller/Keller/Thurnherr, Schweizerisches Bundesstaatsrecht, 10. Aufl. 2020
- Tschannen/Zimmerli/Müller, Allgemeines Verwaltungsrecht, 4. Aufl. 2014
- Müller/Schefer, Grundrechte in der Schweiz, 4. Aufl. 2008
- Rhinow/Schefer/Uebersax, Schweizerisches Verfassungsrecht, 3. Aufl. 2016

## Zentrale Querverweise

- Art. 5 BV (Rechtsstaatsprinzip) → durchzieht alle Kommentierungen
- Art. 8 BV (Rechtsgleichheit) ↔ Art. 29 BV (Verfahrensgarantien)
- Art. 9 BV (Willkürverbot) → zentral für Verwaltungsrecht (→ VwVG)
- Art. 36 BV (Grundrechtseinschränkungen) → referenziert bei jedem Grundrecht
- Art. 49 BV (Vorrang Bundesrecht) ↔ kantonale Gesetzgebung
- Art. 190 BV (Massgeblichkeit) → Verfassungsgerichtsbarkeit

## Besondere Hinweise

- **Verhältnismässigkeitsprüfung** (Art. 5 Abs. 2, Art. 36 Abs. 3): Bei jedem
  Grundrecht die dreigliedrige Prüfung (Eignung, Erforderlichkeit, Zumutbarkeit)
  konsistent darstellen
- **EMRK-Bezüge**: Wo Grundrechte der BV Pendants in der EMRK haben,
  Strassburger Rechtsprechung einbeziehen
- **Föderalismus**: Spannungsfeld Bund/Kantone bei Kompetenznormen immer thematisieren
```

- [ ] **Step 2: Commit**

```bash
git add guidelines/bv.md
git commit -m "docs: add BV-specific authoring guidelines"
```

---

### Task 6: ZGB guidelines

**Files:**
- Create: `guidelines/zgb.md`

- [ ] **Step 1: Write guidelines/zgb.md**

```markdown
# Redaktionsrichtlinien ZGB (Zivilgesetzbuch, SR 210)

> Ergänzt `global.md` mit zivilrechtsspezifischem Kontext.

## Charakter des Gesetzes

Das ZGB ist das Grundgesetz des schweizerischen Privatrechts. Es umfasst:
- **Personenrecht** (Art. 11–89a): Rechtsfähigkeit, Persönlichkeitsschutz, Vereine/Stiftungen
- **Familienrecht** (Art. 90–456): Ehe, Kindesrecht, Erwachsenenschutz
- **Erbrecht** (Art. 457–640): Gesetzliche Erbfolge, Verfügungen von Todes wegen
- **Sachenrecht** (Art. 641–977): Eigentum, Besitz, Grundbuch, Pfandrecht

Das ZGB zeichnet sich durch bewusst offene Formulierungen aus (Art. 1 ZGB:
Richterliche Rechtsfindung). Die Kommentierung muss diese Offenheit reflektieren
und die richterliche Konkretisierung durch Rechtsprechung dokumentieren.

## Massgebliche Literatur

### Kommentare
- Basler Kommentar ZGB I + II (Geiser/Fountoulakis), 7. Aufl. 2022/2023
- Berner Kommentar (div. Bearbeiter, laufend)
- Zürcher Kommentar (div. Bearbeiter, laufend)
- Kurzkommentar ZGB (Breitschmid/Jungo), 3. Aufl. 2023
- CHK — Handkommentar zum Schweizer Privatrecht (diverse), 3. Aufl. 2016

### Lehrbücher
- Tuor/Schnyder/Schmid/Jungo, Das Schweizerische Zivilgesetzbuch, 14. Aufl. 2015
- Hausheer/Aebi-Müller, Das Personenrecht des ZGB, 5. Aufl. 2020
- Hausheer/Geiser/Aebi-Müller, Das Familienrecht des ZGB, 6. Aufl. 2018
- Druey/Druey Just/Glanzmann, Grundriss des Erbrechts, 6. Aufl. 2015
- Schmid/Hürlimann-Kaup, Sachenrecht, 6. Aufl. 2022

## Zentrale Querverweise

- Art. 1 ZGB (Rechtsanwendung) → methodische Grundlage für alle Kommentierungen
- Art. 2 ZGB (Treu und Glauben, Rechtsmissbrauch) → durchzieht gesamtes Privatrecht
- Art. 3 ZGB (guter Glaube) ↔ Sachenrecht (gutgläubiger Erwerb)
- Art. 8 ZGB (Beweislast) → prozessuale Relevanz (→ ZPO)
- Art. 28 ZGB (Persönlichkeitsschutz) ↔ Art. 41 OR (Haftpflicht)
- Art. 641 ZGB (Eigentum) ↔ Art. 930ff. ZGB (Besitz)

## Besondere Hinweise

- **Revision Erbrecht 2023**: Änderungen seit 1.1.2023 konsequent kennzeichnen,
  Übergangsrecht (SchlT ZGB) beachten
- **Revision Erwachsenenschutz 2013**: Seit 1.1.2013 neues System (KESB),
  alte Vormundschaftsterminologie nicht verwenden
- **Randtitel**: Das ZGB verwendet Randtitel (Marginalien), die bei der
  Auslegung heranzuziehen sind — im Kommentar erwähnen
- **Art. 1 ZGB als Methode**: Bei Lücken die Rechtsfindungsmethode
  (Gesetz → Gewohnheitsrecht → Richterrecht) explizit ansprechen
```

- [ ] **Step 2: Commit**

```bash
git add guidelines/zgb.md
git commit -m "docs: add ZGB-specific authoring guidelines"
```

---

### Task 7: OR guidelines

**Files:**
- Create: `guidelines/or.md`

- [ ] **Step 1: Write guidelines/or.md**

```markdown
# Redaktionsrichtlinien OR (Obligationenrecht, SR 220)

> Ergänzt `global.md` mit obligationenrechtsspezifischem Kontext.

## Charakter des Gesetzes

Das OR ist der umfangreichste Teil des schweizerischen Privatrechts und
zugleich der fünfte Teil des ZGB (Art. 1–1186). Es gliedert sich in:
- **Allgemeiner Teil** (Art. 1–183): Entstehung, Wirkung, Erlöschen der Obligationen
- **Einzelne Vertragsverhältnisse** (Art. 184–551): Nominatverträge
- **Handelsgesellschaften** (Art. 552–926): AG, GmbH, Kollektiv-/Kommanditgesellschaft
- **Handelsregister, Geschäftsfirmen, Rechnungslegung** (Art. 927–963)
- **Wertpapiere** (Art. 965–1186)

## Massgebliche Literatur

### Kommentare
- Basler Kommentar OR I + II (Widmer Lüchinger/Oser), 7. Aufl. 2019/2020
- Berner Kommentar (div. Bearbeiter, laufend)
- Zürcher Kommentar (div. Bearbeiter, laufend)
- CHK — Handkommentar zum Schweizer Privatrecht (diverse)
- Kurzkommentar OR (Honsell), 2014

### Lehrbücher
- Gauch/Schluep/Schmid, Schweizerisches Obligationenrecht AT, 11. Aufl. 2020
- Schwenzer/Fountoulakis, Schweizerisches Obligationenrecht AT, 8. Aufl. 2020
- Huguenin, Obligationenrecht — Allgemeiner und Besonderer Teil, 3. Aufl. 2019
- Tercier/Bieri/Carron, Les contrats spéciaux, 5. Aufl. 2016
- Koller, Schweizerisches Obligationenrecht AT, 4. Aufl. 2017

## Zentrale Querverweise

- Art. 1 OR (Vertragsschluss) ↔ Art. 2 ZGB (Treu und Glauben)
- Art. 41 OR (Deliktshaftung) ↔ Art. 28 ZGB (Persönlichkeitsschutz)
- Art. 41 OR ↔ Art. 97 OR (Abgrenzung vertragliche/ausservertragliche Haftung)
- Art. 62 OR (ungerechtfertigte Bereicherung) → subsidiär zu Vertrag und Delikt
- Art. 97 OR (Vertragsverletzung) → Art. 107 OR (Verzug)
- Art. 319ff. OR (Arbeitsvertrag) → arbeitsrechtliche Spezialgesetzgebung
- Art. 716a OR (VR-Aufgaben) → Art. 754 OR (Organhaftung)

## Besondere Hinweise

- **Aktienrechtsrevision 2023**: Änderungen seit 1.1.2023 konsequent kennzeichnen
- **Drei Haftungssäulen**: Vertragshaftung (Art. 97ff.), Deliktshaftung (Art. 41ff.),
  ungerechtfertigte Bereicherung (Art. 62ff.) — Abgrenzung immer sauber darstellen
- **Innominatverträge**: Bei den Einzelnen Vertragsverhältnissen auf die Lückenfüllung
  durch den AT hinweisen
- **Doppelnatur OR/ZGB**: Das OR ist formal Teil des ZGB — Art. 7 ZGB
  (Allgemeine Bestimmungen des OR) beachten
```

- [ ] **Step 2: Commit**

```bash
git add guidelines/or.md
git commit -m "docs: add OR-specific authoring guidelines"
```

---

### Task 8: Remaining 5 per-law guidelines

**Files:**
- Create: `guidelines/zpo.md`
- Create: `guidelines/stgb.md`
- Create: `guidelines/stpo.md`
- Create: `guidelines/schkg.md`
- Create: `guidelines/vwvg.md`

- [ ] **Step 1: Write guidelines/zpo.md**

```markdown
# Redaktionsrichtlinien ZPO (Zivilprozessordnung, SR 272)

> Ergänzt `global.md` mit zivilprozessrechtsspezifischem Kontext.

## Charakter des Gesetzes

Die ZPO vereinheitlicht seit 2011 das Zivilprozessrecht in der Schweiz. Sie regelt:
- **Allgemeine Bestimmungen** (Art. 1–28): Geltungsbereich, Zuständigkeit, Grundsätze
- **Verfahrensvoraussetzungen** (Art. 29–67): Parteifähigkeit, Prozessstandschaft
- **Ordentliches Verfahren** (Art. 219–242): Schriftenwechsel, Beweisverfahren, Urteil
- **Besondere Verfahren** (Art. 243–268): Vereinfachtes, summarisches Verfahren
- **Rechtsmittel** (Art. 308–334): Berufung, Beschwerde, Revision
- **Schiedsgerichtsbarkeit** (Art. 353–399)

## Massgebliche Literatur

### Kommentare
- Basler Kommentar ZPO (Spühler/Tenchio/Infanger), 3. Aufl. 2017
- Berner Kommentar ZPO (Berner Kommentar, laufend)
- Kurzkommentar ZPO (Oberhammer/Domej/Haas), 3. Aufl. 2021
- Sutter-Somm/Hasenböhler/Leuenberger, Kommentar zur ZPO, 3. Aufl. 2016
- DIKE-Kommentar ZPO (Brunner/Gasser/Schwander), 2. Aufl. 2016

### Lehrbücher
- Sutter-Somm, Schweizerisches Zivilprozessrecht, 4. Aufl. 2024
- Staehelin/Staehelin/Grolimund, Zivilprozessrecht, 3. Aufl. 2019
- Meier, Schweizerisches Zivilprozessrecht, 2. Aufl. 2021

## Zentrale Querverweise

- Art. 8 ZGB (Beweislast) ↔ Art. 150–193 ZPO (Beweis)
- Art. 29 BV / Art. 6 EMRK ↔ Art. 52ff. ZPO (Verfahrensgrundsätze)
- Art. 88ff. SchKG ↔ Art. 243ff. ZPO (Streitwertgrenzen, Verfahrensart)
- Art. 257 ZPO (Rechtsschutz in klaren Fällen) → praxisrelevant

## Besondere Hinweise

- **Verfahrensart bestimmt alles**: Ordentliches / vereinfachtes / summarisches
  Verfahren — Streitwertgrenzen und Anwendungsbereich immer klarstellen
- **Dispositions- und Offizialmaxime**: Bei jedem Artikel angeben, welche Maxime gilt
- **Kantone**: Die ZPO lässt den Kantonen Spielraum (z.B. Gerichtsorganisation) —
  auf kantonale Besonderheiten hinweisen, wo relevant
```

- [ ] **Step 2: Write guidelines/stgb.md**

```markdown
# Redaktionsrichtlinien StGB (Strafgesetzbuch, SR 311.0)

> Ergänzt `global.md` mit strafrechtsspezifischem Kontext.

## Charakter des Gesetzes

Das StGB ist das Kerngesetz des schweizerischen Strafrechts. Aufbau:
- **Erstes Buch — Allgemeine Bestimmungen** (Art. 1–110):
  Geltungsbereich, Strafbarkeit, Strafen, Massnahmen, Verjährung
- **Zweites Buch — Besondere Bestimmungen** (Art. 111–332):
  Einzelne Straftatbestände (Leib/Leben, Vermögen, Ehre, Freiheit, etc.)
- **Drittes Buch — Einführung und Anwendung** (Art. 333–392):
  Übergangsrecht

## Massgebliche Literatur

### Kommentare
- Basler Kommentar StGB (Niggli/Wiprächtiger/Heimgartner), 4. Aufl. 2019
- Strafrecht I–IV (Trechsel/Pieth), 3. Aufl. 2018
- Kommentar StGB (Donatsch/Heimgartner/Tag/Wohlers), laufend
- Niggli/Maeder, Strafrecht BT (Zusammenfassungen der Rechtsprechung)

### Lehrbücher
- Donatsch/Tag, Strafrecht I, 10. Aufl. 2022
- Stratenwerth/Wohlers, Schweizerisches Strafgesetzbuch — Handkommentar, 3. Aufl. 2013
- Killias/Kuhn/Dongois/Aebi, Grundriss des Allgemeinen Teils des StGB, 2. Aufl. 2017
- Donatsch, Strafrecht III, 11. Aufl. 2018

## Zentrale Querverweise

- Art. 1 StGB (nulla poena sine lege) ↔ Art. 5 BV (Legalitätsprinzip)
- Art. 12 StGB (Vorsatz/Fahrlässigkeit) → zentral für alle BT-Tatbestände
- Art. 13 StGB (Sachverhaltsirrtum) ↔ Art. 21 StGB (Verbotsirrtum)
- Art. 47 StGB (Strafzumessung) → relevant bei jedem BT-Tatbestand
- Art. 122–125 StGB (Körperverletzung) ↔ Art. 41 OR (zivilrechtliche Haftung)
- Art. 138–147 StGB (Vermögensdelikte) → Abgrenzungen untereinander

## Besondere Hinweise

- **Deliktsstruktur**: Bei jedem BT-Tatbestand die Prüfungsreihenfolge einhalten:
  Objektiver Tatbestand → Subjektiver Tatbestand → Rechtswidrigkeit → Schuld
- **Sanktionenrecht**: Seit Revision 2018 neues Sanktionensystem —
  alte Terminologie vermeiden
- **Nebenstrafrecht**: Auf strafrechtliche Bestimmungen in Nebengesetzen
  hinweisen, wo relevant (SVG, BetmG, etc.)
- **Offizialdelikte vs. Antragsdelikte**: Bei jedem Tatbestand angeben
```

- [ ] **Step 3: Write guidelines/stpo.md**

```markdown
# Redaktionsrichtlinien StPO (Strafprozessordnung, SR 312.0)

> Ergänzt `global.md` mit strafprozessrechtsspezifischem Kontext.

## Charakter des Gesetzes

Die StPO vereinheitlicht seit 2011 das Strafprozessrecht. Struktur:
- **Grundlagen** (Art. 1–11): Geltungsbereich, Grundsätze
- **Strafbehörden** (Art. 12–30): Polizei, Staatsanwaltschaft, Gerichte
- **Parteien und Beteiligung** (Art. 104–121): Beschuldigte, Privatklägerschaft
- **Beweismittel** (Art. 139–195): Einvernahmen, Gutachten, Augenschein
- **Zwangsmassnahmen** (Art. 196–298d): Haft, Beschlagnahme, Überwachung
- **Vorverfahren** (Art. 299–327): Ermittlung, Untersuchung, Anklageerhebung
- **Erstinstanzliches Hauptverfahren** (Art. 328–351)
- **Rechtsmittel** (Art. 379–415): Berufung, Beschwerde, Revision

## Massgebliche Literatur

### Kommentare
- Basler Kommentar StPO (Niggli/Heer/Wiprächtiger), 3. Aufl. 2023
- Kommentar zur StPO (Donatsch/Lieber/Summers/Wohlers), 3. Aufl. 2020
- Goldschmid/Maurer/Sollberger, Kommentierte Textausgabe zur StPO, 2014

### Lehrbücher
- Schmid/Jositsch, Schweizerische Strafprozessordnung — Praxiskommentar, 3. Aufl. 2018
- Riklin, StPO Kommentar, 2. Aufl. 2014
- Wohlers/Bläsi, Strafprozessrecht, 2016

## Zentrale Querverweise

- Art. 3 StPO (Fairnessgebot) ↔ Art. 29/30 BV, Art. 6 EMRK
- Art. 10 StPO (Unschuldsvermutung) ↔ Art. 32 BV
- Art. 140/141 StPO (Beweisverwertungsverbote) → fundamentale Praxisrelevanz
- Art. 196ff. StPO (Zwangsmassnahmen) ↔ Art. 36 BV (Grundrechtseinschränkung)
- Art. 319 StPO (Einstellung) → häufiger Anfechtungsgegenstand

## Besondere Hinweise

- **Grundrechtsbezug**: Zwangsmassnahmen immer im Licht von Art. 36 BV kommentieren
- **Beweisverwertung**: Art. 140/141 als Schlüsselnormen — Praxis des BGer detailliert
- **Staatsanwaltschaftsmodell**: Die zentrale Rolle der StA im schweizerischen
  System erklären und von anderen Rechtsordnungen abgrenzen
```

- [ ] **Step 4: Write guidelines/schkg.md**

```markdown
# Redaktionsrichtlinien SchKG (Bundesgesetz über Schuldbetreibung und Konkurs, SR 281.1)

> Ergänzt `global.md` mit vollstreckungsrechtsspezifischem Kontext.

## Charakter des Gesetzes

Das SchKG regelt die Zwangsvollstreckung in der Schweiz. Struktur:
- **Allgemeine Bestimmungen** (Art. 1–45): Behörden, Fristen, Zustellung
- **Schuldbetreibung** (Art. 46–176): Betreibungsbegehren → Zahlungsbefehl →
  Rechtsvorschlag → Rechtsöffnung → Pfändung/Verwertung
- **Konkurs** (Art. 197–270): Konkurseröffnung, -verfahren, -schluss
- **Nachlassvertrag** (Art. 293–336): Aussergerichtlicher und gerichtlicher Nachlassvertrag
- **Arrest** (Art. 271–281)
- **Anfechtungsklagen** (Art. 285–292): Paulianische Anfechtung

## Massgebliche Literatur

### Kommentare
- Basler Kommentar SchKG I + II (Staehelin/Bauer/Lorandi), 3. Aufl. 2021
- Kommentar SchKG (Kren Kostkiewicz/Vock), 19. Aufl. 2023
- Amonn/Walther, Grundriss des Schuldbetreibungs- und Konkursrechts, 9. Aufl. 2013

### Lehrbücher
- Kren Kostkiewicz, Schuldbetreibungs- und Konkursrecht, 3. Aufl. 2018
- Cometta/Möckli, Schuldbetreibungs- und Konkursrecht, 2018

## Zentrale Querverweise

- Art. 79/80/82 SchKG (Rechtsöffnung) ↔ Art. 243ff. ZPO (Verfahrensart)
- Art. 271ff. SchKG (Arrest) ↔ Art. 261ff. ZPO (Vorsorgliche Massnahmen)
- Art. 285ff. SchKG (Pauliana) ↔ Art. 41 OR (deliktische Haftung)
- Art. 197ff. SchKG (Konkurs) → Art. 725ff. OR (Überschuldungsanzeige AG)

## Besondere Hinweise

- **Verfahrensablauf visualisieren**: Das SchKG-Verfahren ist ein Ablauf
  (Betreibungsbegehren → Zahlungsbefehl → Rechtsvorschlag → Rechtsöffnung →
  Pfändung/Verwertung) — diesen Ablauf in der Übersicht-Ebene immer klarstellen
- **Fristen sind zentral**: Verwirkungsfristen im SchKG haben existenzielle
  Konsequenzen — immer prominent darstellen
- **Betreibungsarten**: Betreibung auf Pfändung / Konkurs / Pfandverwertung —
  bei relevanten Artikeln die Abgrenzung darstellen
```

- [ ] **Step 5: Write guidelines/vwvg.md**

```markdown
# Redaktionsrichtlinien VwVG (Verwaltungsverfahrensgesetz, SR 172.021)

> Ergänzt `global.md` mit verwaltungsverfahrensrechtsspezifischem Kontext.

## Charakter des Gesetzes

Das VwVG regelt das Verwaltungsverfahren vor Bundesbehörden. Kompakt (74 Artikel),
aber als Verfahrensgesetz für das gesamte Bundesverwaltungsrecht zentral. Struktur:
- **Allgemeine Bestimmungen** (Art. 1–4): Geltungsbereich, Behörden
- **Allgemeine Verfahrensgrundsätze** (Art. 5–43): Verfügung, Parteien,
  Verfahrensrechte (rechtliches Gehör, Akteneinsicht)
- **Beschwerdeverfahren** (Art. 44–71a): Beschwerde an das BVGer

## Massgebliche Literatur

### Kommentare
- Praxiskommentar VwVG (Waldmann/Weissenberger), 3. Aufl. 2023
- Kommentar VwVG (Auer/Müller/Schindler), 2. Aufl. 2019
- Basler Kommentar VwVG (in Bearbeitung)

### Lehrbücher
- Häfelin/Müller/Uhlmann, Allgemeines Verwaltungsrecht, 8. Aufl. 2020
- Tschannen/Zimmerli/Müller, Allgemeines Verwaltungsrecht, 4. Aufl. 2014
- Moor/Poltier, Droit administratif, Vol. II, 3. Aufl. 2011

## Zentrale Querverweise

- Art. 5 VwVG (Verfügungsbegriff) → Schlüsselbegriff des Verwaltungsrechts
- Art. 29 VwVG (rechtliches Gehör) ↔ Art. 29 BV
- Art. 35 VwVG (Begründungspflicht) ↔ Art. 29 Abs. 2 BV
- Art. 48 VwVG (Beschwerdelegitimation) → auch für BGG relevant
- Art. 44ff. VwVG → Art. 31ff. VGG (Beschwerde ans BVGer)
- Art. 5 VwVG ↔ Art. 25a VwVG (Verfügung über Realakte)

## Besondere Hinweise

- **Verfügungsbegriff**: Art. 5 ist der Dreh- und Angelpunkt — jede Kommentierung
  muss klären, ob eine Verfügung vorliegt
- **Rechtliches Gehör**: Art. 29–33 besonders praxisrelevant, BGer-Rechtsprechung
  sehr umfangreich
- **Subsidiarität**: Das VwVG gilt subsidiär — Spezialverfahrensrecht geht vor.
  Bei jedem Artikel prüfen, ob relevante Spezialgesetze abweichen
- **Kantone**: Das VwVG gilt nur für Bundesbehörden. Auf kantonale
  Verwaltungsverfahrensgesetze hinweisen, wo sinnvoll
```

- [ ] **Step 6: Commit all 5 files**

```bash
git add guidelines/zpo.md guidelines/stgb.md guidelines/stpo.md guidelines/schkg.md guidelines/vwvg.md
git commit -m "docs: add per-law guidelines for ZPO, StGB, StPO, SchKG, VwVG"
```

---

## Chunk 4: Content Schema & Validation

### Task 9: Content schema definition with pydantic

**Files:**
- Create: `scripts/schema.py`
- Create: `tests/test_schema.py`

- [ ] **Step 1: Write failing test for meta.yaml schema**

Create `tests/test_schema.py`:

```python
import pytest
from scripts.schema import ArticleMeta, LayerMeta


def test_valid_meta():
    meta = ArticleMeta(
        law="OR",
        article=41,
        title="Haftung aus unerlaubter Handlung",
        sr_number="220",
        absatz_count=2,
        fedlex_url="https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de#art_41",
        layers={
            "summary": LayerMeta(
                last_generated="2026-03-10",
                version=1,
                quality_score=0.94,
            ),
            "doctrine": LayerMeta(
                last_generated="2026-03-10",
                version=1,
                quality_score=0.96,
            ),
            "caselaw": LayerMeta(
                last_generated="2026-03-10",
                version=1,
                quality_score=0.92,
            ),
        },
    )
    assert meta.law == "OR"
    assert meta.article == 41
    assert meta.layers["summary"].quality_score == 0.94


def test_invalid_law_rejected():
    with pytest.raises(ValueError):
        ArticleMeta(
            law="INVALID",
            article=1,
            title="Test",
            sr_number="999",
            absatz_count=1,
            fedlex_url="https://example.com",
            layers={},
        )


def test_quality_score_bounds():
    with pytest.raises(ValueError):
        LayerMeta(
            last_generated="2026-03-10",
            version=1,
            quality_score=1.5,
        )


def test_article_number_positive():
    with pytest.raises(ValueError):
        ArticleMeta(
            law="OR",
            article=0,
            title="Test",
            sr_number="220",
            absatz_count=1,
            fedlex_url="https://example.com",
            layers={},
        )


def test_meta_to_yaml_roundtrip():
    meta = ArticleMeta(
        law="BV",
        article=1,
        title="Schweizerische Eidgenossenschaft",
        sr_number="101",
        absatz_count=1,
        fedlex_url="https://www.fedlex.admin.ch/eli/cc/1999/404/de#art_1",
        layers={
            "summary": LayerMeta(last_generated="2026-03-10", version=1),
        },
    )
    yaml_str = meta.to_yaml()
    loaded = ArticleMeta.from_yaml(yaml_str)
    assert loaded == meta
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/jonashertner/projects/openlegalcommentary && uv run pytest tests/test_schema.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.schema'`

- [ ] **Step 3: Write scripts/schema.py**

```python
"""Content schema definitions for openlegalcommentary article metadata."""

from __future__ import annotations

from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator

LAWS = ("BV", "ZGB", "OR", "ZPO", "StGB", "StPO", "SchKG", "VwVG")

SR_NUMBERS: dict[str, str] = {
    "BV": "101",
    "ZGB": "210",
    "OR": "220",
    "ZPO": "272",
    "StGB": "311.0",
    "StPO": "312.0",
    "SchKG": "281.1",
    "VwVG": "172.021",
}

LayerName = Literal["summary", "doctrine", "caselaw"]


class LayerMeta(BaseModel):
    """Metadata for a single commentary layer."""

    last_generated: str = Field(description="ISO date of last generation")
    version: int = Field(ge=1, description="Monotonically increasing version number")
    quality_score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Composite quality score from evaluator"
    )
    trigger: str | None = Field(default=None, description="What triggered the last regeneration")
    last_reviewed: str | None = Field(default=None, description="ISO date of last human review")
    total_decisions: int | None = Field(
        default=None, ge=0, description="Total decisions cited (caselaw layer only)"
    )
    new_decisions_count: int | None = Field(
        default=None, ge=0, description="New decisions in last update (caselaw layer only)"
    )


class ArticleMeta(BaseModel):
    """Metadata for an article commentary directory (meta.yaml)."""

    law: str = Field(description="Law abbreviation")
    article: int = Field(gt=0, description="Article number")
    article_suffix: str = Field(default="", description="Article suffix, e.g. 'a', 'bis'")
    title: str = Field(min_length=1, description="Article title")
    sr_number: str = Field(description="Systematic collection number")
    absatz_count: int = Field(ge=1, description="Number of paragraphs (Absätze)")
    fedlex_url: str = Field(description="URL to article on Fedlex")
    layers: dict[str, LayerMeta] = Field(
        default_factory=dict, description="Per-layer metadata"
    )

    @field_validator("law")
    @classmethod
    def validate_law(cls, v: str) -> str:
        if v not in LAWS:
            raise ValueError(f"Unknown law: {v}. Must be one of {LAWS}")
        return v

    @field_validator("layers")
    @classmethod
    def validate_layer_names(cls, v: dict[str, LayerMeta]) -> dict[str, LayerMeta]:
        valid_names = {"summary", "doctrine", "caselaw"}
        for key in v:
            if key not in valid_names:
                raise ValueError(f"Unknown layer: {key}. Must be one of {valid_names}")
        return v

    def to_yaml(self) -> str:
        """Serialize to YAML string."""
        return yaml.dump(
            self.model_dump(exclude_none=True),
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    @classmethod
    def from_yaml(cls, yaml_str: str) -> ArticleMeta:
        """Deserialize from YAML string."""
        data = yaml.safe_load(yaml_str)
        return cls(**data)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/jonashertner/projects/openlegalcommentary && uv run pytest tests/test_schema.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/schema.py tests/test_schema.py
git commit -m "feat: add content schema with pydantic validation and YAML roundtrip"
```

---

### Task 10: Content directory validator

**Files:**
- Create: `scripts/validate_content.py`
- Create: `tests/test_validate_content.py`

- [ ] **Step 1: Write failing tests for content validator**

Create `tests/test_validate_content.py`:

```python
import os
import pytest
from pathlib import Path
from scripts.validate_content import validate_article_dir, validate_content_tree


@pytest.fixture
def valid_article(tmp_path: Path) -> Path:
    """Create a valid article directory."""
    art_dir = tmp_path / "or" / "art-041"
    art_dir.mkdir(parents=True)

    (art_dir / "meta.yaml").write_text(
        "law: OR\n"
        "article: 41\n"
        "title: Haftung aus unerlaubter Handlung\n"
        "sr_number: '220'\n"
        "absatz_count: 2\n"
        "fedlex_url: https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de#art_41\n"
        "layers:\n"
        "  summary:\n"
        "    last_generated: '2026-03-10'\n"
        "    version: 1\n"
        "  doctrine:\n"
        "    last_generated: '2026-03-10'\n"
        "    version: 1\n"
        "  caselaw:\n"
        "    last_generated: '2026-03-10'\n"
        "    version: 1\n"
    )
    (art_dir / "summary.md").write_text("# Übersicht\n\nPlaceholder.")
    (art_dir / "doctrine.md").write_text("# Doktrin\n\n**N. 1** Placeholder.")
    (art_dir / "caselaw.md").write_text("# Rechtsprechung\n\nPlaceholder.")
    return art_dir


@pytest.fixture
def missing_layer(tmp_path: Path) -> Path:
    """Article directory missing caselaw.md."""
    art_dir = tmp_path / "or" / "art-041"
    art_dir.mkdir(parents=True)

    (art_dir / "meta.yaml").write_text(
        "law: OR\n"
        "article: 41\n"
        "title: Test\n"
        "sr_number: '220'\n"
        "absatz_count: 1\n"
        "fedlex_url: https://example.com\n"
        "layers:\n"
        "  summary:\n"
        "    last_generated: '2026-03-10'\n"
        "    version: 1\n"
    )
    (art_dir / "summary.md").write_text("# Übersicht\n\nTest.")
    (art_dir / "doctrine.md").write_text("# Doktrin\n\nTest.")
    # caselaw.md intentionally missing
    return art_dir


def test_valid_article_passes(valid_article: Path):
    errors = validate_article_dir(valid_article)
    assert errors == []


def test_missing_layer_detected(missing_layer: Path):
    errors = validate_article_dir(missing_layer)
    assert any("caselaw.md" in e for e in errors)


def test_missing_meta_detected(tmp_path: Path):
    art_dir = tmp_path / "or" / "art-001"
    art_dir.mkdir(parents=True)
    (art_dir / "summary.md").write_text("Test")
    errors = validate_article_dir(art_dir)
    assert any("meta.yaml" in e for e in errors)


def test_content_tree_validation(valid_article: Path):
    content_root = valid_article.parent.parent  # tmp_path
    results = validate_content_tree(content_root)
    assert results["total_articles"] == 1
    assert results["errors"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_validate_content.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write scripts/validate_content.py**

```python
"""Validate the content/ directory structure and metadata."""

from __future__ import annotations

from pathlib import Path

from scripts.schema import ArticleMeta, LAWS

REQUIRED_LAYERS = ("summary.md", "doctrine.md", "caselaw.md")
LAW_DIRS = {law.lower(): law for law in LAWS}


def validate_article_dir(article_dir: Path) -> list[str]:
    """Validate a single article directory. Returns list of error messages."""
    errors: list[str] = []
    prefix = f"{article_dir.parent.name}/{article_dir.name}"

    # Check meta.yaml exists and is valid
    meta_path = article_dir / "meta.yaml"
    if not meta_path.exists():
        errors.append(f"{prefix}: missing meta.yaml")
        return errors  # Can't validate further without meta

    try:
        meta = ArticleMeta.from_yaml(meta_path.read_text())
    except Exception as e:
        errors.append(f"{prefix}: invalid meta.yaml — {e}")
        return errors

    # Check required layer files exist
    for layer_file in REQUIRED_LAYERS:
        if not (article_dir / layer_file).exists():
            errors.append(f"{prefix}: missing {layer_file}")

    # Check layer files declared in meta have corresponding files
    for layer_name in meta.layers:
        expected_file = f"{layer_name}.md"
        if not (article_dir / expected_file).exists():
            errors.append(f"{prefix}: meta.yaml declares layer '{layer_name}' but {expected_file} missing")

    # Check law directory matches meta.law
    law_dir = article_dir.parent.name
    if law_dir in LAW_DIRS and LAW_DIRS[law_dir] != meta.law:
        errors.append(
            f"{prefix}: directory is under '{law_dir}/' but meta.yaml says law='{meta.law}'"
        )

    return errors


def validate_content_tree(content_root: Path) -> dict:
    """Validate the entire content/ directory tree."""
    all_errors: list[str] = []
    total_articles = 0

    for law_dir in sorted(content_root.iterdir()):
        if not law_dir.is_dir() or law_dir.name.startswith("."):
            continue
        for article_dir in sorted(law_dir.iterdir()):
            if not article_dir.is_dir() or not article_dir.name.startswith("art-"):
                continue
            total_articles += 1
            all_errors.extend(validate_article_dir(article_dir))

    return {
        "total_articles": total_articles,
        "errors": all_errors,
        "valid": len(all_errors) == 0,
    }


if __name__ == "__main__":
    import sys

    content_path = Path("content")
    if not content_path.exists():
        print("No content/ directory found.")
        sys.exit(1)

    results = validate_content_tree(content_path)
    print(f"Validated {results['total_articles']} articles.")

    if results["errors"]:
        print(f"\n{len(results['errors'])} errors found:\n")
        for error in results["errors"]:
            print(f"  ✗ {error}")
        sys.exit(1)
    else:
        print("All valid.")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_validate_content.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/validate_content.py tests/test_validate_content.py
git commit -m "feat: add content directory validator with tests"
```

---

## Chunk 5: Fedlex Article Enumerator

### Task 11: Fedlex HTML article enumerator

The Fedlex SPARQL endpoint (`fedlex.data.admin.ch/sparqlendpoint`) does not reliably
expose article-level data — the RDF model uses `jolux:LegalResourceSubdivision` with
sparse coverage. Instead, we fetch the consolidated HTML law pages from Fedlex and
parse article anchors from the DOM. This is reliable because Fedlex renders all articles
with consistent `id="art_XX"` anchors in the HTML.

**Files:**
- Create: `scripts/fetch_articles.py`
- Create: `tests/test_fetch_articles.py`
- Modify: `pyproject.toml` (add pytest marker)

- [ ] **Step 1: Register pytest network marker**

Add to `pyproject.toml` under `[tool.pytest.ini_options]`:
```toml
markers = ["network: requires network access to Fedlex"]
```

- [ ] **Step 2: Write tests for article fetcher**

Create `tests/test_fetch_articles.py`:

```python
import pytest
from scripts.fetch_articles import (
    parse_articles_from_html,
    article_dir_name,
    build_fedlex_url,
    LAW_ELI_PATHS,
)


def test_law_eli_paths_has_all_laws():
    expected = {"BV", "ZGB", "OR", "ZPO", "StGB", "StPO", "SchKG", "VwVG"}
    assert set(LAW_ELI_PATHS.keys()) == expected


def test_article_dir_name():
    assert article_dir_name(1) == "art-001"
    assert article_dir_name(41) == "art-041"
    assert article_dir_name(1186) == "art-1186"


def test_article_dir_name_with_suffix():
    assert article_dir_name(6, suffix="a") == "art-006a"
    assert article_dir_name(319, suffix="bis") == "art-319bis"


def test_build_fedlex_url():
    url = build_fedlex_url("BV")
    assert url == "https://www.fedlex.admin.ch/eli/cc/1999/404/de"


def test_parse_articles_from_html():
    """Test parsing article anchors from sample HTML."""
    sample_html = '''
    <html><body>
    <div id="art_1">
        <h6 class="heading"><span class="article-num">Art. 1</span>
        <span class="article-title">Schweizerische Eidgenossenschaft</span></h6>
    </div>
    <div id="art_2">
        <h6 class="heading"><span class="article-num">Art. 2</span>
        <span class="article-title">Zweck</span></h6>
    </div>
    <div id="art_6a">
        <h6 class="heading"><span class="article-num">Art. 6<i>a</i></span>
        <span class="article-title">Sechster Artikel a</span></h6>
    </div>
    </body></html>
    '''
    articles = parse_articles_from_html(sample_html)
    assert len(articles) == 3
    assert articles[0]["number"] == 1
    assert articles[0]["suffix"] == ""
    assert articles[0]["title"] == "Schweizerische Eidgenossenschaft"
    assert articles[2]["number"] == 6
    assert articles[2]["suffix"] == "a"


def test_parse_articles_deduplicates():
    """Duplicate anchors should be collapsed."""
    sample_html = '''
    <html><body>
    <div id="art_1"><h6 class="heading"><span class="article-num">Art. 1</span>
    <span class="article-title">Title</span></h6></div>
    <div id="art_1"><h6 class="heading"><span class="article-num">Art. 1</span>
    <span class="article-title">Title</span></h6></div>
    </body></html>
    '''
    articles = parse_articles_from_html(sample_html)
    assert len(articles) == 1


@pytest.mark.network
async def test_fetch_vwvg_articles_live():
    """Integration test — requires network. Run with: pytest -m network"""
    from scripts.fetch_articles import fetch_articles

    articles = await fetch_articles("VwVG")  # Smallest law, ~74 articles
    assert len(articles) >= 50
    assert all("number" in a for a in articles)
    assert all("title" in a for a in articles)
```

- [ ] **Step 3: Run tests (unit only) to verify they fail**

Run: `uv run pytest tests/test_fetch_articles.py -v -m "not network"`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Write scripts/fetch_articles.py**

```python
"""Fetch article lists from Fedlex consolidated HTML pages for Swiss federal laws."""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import httpx

from scripts.schema import SR_NUMBERS

# ELI paths for the consolidated version of each law on Fedlex.
# These are the historical compilation references, NOT the SR numbers.
LAW_ELI_PATHS: dict[str, str] = {
    "BV": "1999/404",
    "ZGB": "24/233_245_233",
    "OR": "27/317_321_377",
    "ZPO": "2010/262",
    "StGB": "54/757_781_799",
    "StPO": "2010/267",
    "SchKG": "11/529_488_529",
    "VwVG": "1969/737_757_755",
}


def build_fedlex_url(law: str, lang: str = "de") -> str:
    """Build the Fedlex URL for a law's consolidated HTML page."""
    path = LAW_ELI_PATHS[law]
    return f"https://www.fedlex.admin.ch/eli/cc/{path}/{lang}"


def build_article_fedlex_url(law: str, number: int, suffix: str = "", lang: str = "de") -> str:
    """Build the Fedlex URL for a specific article."""
    path = LAW_ELI_PATHS[law]
    return f"https://www.fedlex.admin.ch/eli/cc/{path}/{lang}#art_{number}{suffix}"


def parse_articles_from_html(html: str) -> list[dict]:
    """Parse article entries from Fedlex consolidated law HTML.

    Fedlex renders articles as <div id="art_XX"> with nested headings containing
    article numbers and titles. This parser extracts all articles by matching
    these DOM patterns.
    """
    articles: list[dict] = []
    seen: set[str] = set()

    # Match div ids like art_1, art_6a, art_319bis, art_100
    for match in re.finditer(
        r'<div[^>]*\bid=["\']art_(\d+)([a-z]*)["\']',
        html,
    ):
        raw_num = match.group(1)
        suffix = match.group(2)
        anchor_id = f"art_{raw_num}{suffix}"

        if anchor_id in seen:
            continue
        seen.add(anchor_id)

        number = int(raw_num)

        # Try to extract title from nearby article-title span
        # Search within 500 chars after the anchor for the title span
        search_region = html[match.start() : match.start() + 500]
        title_match = re.search(
            r'class=["\']article-title["\'][^>]*>([^<]+)<',
            search_region,
        )
        title = title_match.group(1).strip() if title_match else ""

        articles.append({
            "number": number,
            "suffix": suffix,
            "title": title,
            "raw_num": f"{raw_num}{suffix}",
        })

    # Sort by number, then suffix
    articles.sort(key=lambda a: (a["number"], a["suffix"]))
    return articles


def article_dir_name(number: int, suffix: str = "") -> str:
    """Generate directory name for an article. E.g., 41 -> 'art-041', 6a -> 'art-006a'."""
    padded = str(number).zfill(3)
    return f"art-{padded}{suffix}"


async def fetch_articles(law: str) -> list[dict]:
    """Fetch all articles for a law by scraping its Fedlex consolidated HTML page."""
    if law not in LAW_ELI_PATHS:
        raise ValueError(f"Unknown law: {law}. Must be one of {list(LAW_ELI_PATHS.keys())}")

    url = build_fedlex_url(law)

    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        response = await client.get(
            url,
            headers={
                "Accept": "text/html",
                "User-Agent": "openlegalcommentary/0.1 (https://openlegalcommentary.ch)",
            },
        )
        response.raise_for_status()
        return parse_articles_from_html(response.text)


async def fetch_all_laws() -> dict[str, list[dict]]:
    """Fetch article lists for all 8 laws."""
    results: dict[str, list[dict]] = {}
    for law in LAW_ELI_PATHS:
        print(f"Fetching {law}...")
        results[law] = await fetch_articles(law)
        print(f"  → {len(results[law])} articles")
    return results


if __name__ == "__main__":
    results = asyncio.run(fetch_all_laws())

    output = {}
    for law, articles in results.items():
        output[law] = {
            "sr_number": SR_NUMBERS[law],
            "article_count": len(articles),
            "articles": articles,
        }

    out_path = Path("scripts/article_lists.json")
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nSaved to {out_path}")
    print(f"Total: {sum(len(a) for a in results.values())} articles across {len(results)} laws")
```

Note: Fedlex uses client-side rendering (Angular). If `fetch_articles` returns empty results
because the HTML contains only a JS app shell, fall back to fetching the XML version at
`https://www.fedlex.admin.ch/filestore/fedlex.data.admin.ch/eli/cc/{path}/de/xml/...`
or use the `droid-f/fedlex` GitHub repo which mirrors consolidated JSON objects. The
integration test (Step 6) will verify which approach works.

- [ ] **Step 5: Run unit tests to verify they pass**

Run: `uv run pytest tests/test_fetch_articles.py -v -m "not network"`
Expected: 6 passed

- [ ] **Step 6: Run integration test (requires network)**

Run: `uv run pytest tests/test_fetch_articles.py -v -m network`
Expected: 1 passed (fetches VwVG articles from Fedlex)

If this fails because Fedlex serves a JS-only page, switch the implementation to fetch
from the `droid-f/fedlex` GitHub repo instead (raw JSON files at predictable URLs).
Debug directly: `uv run python scripts/fetch_articles.py`

- [ ] **Step 7: Commit**

```bash
git add scripts/fetch_articles.py tests/test_fetch_articles.py pyproject.toml
git commit -m "feat: add Fedlex HTML article enumerator for all 8 laws"
```

---

### Task 12: Content directory scaffolder

**Files:**
- Create: `scripts/scaffold_content.py`
- Create: `tests/test_scaffold_content.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_scaffold_content.py`:

```python
import pytest
from pathlib import Path
from scripts.scaffold_content import scaffold_article, scaffold_law
from scripts.schema import ArticleMeta


@pytest.fixture
def content_root(tmp_path: Path) -> Path:
    return tmp_path / "content"


def test_scaffold_article_creates_files(content_root: Path):
    scaffold_article(
        content_root=content_root,
        law="OR",
        number=41,
        suffix="",
        title="Haftung aus unerlaubter Handlung",
        absatz_count=2,
    )

    art_dir = content_root / "or" / "art-041"
    assert art_dir.exists()
    assert (art_dir / "meta.yaml").exists()
    assert (art_dir / "summary.md").exists()
    assert (art_dir / "doctrine.md").exists()
    assert (art_dir / "caselaw.md").exists()

    # Verify meta.yaml is valid
    meta = ArticleMeta.from_yaml((art_dir / "meta.yaml").read_text())
    assert meta.law == "OR"
    assert meta.article == 41


def test_scaffold_article_does_not_overwrite(content_root: Path):
    scaffold_article(content_root, "OR", 41, "", "Title", 1)
    (content_root / "or" / "art-041" / "doctrine.md").write_text("Custom content")

    scaffold_article(content_root, "OR", 41, "", "Title", 1)
    assert (content_root / "or" / "art-041" / "doctrine.md").read_text() == "Custom content"


def test_scaffold_law(content_root: Path):
    articles = [
        {"number": 1, "suffix": "", "title": "Entstehung"},
        {"number": 2, "suffix": "", "title": "Vertrag"},
    ]
    scaffold_law(content_root, "OR", articles)

    assert (content_root / "or" / "art-001" / "meta.yaml").exists()
    assert (content_root / "or" / "art-002" / "meta.yaml").exists()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_scaffold_content.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write scripts/scaffold_content.py**

```python
"""Scaffold content directories for articles based on Fedlex article lists."""

from __future__ import annotations

from pathlib import Path

from scripts.fetch_articles import article_dir_name, build_article_fedlex_url
from scripts.schema import ArticleMeta, LayerMeta, SR_NUMBERS


def scaffold_article(
    content_root: Path,
    law: str,
    number: int,
    suffix: str,
    title: str,
    absatz_count: int = 1,
) -> Path:
    """Create an article directory with meta.yaml and placeholder layer files.

    Does not overwrite existing files.
    """
    dir_name = article_dir_name(number, suffix)
    art_dir = content_root / law.lower() / dir_name
    art_dir.mkdir(parents=True, exist_ok=True)

    sr = SR_NUMBERS.get(law, "")
    fedlex_url = build_article_fedlex_url(law, number, suffix)

    # Write meta.yaml only if it doesn't exist
    meta_path = art_dir / "meta.yaml"
    if not meta_path.exists():
        meta = ArticleMeta(
            law=law,
            article=number,
            article_suffix=suffix,
            title=title,
            sr_number=sr,
            absatz_count=absatz_count,
            fedlex_url=fedlex_url,
            layers={},
        )
        meta_path.write_text(meta.to_yaml())

    # Create placeholder layer files only if they don't exist
    placeholders = {
        "summary.md": f"# Übersicht\n\nArt. {number}{suffix} {law} — {title}\n",
        "doctrine.md": f"# Doktrin\n\nArt. {number}{suffix} {law} — {title}\n",
        "caselaw.md": f"# Rechtsprechung\n\nArt. {number}{suffix} {law} — {title}\n",
    }

    for filename, content in placeholders.items():
        file_path = art_dir / filename
        if not file_path.exists():
            file_path.write_text(content)

    return art_dir


def scaffold_law(
    content_root: Path,
    law: str,
    articles: list[dict],
) -> None:
    """Scaffold all article directories for a law."""
    for article in articles:
        scaffold_article(
            content_root=content_root,
            law=law,
            number=article["number"],
            suffix=article.get("suffix", ""),
            title=article.get("title", ""),
        )


if __name__ == "__main__":
    import asyncio
    import json
    from pathlib import Path

    from scripts.fetch_articles import fetch_all_laws

    content_root = Path("content")

    # Try loading cached article lists first
    cache_path = Path("scripts/article_lists.json")
    if cache_path.exists():
        print("Using cached article lists...")
        data = json.loads(cache_path.read_text())
        for law, info in data.items():
            print(f"Scaffolding {law} ({info['article_count']} articles)...")
            scaffold_law(content_root, law, info["articles"])
    else:
        print("Fetching article lists from Fedlex...")
        results = asyncio.run(fetch_all_laws())
        for law, articles in results.items():
            print(f"Scaffolding {law} ({len(articles)} articles)...")
            scaffold_law(content_root, law, articles)

    print("Done.")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_scaffold_content.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/scaffold_content.py tests/test_scaffold_content.py
git commit -m "feat: add content directory scaffolder from article lists"
```

---

### Task 13: Run full lint and test suite

- [ ] **Step 1: Run ruff**

Run: `cd /Users/jonashertner/projects/openlegalcommentary && uv run ruff check .`
Expected: No errors (fix any that appear)

- [ ] **Step 2: Run full test suite**

Run: `uv run pytest -v -m "not network"`
Expected: All tests pass

- [ ] **Step 3: Commit any lint fixes**

If ruff found issues, fix and commit:
```bash
git add -A
git commit -m "style: fix lint issues"
```

---

### Task 14: Create GitHub repository

- [ ] **Step 1: Create remote repo**

```bash
cd /Users/jonashertner/projects/openlegalcommentary
gh repo create openlegalcommentary --public --source=. --push --description "Open-access AI-generated legal commentary on Swiss federal law"
```

- [ ] **Step 2: Verify repo is live**

```bash
gh repo view openlegalcommentary --web
```
