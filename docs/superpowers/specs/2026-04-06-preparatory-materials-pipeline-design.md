# Preparatory Materials Pipeline — Design Specification

**Date:** 2026-04-06
**Status:** Draft

## Problem

The commentary pipeline currently generates doctrine from two inputs: statute text (Fedlex) and case law (opencaselaw). The Entstehungsgeschichte section — legislative history, Federal Council rationale, parliamentary debate — relies on the model's training data, which is unreliable for Swiss parliamentary sources. Botschaft quotes may be fabricated, BBl page references imprecise, parliamentary modification claims unverifiable.

Best-in-class legal commentary (BSK, Stämpfli Handkommentar) grounds every doctrinal statement in either preparatory materials or case law. This project already has best-in-class case law input via opencaselaw (963k decisions, daily updates). Adding structured preparatory materials closes the gap.

## Objective

Build a pipeline that discovers, downloads, extracts, and structures preparatory materials (Botschaften, parliamentary resolutions, debate documents) for all 9 covered laws, and integrates them into the commentary generation and evaluation pipeline.

**The formula:**

```
Statute text (Fedlex) + Preparatory materials (this pipeline) + Case law (opencaselaw)
= Best-in-class commentary
```

## Data Sources

### 1. Swiss Parliament API (`ws-old.parlament.ch`)

RESTful API, JSON format. Individual affair detail at `/affairs/{id}?format=json&lang=de`.

**Per affair, provides:**

| Field | Path | Content |
|-------|------|---------|
| Botschaft reference | `drafts[].references[].publication` | BBl source string, PDF URL, date |
| Parliamentary resolutions | `drafts[].consultation.resolutions[]` | Council, date, decision text |
| Committee assignments | `drafts[].preConsultations[]` | Committee name, rapporteurs |
| Debate documents | `drafts[].links[]` | PDF URLs for "Verhandlungen \| Argumente" |
| Related affairs | `relatedAffairs[]` | IDs of linked amendments/motions |
| Enactment text | AS reference in `drafts[].references[]` | Amtliche Sammlung URL |
| Legislative states | `drafts[].states[]` | Chronological state transitions |

**Verified working examples:**

- BGFA (99.027): Botschaft BBl 1999 6013 at `admin.ch/opc/de/federal-gazette/1999/6013.pdf`
- BV Reform (96.091): Botschaft BBl 1997 I 1
- OR Aktienrecht (16.077): Botschaft BBl 2017 399

### 2. Federal Gazette PDFs (admin.ch)

Botschaft PDFs hosted at `https://www.admin.ch/opc/de/federal-gazette/{year}/{page}.pdf`. Accessible without authentication. Older format (pre-2000) uses volume numbering: `BBl 1999 IV 4462`.

### 3. Fedlex SPARQL Endpoint (`fedlex.data.admin.ch/sparqlendpoint`)

