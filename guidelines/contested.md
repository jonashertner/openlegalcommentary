# Redaktionsrichtlinien — Streitfragen (Contested Questions)

> Dieses Dokument ergänzt global.md und gilt für alle Streitfragenseiten. Streitfragenseiten präsentieren MEHRERE Positionen zu genuinen Rechtsfragen, ohne sie zu entscheiden.

---

## I. Zweck

Streitfragenseiten machen Unsicherheit sichtbar — das Kintsugi-Prinzip: Die Brüche zeigen, statt sie zu verbergen. In einer rechtsstaatlichen Ordnung ist es ebenso wichtig zu wissen, **wo** vernünftige Juristinnen und Juristen uneins sind, wie die gefestigte Rechtslage zu kennen.

---

## II. Struktur

Jede Streitfragenseite folgt dieser Gliederung:

### 1. Die Frage
Präzise Formulierung der strittigen Rechtsfrage. Nicht vage («Ist Art. X problematisch?»), sondern scharf («Schliesst das Berufsgeheimnis nach Art. 13 BGFA auch die Ergebnisse interner Untersuchungen ein, die ein Unternehmensanwalt durchführt?»).

### 2. Position A
- **These** in einem Satz
- **Argumente**: Die stärkste Version der Position, mit Quellenbelegen
- **Vertreter**: Wer vertritt diese Position? (Autoren, Gerichte, Behörden)
- **Schwächen**: Ehrliche Darstellung der Gegenargumente

### 3. Position B
- Gleiche Struktur wie Position A

### 4. Position C (falls vorhanden)
- Gleiche Struktur

### 5. Analyse
- Wo genau liegt die Divergenz? (Unterschiedliche Auslegungsmethoden? Unterschiedliche Gewichtung von Interessen? Unterschiedliche Sachverhaltsannahmen?)
- Gibt es Annäherungen oder Kompromisslinien?

### 6. Implikationen
- Was folgt aus jeder Position für die Praxis?
- Welche Fälle würden unterschiedlich entschieden?

### 7. Ungelöst
- Was bleibt offen? Welche Entwicklungen sind absehbar?

---

## III. Frontmatter

Jede Streitfragenseite hat eine `meta.yaml` mit folgenden Feldern:

```yaml
type: contested
slug: open-methodology-bgfa     # URL-kompatibler Bezeichner
title: "Open-Source-Rechtskommentar und anwaltliche Berufsausübung"
question: "Stellt die Veröffentlichung eines KI-generierten Rechtskommentars eine bewilligungspflichtige anwaltliche Tätigkeit dar?"
provisions:
  - bgfa/art-012
  - bgfa/art-013
positions:
  - label: "Keine anwaltliche Tätigkeit"
    summary: "Rechtskommentierung ist Wissenschaft, nicht Rechtsberatung"
  - label: "Bewilligungspflichtig"
    summary: "Personalisierte Rechtsaussagen erfordern Anwaltszulassung"
author_status: draft | reviewed | contested
tags: []
last_generated: ""
```

- **question**: Die strittige Rechtsfrage als vollständiger Satz
- **provisions**: Alle betroffenen Bestimmungen
- **positions**: Liste der vertretenen Positionen mit Kurzbezeichnung und Zusammenfassung
- **author_status**: Default ist `contested` — das ist der Normalzustand einer Streitfragenseite

---

## IV. Qualitätsstandards

### Fairness
Jede Position muss in ihrer **stärksten** Version dargestellt werden. Die Seite darf keine Position bevorzugen. Der Massstab: Würde eine Vertreterin jeder Position ihre eigene Darstellung als fair anerkennen?

### Die Seite entscheidet NICHT
Eine Streitfragenseite löst die Frage nicht auf. Sie kartiert die Meinungsverschiedenheit. Formulierungen wie «die richtige Ansicht ist…» oder «überzeugend erscheint…» sind unzulässig.

### Quellengestützt
Jede Position muss auf Autorität gestützt sein — Rechtsprechung, Lehrmeinungen, Behördenpraxis. Spekulationen sind unzulässig.

### Der Leser versteht das WARUM
Das Ziel ist nicht bloss: «A sagt ja, B sagt nein.» Der Leser soll nach der Lektüre verstehen, **warum** vernünftige Juristinnen und Juristen zu unterschiedlichen Ergebnissen kommen. Die Analyse-Sektion ist der Kern der Seite.

### Randziffern
Streitfragenseiten verwenden Randziffern (N. 1, N. 2 usw.) wie Doktrinseiten.
