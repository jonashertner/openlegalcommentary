# Redaktionsrichtlinien — Konzeptseiten (Cross-Cutting Concepts)

> Dieses Dokument ergänzt global.md und gilt für alle Konzeptseiten. Konzeptseiten sind KEINE Artikelkommentare — sie synthetisieren über mehrere Bestimmungen und Gesetze hinweg.

---

## I. Zweck

Konzeptseiten bilden doktrinäre Konzepte ab, die sich über mehrere Normen und Gesetze erstrecken. Sie machen die **Verbindungen** zwischen Bestimmungen sichtbar, die in isolierten Artikelkommentaren untergehen.

Beispiel: *Berufsgeheimnis* berührt Art. 13 BGFA, Art. 171 StPO, Art. 160 ZPO, Art. 321 StGB, Art. 13 BV — erst die Gesamtschau ergibt ein vollständiges Bild.

---

## II. Struktur

Jede Konzeptseite folgt dieser Gliederung:

### 1. Verfassungsrechtliche Grundlage
Welche verfassungsrechtlichen Prinzipien tragen das Konzept? Grundrechte, Kompetenznormen, Staatsziele.

### 2. Bundesgesetzlicher Rahmen
Die relevanten Gesetzesbestimmungen im Überblick — nicht als Aufzählung, sondern als Darstellung der systematischen Beziehungen.

### 3. Massgebliche Rechtsprechung
Leitentscheide, die das Konzept geformt haben. Fokus auf Entscheide, die **mehrere** der betroffenen Bestimmungen verbinden.

### 4. Praktische Anwendung
Wie wirkt das Konzept in der Praxis? Fallkonstellationen, typische Konflikte, Handlungsempfehlungen.

### 5. Offene Fragen
Ungeklärte Punkte, laufende Kontroversen, absehbare Entwicklungen.

---

## III. Frontmatter

Jede Konzeptseite hat eine `meta.yaml` mit folgenden Feldern:

```yaml
type: concept
slug: berufsgeheimnis          # URL-kompatibler Bezeichner
title: Berufsgeheimnis          # Titel in der Hauptsprache
provisions:                     # Betroffene Bestimmungen
  - bgfa/art-013
  - stpo/art-171
  - zpo/art-160
  - stgb/art-321
  - bv/art-013
confidence: settled | contested | evolving
author_status: draft | reviewed | contested
tags: []
last_generated: ""
quality_score: null
```

- **provisions**: Liste aller betroffenen Bestimmungen im Format `{law}/art-{number}`
- **confidence**: `settled` (gefestigte Rechtslage), `contested` (umstrittene Fragen), `evolving` (laufende Entwicklung)
- **author_status**: `draft` (Erstentwurf), `reviewed` (qualitätsgeprüft), `contested` (Widerspruch eingegangen)

---

## IV. Qualitätsstandards

### Gleiche Strenge wie Doktrin
Konzeptseiten unterliegen denselben akademischen Standards wie die Doktrinebene (global.md, Abschnitt II.2). Jede Rechtsaussage ist quellengestützt. Doktrinäre Positionen werden namentlich zugeschrieben.

### Fokus auf Verbindungen
Der Mehrwert einer Konzeptseite liegt in der **Synthese**. Eine blosse Aneinanderreihung von Artikelkommentaren ist unzulässig. Die Konzeptseite muss zeigen:

- Wie die Bestimmungen zusammenwirken
- Wo Spannungen und Widersprüche bestehen
- Welche Bestimmung in welcher Situation vorgeht

### Querverweise
Jede Konzeptseite verweist auf die betroffenen Artikelkommentare und umgekehrt. Die Pfeilnotation aus global.md gilt.

### Randziffern
Konzeptseiten verwenden Randziffern (N. 1, N. 2 usw.) wie Doktrinseiten.