Linked data for Swiss legislation. Complex ontology (jolux). Useful for:
- `foreseenImpactToLegalResource` → finds Vernehmlassung consultations
- Consolidation history (versions per law over time)
- Less useful for direct Botschaft discovery (parliament API is better for this)

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│ 1. DISCOVER                                                       │
│                                                                    │
│ Seed affair IDs (9 laws) ──→ parlament.ch API                     │
│   ├─ Extract BBl references + PDF URLs                            │
│   ├─ Extract parliamentary resolutions                            │
│   ├─ Follow relatedAffairs[] for amendments                       │
│   └─ Output: scripts/preparatory_materials/registry.json          │
├──────────────────────────────────────────────────────────────────┤
│ 2. DOWNLOAD                                                       │
│                                                                    │
│ registry.json ──→ fetch Botschaft PDFs                            │
│   └─ Output: data/botschaften/{bbl_ref_normalized}.pdf            │
│              (gitignored, cached)                                  │
├──────────────────────────────────────────────────────────────────┤
│ 3. EXTRACT                                                        │
│                                                                    │
│ PDFs ──→ PyMuPDF text extraction                                  │
│   └─ Output: data/botschaften/{bbl_ref_normalized}.txt            │
├──────────────────────────────────────────────────────────────────┤
│ 4. DIGEST                                                         │
│                                                                    │
│ Raw text ──→ Claude Opus per-article extraction                   │
│   └─ Output: scripts/preparatory_materials/{law}.json             │
├──────────────────────────────────────────────────────────────────┤
│ 5. INTEGRATE                                                      │
│                                                                    │
│ Per-article JSON ──→ prompt injection into law agent + evaluator  │
│   Modified: agents/references.py, agents/prompts.py,              │
│             guidelines/evaluate.md                                 │
└──────────────────────────────────────────────────────────────────┘
```

## Step 1: Discovery — Registry Builder

### Script: `scripts/discover_botschaften.py`

**Input:** Seed affair IDs per law (hardcoded lookup table).

**Seed affairs:** Each law has one or more known parliament affairs for its original enactment and major revisions. These IDs are deterministic from parliamentary history.

```python
# Verified: BV, BGFA, OR (Aktienrecht). Others need validation on first run.
# The discovery script validates each ID by checking the affair title.
SEED_AFFAIRS: dict[str, list[str]] = {
    "BV":    ["19960091"],                          # Totalrevision 1999 (verified)
    "ZGB":   ["19940083", "20150046", "20180069"],  # Kindesrecht, Erbrecht, etc. (to verify)
    "OR":    ["20160077", "20080064"],               # Aktienrecht 2020 (verified), OR-Revision (to verify)
    "ZPO":   ["20060062"],                           # Vereinheitlichung Zivilprozessrecht (to verify)
    "StGB":  ["19990063", "20100050"],               # AT-Revision, Sanktionenrecht (to verify)
    "StPO":  ["20060013"],                           # Vereinheitlichung Strafprozessrecht (to verify)
    "SchKG": ["19910089"],                           # SchKG-Revision 1994 (to verify)
    "VwVG":  ["19650079"],                           # Original or closest available (to verify)
    "BGFA":  ["19990027"],                           # Anwaltsgesetz (verified)
}
```

**Note:** Three seed IDs are verified (BV, OR Aktienrecht, BGFA). The remainder are best-guess IDs from parliamentary history. The discovery script validates each on first run and logs warnings for mismatches. Incorrect IDs are fixed in the seed table and re-run. This is a one-time manual step during initial setup.

**Process per affair ID:**

1. `GET /affairs/{id}?format=json&lang=de`
2. Extract from each `draft`:
   - `references[]` → BBl source, PDF URL, title, date
   - `consultation.resolutions[]` → council, date, decision text
   - `preConsultations[]` → committee name, abbreviation, rapporteurs
   - `links[]` → debate document URLs
   - `states[]` → legislative state chronology
   - `texts[]` → draft titles
3. Follow `relatedAffairs[]` (breadth-first, max depth 2) to discover amendment affairs
4. For each discovered amendment affair, repeat extraction
5. Deduplicate by affair ID

**Rate limiting:** 1 request/second to be respectful to the parliament API.

**Output:** `scripts/preparatory_materials/registry.json`

```json
{
  "generated": "2026-04-06T12:00:00Z",
  "laws": {
    "BGFA": {
      "sr_number": "935.61",
      "affairs": [
        {
          "id": "19990027",
          "short_id": "99.027",
          "title": "Freizügigkeit der Anwältinnen und Anwälte. Bundesgesetz",
          "type": "original",
          "botschaften": [
            {
              "title": "Botschaft vom 28. April 1999 zum BGFA",
              "bbl_ref": "BBl 1999 6013",
              "bbl_ref_normalized": "bbl-1999-6013",
              "pdf_url": "https://www.admin.ch/opc/de/federal-gazette/1999/6013.pdf",
              "date": "1999-04-28"
            }
          ],
          "resolutions": [
            {
              "council": "Nationalrat",
              "date": "1999-09-01",
              "text": "Beschluss abweichend vom Entwurf"
            },
            {
              "council": "Ständerat",
              "date": "1999-12-20",
              "text": "Abweichung"
            },
            {
              "council": "Ständerat",
              "date": "2000-03-16",
              "text": "Rückweisung an die Kommission"
            },
            {
              "council": "Nationalrat",
              "date": "2000-06-23",
              "text": "Annahme in der Schlussabstimmung"
            },
            {
              "council": "Ständerat",
              "date": "2000-06-23",
              "text": "Annahme in der Schlussabstimmung"
            }
          ],
          "committees": [
            {
              "name": "Kommission für Rechtsfragen Nationalrat",
              "abbreviation": "RK-N"
            }
          ],
          "debate_documents": [],
          "enactment_ref": "AS 2002 863"
        }
      ]
    }
  }
}
```

### Seed affair ID validation

The discovery script validates each seed affair ID on first run: fetch the affair, check that its title plausibly relates to the law (substring match on law name or SR number in descriptors), and warn if not. This catches typos in the seed table.

### Amendment discovery via `relatedAffairs[]`

Each affair lists related affairs. The script follows these links (BFS, max depth 2) and includes any affair whose `affairType` is `BRG` (Geschäft des Bundesrates) — these are the ones that carry Botschaften. Motions, interpellations, and postulates are excluded (they don't produce Botschaften).

## Step 2: Download

### Script: `scripts/download_botschaften.py`

Reads `registry.json`, downloads each unique Botschaft PDF to `data/botschaften/{bbl_ref_normalized}.pdf`. Skips if file already exists (cached).

**Directory:** `data/botschaften/` at project root — gitignored (PDFs are large). The extracted `.txt` files are also in `data/botschaften/` (gitignored). Only the structured JSON output in `scripts/preparatory_materials/` is committed.

**BBl ref normalization:** `BBl 1999 6013` → `bbl-1999-6013`. `BBl 1999 IV 4462` → `bbl-1999-IV-4462`.

**Error handling:** Some older BBl URLs may 404 or redirect. The script logs failures but continues. Missing PDFs are flagged in the registry as `"download_status": "failed"`.

**PDF URL construction:**
- Post-2000: `https://www.admin.ch/opc/de/federal-gazette/{year}/{page}.pdf`
- Pre-2000 (old format with volume): URL from parliament API directly (may point to year-level page, not individual PDF). For these, the script tries the Fedlex ELI alternative: `https://www.fedlex.admin.ch/eli/fga/{year}/{id}/de`

