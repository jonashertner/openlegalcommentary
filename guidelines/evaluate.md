# Qualitätsbewertung / Quality Evaluation Rubric

> Dieses Dokument ist das Äquivalent von `val_bpb` in autoresearch: ein eigenständiger Evaluator-Agent, der nach jeder Generierung prüft, ob der Kommentar die Qualitätsschwellen erreicht, bevor er veröffentlicht wird.

---

## I. Unverhandelbare Kriterien (binär)

Jedes der folgenden Kriterien wird binär geprüft. Ein einziges Nichterfüllen führt zur Ablehnung des Entwurfs ohne Ausnahme.

### 1. Keine unbelegten Rechtsaussagen

Jede Aussage über geltendes Recht, Rechtsprechung oder herrschende Doktrin muss mit einer Primärquelle belegt sein.

**Prüfmethode**: Jeder Satz, der eine Rechtslage behauptet, wird auf einen expliziten Quellenbeleg geprüft. Sätze ohne Beleg werden markiert und führen zur Ablehnung.

**Erweiterung bei BSK/CR-Referenzdaten**: Wenn Referenzdaten bereitgestellt werden, müssen zitierte BSK/CR-Autorinnen/Autoren und Randziffern mit den Referenzdaten übereinstimmen.

### 2. Keine faktischen Fehler

Die zitierten Leitsätze und Holdings müssen mit den tatsächlichen Entscheiden übereinstimmen. Falsch dargestellte Urteile führen zur Ablehnung.

**Prüfmethode**: Alle BGE-Referenzen werden gegen die opencaselaw-Datenbank abgeglichen. Divergenzen zwischen zitiertem Leitsatz und tatsächlichem Entscheid führen zur Ablehnung.

### 3. Keine fehlenden Leitentscheide

Alle auf opencaselaw verfügbaren Leitentscheide zu einem Artikel müssen in Ebene 3 erscheinen.

**Prüfmethode**: Die Liste der relevanten BGE aus opencaselaw wird mit den im Text zitierten BGE verglichen. Fehlende Entscheide führen zur Ablehnung.

### 4. Korrekte Legalbegriffe

Die im Kommentar verwendeten Rechtsbegriffe müssen mit den Begriffen im massgeblichen SR-Text übereinstimmen.

**Prüfmethode**: Automatischer Abgleich der Schlüsselbegriffe mit dem SR-Text via Fedlex. Abweichungen (z.B. *Nachteil* statt *Schaden*, *Besitz* statt *Eigentum*) führen zur Ablehnung.

### 5. Strukturelle Vollständigkeit

Alle für die jeweilige Ebene vorgeschriebenen Sektionen müssen vorhanden sein (→ global.md II.).

**Prüfmethode**: Automatische Prüfung auf Vorhandensein aller Pflicht-Überschriften gemäss Ebenen-Spezifikation.

### 6. **Korrekte Materialien** (Correct preparatory materials)
   Wenn Materialien-Referenzdaten bereitgestellt werden:
   - Zitierte BBl-Seitenverweise müssen mit den Referenzdaten übereinstimmen
   - Aussagen zur Gesetzgebungsabsicht müssen auf die bereitgestellten Botschaftsauszüge zurückführbar sein
   - Aussagen zu parlamentarischen Änderungen müssen mit den Abstimmungsdaten übereinstimmen
   - Keine Botschaftszitate erfinden, die nicht in den Referenzdaten enthalten sind

---

## II. Bewertete Dimensionen

Jede Dimension wird auf einer Skala von 0–1 bewertet. Der angegebene Schwellenwert ist Mindestvoraussetzung für die Veröffentlichung.

### 1. Präzision (Schwellenwert: 0.95)

- Zitiergenauigkeit: BGE- und Literaturzitate im vorgeschriebenen Format
- Terminologische Exaktheit: keine unzulässigen Synonyme
- Zeitliche Genauigkeit: Geltungszeitraum explizit angegeben

### 2. Konzision (Schwellenwert: 0.90)

- Keine Redundanzen zwischen Sektionen
- Wortzahl der Zusammenfassung: 150–300 Wörter
- Keine Füll- und Absicherungsformeln

### 3. Zugänglichkeit (Schwellenwert: 0.90, nur Ebene 1)

- Kein unübersetzter Fachjargon
- Durchschnittliche Satzlänge ≤ 25 Wörter
- Mindestens ein konkretes Beispiel vorhanden

### 4. Relevanz (Schwellenwert: 0.90)

- Praktische Bedeutung wird vor theoretischen Debatten dargestellt
- Überholte Rechtslage ist als solche markiert
- Entwicklungen der letzten 12 Monate sind berücksichtigt

### 5. Akademische Strenge (Schwellenwert: 0.95)

- Mindestens 3 Sekundärquellen (verschiedene Autorinnen/Autoren)
- Botschaft zitiert (wo vorhanden)
- Streitstände mit Nennung der vertretenden Autorinnen und Autoren
- Auseinandersetzung mit den in den Referenzdaten identifizierten doktrinären Kontroversen

---

## III. Bewertungsablauf

```
Generierung
    │
    ▼
Unverhandelbare Kriterien prüfen (binär)
    │
    ├── Nichterfüllt ──► Ablehnung → Retry (max. 3×)
    │                                    │
    │                                    └── Nach 3 Fehlversuchen: Flag für Mensch
    │
    └── Alle erfüllt
            │
            ▼
    Bewertete Dimensionen messen
            │
            ├── Unter Schwellenwert ──► Ablehnung → Retry (max. 3×)
            │                                           │
            │                                           └── Nach 3 Fehlversuchen: Flag für Mensch
            │
            └── Alle Schwellenwerte erreicht
                        │
                        ▼
                  Veröffentlichung
```

Maximale Anzahl Wiederholungsversuche: **3**. Nach dem dritten Fehlversuch wird der Entwurf mit detailliertem Feedbackbericht zur manuellen Überprüfung markiert.

---

## IV. Evaluator-Prompt-Vorlage

Der Evaluator-Agent erhält folgenden Input und gibt strukturiertes JSON zurück.

**Input**:

```
article_text:       [SR-Text des Artikels]
generated_content:  [generierter Kommentartext]
layer_type:         [1 | 2 | 3]
leading_cases_ref:  [Liste der auf opencaselaw verfügbaren BGE zum Artikel]
```

**Output-Format**:

```json
{
  "verdict": "publish" | "reject",
  "non_negotiables": {
    "keine_unbelegten_rechtsaussagen": true | false,
    "keine_faktischen_fehler": true | false,
    "keine_fehlenden_leitentscheide": true | false,
    "korrekte_legalbegriffe": true | false,
    "strukturelle_vollstaendigkeit": true | false
  },
  "scores": {
    "praezision": 0.00,
    "konzision": 0.00,
    "zugaenglichkeit": 0.00,
    "relevanz": 0.00,
    "akademische_strenge": 0.00
  },
  "feedback": {
    "blocking_issues": ["..."],
    "improvement_suggestions": ["..."]
  }
}
```

Ein `"verdict": "publish"` wird nur ausgegeben, wenn alle unverhandelbaren Kriterien `true` sind **und** alle Bewertungsdimensionen den jeweiligen Schwellenwert erreichen.
