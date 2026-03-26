# Per-Article Prompt Enrichment — Design

## Problem

The current pipeline uses the same generic prompt for every BV article. While the output is solid (academic citations, BGE references, doctrinal debates), it lacks article-specific depth that a human expert would bring:

1. **No awareness of the article's significance** — Art. 8 (equality) gets the same treatment as Art. 155 (parliamentary services)
2. **No article-specific literature** — the pipeline doesn't know which specific monographs or journal articles are seminal for each provision
3. **No awareness of recent developments** — constitutional amendments, pending initiatives, recent landmark decisions
4. **No EMRK parallel mapping** — which EMRK article corresponds to which BV article
5. **No cross-law impact** — which implementing legislation (GlG, BehiG, etc.) concretizes each BV article

## Solution: Article-Specific Context Files

Create a `scripts/article_context/bv/` directory with per-article JSON files that enrich the generation prompt:

```json
{
  "article": "8",
  "significance": "high",
  "norm_type": "grundrecht",
  "emrk_parallel": ["Art. 14 EMRK", "12. ZP EMRK (nicht ratifiziert)"],
  "uno_parallel": ["Art. 2 UNO-Pakt II", "Art. 26 UNO-Pakt II", "CEDAW", "BRK"],
  "implementing_legislation": [
    {"law": "GlG", "sr": "151.1", "relevance": "Geschlechtergleichstellung im Erwerbsleben"},
    {"law": "BehiG", "sr": "151.3", "relevance": "Beseitigung von Benachteiligungen Behinderter"}
  ],
  "key_decisions": [
    "BGE 139 I 161 (Rechtsgleichheitsprüfung, Dreistufentest)",
    "BGE 131 I 105 (Lohngleichheit, unmittelbare Anwendbarkeit)",
    "BGE 123 I 152 (Geschlechterquoten, Zurückhaltung)",
    "BGE 136 I 297 (indirekte Diskriminierung, Prüfungsmassstab)"
  ],
  "seminal_literature": [
    "Müller/Schefer, Grundrechte in der Schweiz, 4. Aufl. 2008, § 34-36",
    "Waldmann, BSK BV, Art. 8 (2. Aufl. 2024)",
    "Schweizer/Mohler, St. Galler Kommentar, Art. 8 (4. Aufl. 2023)",
    "Bigler-Eggenberger/Kaufmann, Kommentar GlG, 2. Aufl.",
    "Pärli, Gleichbehandlung und Sozialversicherung, 2020"
  ],
  "recent_developments": [
    "Revision des GlG (Lohngleichheitsanalyse seit 2020)",
    "BRK-Konformität der Schweizer Behindertenpolitik (Staatenberichtsverfahren 2022)",
    "Lohngleichheitsanalysen: erste Ergebnisse und Kritik"
  ],
  "doctrinal_debates": [
    {
      "topic": "Indirekte Diskriminierung",
      "positions": {
        "broad": "Müller/Schefer: Art. 8 Abs. 2 erfasst auch indirekte Diskriminierungen",
        "narrow": "Kiener/Kälin/Wyttenbach: differenzierte Betrachtung je nach Merkmal"
      }
    },
    {
      "topic": "Positive Massnahmen / Quotenregelungen",
      "positions": {
        "pro": "Bigler-Eggenberger: Abs. 3 S. 2 als Grundlage für Quotenregelungen",
        "contra": "Schweizer: verfassungsrechtliche Schranken; BG zurückhaltend (BGE 123 I 152)"
      }
    },
    {
      "topic": "Drittwirkung",
      "positions": {
        "indirect": "h.L. (Häfelin/Haller/Keller/Thurnherr): nur mittelbare über Generalklauseln",
        "differentiated": "Biaggini: differenziert nach Diskriminierungsmerkmal"
      }
    }
  ],
  "quality_focus": [
    "EMRK-Parallelen müssen systematisch dargestellt werden",
    "Die Dreiteilung (Abs. 1 allg. Gleichheit, Abs. 2 Diskriminierung, Abs. 3 Geschlechter, Abs. 4 Behinderte) muss klar herausgearbeitet werden",
    "Praktische Relevanz: Lohngleichheitsklagen, GlG-Verfahren, Diskriminierung im Privatrecht"
  ]
}
```

## Automation Strategy

### Phase 1: Generate context files automatically

For each BV article, use Claude to generate the context file by:

1. **Reading the article text** from Fedlex
2. **Querying opencaselaw** for leading cases
3. **Consulting the BSK reference data** for author positions
4. **Classifying the norm type** (Grundrecht, Kompetenz, Organisation, Programmatik)
5. **Identifying EMRK parallels** based on standard mappings
6. **Identifying implementing legislation** from the SR

This can be done as a one-time batch job: `scripts/generate_article_context.py`

### Phase 2: Inject context into generation prompts

Update `agents/prompts.py` to load and format the context file for each article, adding it to the system prompt as "Article-Specific Research Context".

### Phase 3: Quality criteria per norm type

Different norm types need different quality criteria:

| Norm Type | Additional Requirements |
|-----------|------------------------|
| **Grundrecht** (Art. 7-36) | EMRK parallel, Einschränkungsdogmatik (Art. 36), indirekte Drittwirkung, Schutzbereichsbestimmung |
| **Kompetenz** (Art. 54-135) | Bundesgesetz-Umsetzung, kantonale Restkompetenz, Gesetzgebungsart (ausschliesslich/konkurrierend/Rahmen) |
| **Organisation** (Art. 143-191c) | Verfahrensablauf, Zuständigkeitsabgrenzung, praktische Bedeutung gering → knapper |
| **Programmatik** (Art. 41) | Nicht-Justiziabilität, politische Bedeutung, internationale Parallelen |
| **Übergang** (Art. 196-197) | Befristung, Verhältnis zum Hauptartikel, aktuelle Gültigkeit |

### Expected Quality Improvements

1. **Article-aware depth** — high-significance articles get more thorough treatment
2. **Complete EMRK mapping** — every fundamental right linked to its EMRK counterpart
3. **Implementing legislation** — every competence norm linked to its concretizing laws
4. **Recent developments** — amendments, initiatives, new case law since 2020
5. **Named doctrinal debates** — specific author positions with citations, not "umstritten"
6. **Consistent cross-references** — every article aware of its systematic context

### Cost Estimate

- Context generation: ~$0.10/article × 232 = ~$23
- Regeneration with enriched prompts: ~$2.50/article × 232 = ~$580
- Total: ~$600 for a complete quality upgrade of BV

This would bring the commentary from "good AI-generated" to "comparable to a junior academic commentary" level.