## Step 3: Text Extraction

### Script: `scripts/extract_botschaften.py`

Uses PyMuPDF (`fitz`) to extract text from each PDF. Same library and pattern as the BSK/CR extraction plan.

**Output:** `data/botschaften/{bbl_ref_normalized}.txt`

**Processing:**
1. Extract text per page with `page.get_text("text")`
2. Preserve page numbers as markers: `[Page 6045]`
3. Clean up OCR artifacts, hyphenation at line breaks, header/footer repetition
4. Store as plain UTF-8 text

**Quality check:** If extracted text is less than 1000 characters per page average, flag as potential scan/OCR issue (some older Botschaften are scanned images, not text PDFs).

## Step 4: Digestion — Per-Article Extraction

### Script: `scripts/digest_botschaften.py`

The key step. For each law, processes all Botschaft texts and extracts per-article structured data.

**Model:** Claude Opus (complex legal document comprehension)

**Process per law:**

1. Load all Botschaft texts for the law from `data/botschaften/`
2. Load the article list for the law from `scripts/article_lists.json`
3. For each Botschaft text:
   a. Send to Claude with system prompt (see below) and the list of articles
   b. Claude identifies the "Besonderer Teil" (article-by-article commentary) and "Allgemeiner Teil" (general rationale)
   c. For each article mentioned, Claude extracts structured data
4. Merge extracts from multiple Botschaften (original + amendments) per article
5. Add parliamentary resolution data from `registry.json`

**System prompt for digestion:**

```
You are a legal document analyst for openlegalcommentary.ch. You are processing
a Swiss Federal Council Botschaft (legislative message) to extract per-article
legislative intent and rationale.

The Botschaft typically has this structure:
1. Allgemeiner Teil — general context, problem statement, international comparison
2. Besonderer Teil — article-by-article commentary with the Federal Council's rationale
3. Auswirkungen — financial, personnel, cantonal effects

For each article in the provided list, extract:

1. legislative_intent: What did the Federal Council intend with this provision?
   Be specific and cite the Botschaft's own language where possible.
2. key_arguments: The main arguments for the chosen design (list of strings)
3. design_choices: What alternatives were considered and why this design was chosen
4. rejected_alternatives: Specific alternatives mentioned and reasons for rejection
5. bbl_page_refs: Exact page references in the Botschaft (e.g., "BBl 1999 6045-6048")
6. general_context: Relevant points from the Allgemeiner Teil that apply to this article

If an article is not discussed in this Botschaft (because the Botschaft concerns a
different revision), set all fields to null for that article.

Return JSON. Be precise. Preserve the Botschaft's original German phrasing in quotes.
```

**Cost estimate:** ~$1-3 per Botschaft (Opus, ~100-300 pages of text input + structured output). Total for all 9 laws' initial Botschaften: ~$10-30.

**Output:** `scripts/preparatory_materials/{law}.json`

```json
{
  "law": "BGFA",
  "sr_number": "935.61",
  "generated": "2026-04-06T14:00:00Z",
  "general_context": {
    "bbl_ref": "BBl 1999 6013",
    "problem_statement": "26 kantonale Anwaltsgesetze mit unterschiedlichen Regelungen...",
    "solution_overview": "Bundesgesetzliche Regelung der Freizügigkeit...",
    "international_comparison": "EU-Richtlinie 98/5/EG als Vorbild..."
  },
  "articles": {
    "1": {
      "provisions_discussed": ["Art. 1"],
      "sources": [
        {
          "bbl_ref": "BBl 1999 6013",
          "bbl_page_refs": ["6034-6035"],
          "legislative_intent": "Art. 1 definiert den Geltungsbereich des Gesetzes. Der Bundesrat betonte, dass...",
          "key_arguments": [
            "Einheitliche Regelung der Freizügigkeit auf Bundesebene",
            "Beschränkung auf Anwältinnen und Anwälte mit kantonalem Patent"
          ],
          "design_choices": [
            "Keine vollständige Harmonisierung des Anwaltsrechts, sondern Beschränkung auf Freizügigkeit"
          ],
          "rejected_alternatives": [
            "Vollharmonisierung abgelehnt wegen kantonaler Kompetenz (Art. 3 BV)"
          ],
          "general_context": "Das Gesetz verfolgt primär das Ziel der interkantonalen Freizügigkeit..."
        }
      ],
      "parliamentary_modifications": [
        {
          "council": "Nationalrat",
          "date": "1999-09-01",
          "change": "Beschluss abweichend vom Entwurf",
          "source": "registry.json"
        }
      ]
    },
    "12": {
      "provisions_discussed": ["Art. 12 Abs. 1", "Art. 12 Abs. 2 lit. a-j"],
      "sources": [
        {
          "bbl_ref": "BBl 1999 6013",
          "bbl_page_refs": ["6045-6048"],
          "legislative_intent": "Art. 12 enthält einen abschliessenden Katalog von Berufsregeln...",
          "key_arguments": [
            "Numerus clausus: Bundesrechtlicher Katalog ist abschliessend",
            "Kantone können keine zusätzlichen Berufsregeln aufstellen"
          ],
          "design_choices": [
            "Abschliessender Katalog statt Mindeststandards, weil..."
          ],
          "rejected_alternatives": [
            "Selbstregulierung durch Anwaltsverbände abgelehnt, weil..."
          ],
          "general_context": null
        }
      ],
      "parliamentary_modifications": []
    }
  }
}
```

### Merging multiple Botschaften per article

When multiple Botschaften discuss the same article (original + subsequent amendments), each gets its own entry in the `sources` array, ordered chronologically. The prompt injection formats them with clear temporal markers:

```
### Preparatory Materials for Art. 12 BGFA

#### Original Botschaft (BBl 1999 6013, pp. 6045-6048)
Legislative intent: Art. 12 enthält einen abschliessenden Katalog...
Key arguments: ...

#### Amendment Botschaft (BBl 2020 1234, pp. 15-16)
Change: Abs. 2 lit. j (Meldepflicht) added
Legislative intent: ...
```

## Step 5: Pipeline Integration

### Modified file: `agents/references.py`

Add functions parallel to existing commentary refs:

```python
PREPARATORY_MATERIALS_ROOT = Path("scripts/preparatory_materials")

_prep_materials_cache: dict[str, dict] = {}


def load_preparatory_materials(law: str) -> dict:
    """Load per-article preparatory materials for a law.

    Returns dict keyed by article number string, or empty dict if no file.
    """
    if law in _prep_materials_cache:
        return _prep_materials_cache[law]

    path = PREPARATORY_MATERIALS_ROOT / f"{law.lower()}.json"
    if not path.exists():
        _prep_materials_cache[law] = {}
        return {}

    data = json.loads(path.read_text())
    _prep_materials_cache[law] = data.get("articles", {})
    return _prep_materials_cache[law]


def format_preparatory_materials(
    law: str, article_number: int, suffix: str,
) -> str:
    """Format preparatory materials for prompt injection.

    Returns empty string if no data available.
    """
    materials = load_preparatory_materials(law)
    key = f"{article_number}{suffix}"
    article_data = materials.get(key)
    if not article_data:
        return ""

    blocks = []
    blocks.append("## Preparatory Materials (Materialien)")
    blocks.append("")

    for source in article_data.get("sources", []):
        bbl = source.get("bbl_ref", "?")
        pages = ", ".join(source.get("bbl_page_refs", []))
        blocks.append(f"### {bbl} (pp. {pages})")
        blocks.append("")

        intent = source.get("legislative_intent")
        if intent:
            blocks.append(f"**Legislative intent:** {intent}")
            blocks.append("")

        for arg in source.get("key_arguments", []):
            blocks.append(f"- {arg}")

        choices = source.get("design_choices", [])
        if choices:
            blocks.append("")
            blocks.append("**Design choices:**")
            for c in choices:
                blocks.append(f"- {c}")

        rejected = source.get("rejected_alternatives", [])
        if rejected:
            blocks.append("")
            blocks.append("**Rejected alternatives:**")
            for r in rejected:
                blocks.append(f"- {r}")

        blocks.append("")

    mods = article_data.get("parliamentary_modifications", [])
    if mods:
        blocks.append("### Parliamentary Modifications")
        for m in mods:
            blocks.append(f"- {m['council']}, {m['date']}: {m['change']}")
        blocks.append("")

    blocks.append(
        "Use these materials to ground the Entstehungsgeschichte section. "
        "Cite with exact BBl page references. "
        "Trace where courts have deviated from or confirmed legislative intent."
    )

    return "\n".join(blocks)
```

### Modified file: `agents/prompts.py`

**Doctrine LAYER_INSTRUCTIONS** — add after the BSK/CR block:

```
When preparatory materials (Materialien) are provided in the prompt:
- Ground the Entstehungsgeschichte section in actual Botschaft quotes
- Cite with exact BBl page references: "BBl 1999 6045"
- Include the Federal Council's stated intent for the provision
- Note where the parliamentary process modified the Federal Council's proposal
- In the Norminhalt and Streitstände sections, trace where judicial interpretation
  has confirmed, narrowed, or expanded the original legislative intent
- Do NOT reproduce Botschaft text verbatim — synthesize and cite
```

**Summary LAYER_INSTRUCTIONS** — add:

```
When preparatory materials are provided:
- Use the Botschaft's own plain-language explanation as a starting point
- The summary should reflect what the legislature intended, not just what the text says
```

### Modified file: `agents/generation.py`

In the article generation flow, after loading commentary refs, also load and format preparatory materials. Inject into the user message alongside existing reference data.

### Modified file: `guidelines/evaluate.md`

Add 6th non-negotiable criterion:

```
6. Korrekte Materialien (Correct preparatory materials)
   When preparatory materials reference data is provided:
   - Cited BBl page references must match the reference data
   - Legislative intent claims must be traceable to the provided Botschaft extracts
   - Parliamentary modification claims must match the resolution data
   - Do NOT fabricate Botschaft quotes that aren't in the reference data
```

## CLI Commands

```bash
# Step 1: Discover — build registry from parliament API
uv run python -m scripts.discover_botschaften

# Step 2: Download — fetch Botschaft PDFs
uv run python -m scripts.download_botschaften

# Step 3: Extract — PyMuPDF text extraction
uv run python -m scripts.extract_botschaften

# Step 4: Digest — Claude per-article extraction
uv run python -m scripts.digest_botschaften
uv run python -m scripts.digest_botschaften --law BGFA  # single law
uv run python -m scripts.digest_botschaften --max-budget 20  # budget limit

# Full pipeline (all steps)
uv run python -m scripts.preparatory_materials_pipeline
uv run python -m scripts.preparatory_materials_pipeline --law BGFA
```

## Incremental Enrichment Path

### Phase 1 (this spec): Botschaften
- Federal Council messages for all 9 laws
- Per-article structured extracts
- Parliamentary resolutions from API (already structured, no PDF needed)

### Phase 2: Debate transcripts
- Amtliches Bulletin PDFs from `drafts[].links[]` in registry
- Extract council debate text per article
- Add `debate_excerpts` field to per-article JSON
- Prompt addition: "Note key parliamentary debate points (minority positions, committee recommendations)"

### Phase 3: Committee reports
- Some committee reports available via parliament API links
- Extract committee positions, minority views
- Add `committee_positions` field

### Phase 4: Vernehmlassung (public consultation)
- Fedlex `foreseenImpactToLegalResource` provides consultation entries
- Extract key stakeholder positions from consultation results
- Add `vernehmlassung` field

Each phase adds a new field to the JSON and a new section to the prompt instructions. The pipeline architecture, storage format, and integration points remain unchanged.

## File Changes Summary

| File | Change |
|------|--------|
| `scripts/discover_botschaften.py` | **New** — registry builder |
| `scripts/download_botschaften.py` | **New** — PDF downloader |
| `scripts/extract_botschaften.py` | **New** — PyMuPDF text extraction |
| `scripts/digest_botschaften.py` | **New** — Claude per-article digestion |
| `scripts/preparatory_materials_pipeline.py` | **New** — orchestrates all steps |
| `scripts/preparatory_materials/registry.json` | **New** — generated, committed |
| `scripts/preparatory_materials/{law}.json` | **New** — generated, committed |
| `data/botschaften/` | **New** — gitignored PDF + txt cache |
| `.gitignore` | **Modified** — add `data/botschaften/` |
| `agents/references.py` | **Modified** — add `load_preparatory_materials`, `format_preparatory_materials` |
| `agents/prompts.py` | **Modified** — extend LAYER_INSTRUCTIONS for doctrine and summary |
| `agents/generation.py` | **Modified** — load and inject preparatory materials |
| `guidelines/evaluate.md` | **Modified** — add 6th non-negotiable criterion |
| `tests/test_references.py` | **Modified** — add tests for new functions |
| `tests/test_preparatory_materials.py` | **New** — tests for discovery, extraction, digestion |

## Cost Estimate

| Step | Cost | Notes |
|------|------|-------|
| Discovery | Free | Parliament API, no auth |
| Download | Free | Admin.ch PDFs, public |
| Extraction | Free | PyMuPDF, local |
| Digestion | ~$10-30 | Opus, ~15-25 Botschaften, 100-300 pages each |
| **Total initial build** | **~$10-30** | One-time |
| Subsequent updates | ~$1-3 | Per new Botschaft (when laws are amended) |

## Dependencies

- `PyMuPDF` (fitz) — already in project dependencies (planned for BSK/CR pipeline)
- `anthropic` — already in project dependencies
- `httpx` — for parliament API calls (already available or trivial to add)

## Success Criteria

1. `registry.json` contains Botschaft references for all 9 laws
2. Per-article JSON exists for at least BGFA (smallest law, 38 articles) as proof-of-concept
3. Doctrine generation for BGFA Art. 12 produces Entstehungsgeschichte grounded in actual BBl 1999 6013 quotes with correct page references
4. Evaluator rejects fabricated Botschaft quotes when reference data is available
5. The pipeline is idempotent — re-running produces the same output unless source data changes
