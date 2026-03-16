# BSK/CR Commentary Integration Design

> Integrate Basler Kommentar and Commentaire Romand PDFs as structured reference sources for the commentary generation pipeline.

## Context

The pipeline currently generates doctrinal commentary relying on the LLM's training data for author positions, Randziffern, and doctrinal debates. This means citations to specific BSK authors and positions are likely imprecise or hallucinated. With access to the actual BSK/CR volumes as PDFs (OCR'd), we can extract structured reference data and inject it into the pipeline — grounding doctrine in real, citable positions.

### Available Volumes

| Volume | Type | Coverage |
|--------|------|----------|
| BSK OR I | Basler Kommentar | Art. 1–529 OR |
| BSK OR II | Basler Kommentar | Art. 530–1186 OR |
| CR CO I | Commentaire Romand (French) | Art. 1–529 CO |
| BSK BV | Basler Kommentar | SR 101 |
| BSK StGB | Basler Kommentar | SR 311.0 |
| BSK ZPO | Basler Kommentar | SR 272 |
| BSK StPO | Basler Kommentar | SR 312.0 |

Not covered: ZGB, SchKG, VwVG (no BSK volumes available).

### Design Principles

- **No reproduction**: The pipeline must not copy or closely paraphrase BSK/CR text. It synthesizes original commentary that cites specific authors and positions.
- **Structured references, not raw text**: What gets injected into prompts is author names, Randziffern maps, named positions, and controversies — not the commentary text itself.
- **Minimal architecture change**: Follows the existing pattern of `_format_article_text()` injection. No new infrastructure (no vector DB, no embeddings).

## 1. PDF Storage

PDFs stored locally at `data/commentary_pdfs/`, not committed to git.

```
data/
  commentary_pdfs/
    bsk_or_i.pdf
    bsk_or_ii.pdf
    cr_co_i.pdf
    bsk_bv.pdf
    bsk_stgb.pdf
    bsk_zpo.pdf
    bsk_stpo.pdf
```

`.gitignore` additions:

```
data/commentary_pdfs/
scripts/commentary_raw/
```

## 2. Extraction Pipeline (Two-Pass)

### Pass 1 — Raw Text Extraction

**Script**: `scripts/extract_commentary.py`

- Uses PyMuPDF (`pymupdf`) to extract text from OCR'd PDFs
- Splits into per-article chunks using article header detection (regex for `Art. XX` patterns + font size/weight heuristics from PyMuPDF block/span metadata)
- OCR cleanup: fix broken umlauts, normalize whitespace, repair Randziffern artifacts (`N.  12` → `N. 12`), fix broken BGE references
- Output: `scripts/commentary_raw/{law}_bsk.json` (or `_cr.json`)
- Intermediate file, gitignored — raw text stays local

### Pass 2 — Structured Digestion

**Script**: `scripts/digest_commentary.py`

- Reads raw article chunks from Pass 1
- Sends each article's text to Claude Sonnet with a structured extraction prompt
- Prompt instructs Claude to identify (not summarize or paraphrase):
  - Authors and edition info
  - Randziffern map (which N. ranges cover which topics)
  - Named doctrinal positions (author + N. reference + position)
  - Doctrinal controversies (topic + opposing positions with citations)
  - Cross-references to other articles
  - Key secondary literature cited by the BSK/CR
- Output: `scripts/commentary_refs/{law}_bsk.json` (or `_cr.json`) — committed to git
- **Validation**: Each article's output is validated against a Pydantic schema (see §3) before writing. Malformed entries are logged and skipped, not written.
- **Resume**: State file at `scripts/commentary_raw/{law}_bsk_digest_state.json` tracks completed article keys. `--resume` flag skips already-digested articles. Same pattern as `agents/bootstrap.py`.
- CR CO I: French input, but output schema is identical (positions summarized in German for uniform consumption by the law agent)
- **Long articles**: Articles exceeding 20k tokens of raw text are split into overlapping chunks for digestion, then merged. A `--max-input-tokens` flag (default 20000) controls this threshold.

### Cost Estimate

~3,300 unique articles across 6 volumes (CR CO I overlaps with OR I). Estimated ~9M input tokens + ~2M output tokens using Sonnet 4. Note: major articles (e.g., Art. 41 OR at 20–40 BSK pages) will consume significantly more tokens than the average; the estimate accounts for a long-tail distribution.

| | Tokens | Rate | Cost |
|---|--------|------|------|
| Input | ~9M | $3/1M | ~$27 |
| Output | ~2M | $15/1M | ~$30 |
| **Total** | | | **~$55–70** |

One-time cost. Ongoing cost increase per article generation is negligible (~500–1000 extra prompt tokens).

## 3. Storage Schema

`scripts/commentary_refs/{law}_bsk.json`

Article keys use the same format as `article_texts.json`: `"{number}{suffix}"` (e.g., `"41"`, `"6a"`, `"706b"`).

```json
{
  "OR": {
    "41": {
      "authors": ["Kessler", "Widmer Lüchinger"],
      "edition": "BSK OR I, 7. Aufl. 2019",
      "randziffern_map": {
        "1-3": "Entstehungsgeschichte",
        "4-8": "Systematische Einordnung",
        "9-25": "Tatbestandsmerkmale (Widerrechtlichkeit)",
        "26-35": "Kausalzusammenhang",
        "36-42": "Verschulden"
      },
      "positions": [
        {
          "author": "Kessler",
          "n": "N. 12",
          "topic": "Widerrechtlichkeit",
          "position": "Erfolgsunrecht genügt bei absoluten Rechtsgütern; Verhaltensunrecht nur bei reinen Vermögensschäden"
        }
      ],
      "controversies": [
        {
          "topic": "Organhaftung vs. Art. 55 OR",
          "positions": {
            "Kessler (BSK OR I, N. 30)": "Art. 55 OR ist lex specialis",
            "Huguenin (OR AT, N. 1850)": "Parallelanwendung möglich"
          }
        }
      ],
      "cross_refs": ["Art. 97 OR", "Art. 55 OR", "Art. 28 ZGB"],
      "key_literature": [
        "Gauch/Schluep/Schmid, OR AT, 11. Aufl. 2020",
        "Schwenzer/Fountoulakis, OR AT, 8. Aufl. 2020"
      ]
    }
  }
}
```

## 4. Pipeline Integration

### Shared utility: `agents/references.py` (new file)

Reference loading and formatting live in a dedicated module (not as private functions in `law_agent.py`) since both the law agent and evaluator need them.

- `load_commentary_refs(refs_root: Path, law: str) -> dict` — loads and caches `{refs_root}/{law}_bsk.json` + `{refs_root}/{law}_cr.json`, merging both into a single dict. Returns empty dict if no files exist (graceful for ZGB, SchKG, VwVG).
- `format_commentary_refs(refs_root: Path, law: str, article_number: int, suffix: str) -> str` — looks up the article key, formats the reference block. Returns empty string if no data.

**BSK + CR merging**: When both BSK and CR cover the same article (OR Art. 1–529), the formatted block includes both under labeled subsections (`### BSK` and `### CR`), presented sequentially.

### Law Agent (`agents/law_agent.py`)

Calls `format_commentary_refs()` from `agents/references.py`.

Injection in `generate_layer()` for `doctrine` and `summary` layers only (caselaw layer does not need doctrinal references):

```python
if layer_type in ("doctrine", "summary"):
    commentary_refs = format_commentary_refs(
        config.commentary_refs_root, law, article_number, suffix_str,
    )
    if commentary_refs:
        prompt += f"\n\n{commentary_refs}"
```

Injected block format:

```
## Doctrinal Reference Data (BSK / CR)

Authors: Kessler/Widmer Lüchinger, BSK OR I, 7. Aufl. 2019

Randziffern overview:
- N. 1–3: Entstehungsgeschichte
- N. 9–25: Tatbestandsmerkmale (Widerrechtlichkeit)
...

Key positions:
- Kessler, N. 12: Erfolgsunrecht genügt bei absoluten Rechtsgütern...

Doctrinal controversies:
- Organhaftung vs. Art. 55 OR: Kessler (N. 30) sees Art. 55 as lex specialis; Huguenin disagrees...

Use these references to ground your doctrinal analysis. Cite authors with proper BSK/CR Randziffern.
Do NOT reproduce commentary text — synthesize original analysis that cites specific positions.
```

### Evaluator (`agents/evaluator.py`)

Calls `format_commentary_refs()` from `agents/references.py` with the same signature. Enables the evaluator to:

- Verify cited BSK/CR authors exist in the reference data
- Check that N. references are plausible given the Randziffern map
- Assess whether doctrinal controversies are represented fairly

Strengthens the `keine_unbelegten_rechtsaussagen` non-negotiable from "trust the LLM" to "verify against known references."

### Prompts (`agents/prompts.py`)

Add to `LAYER_INSTRUCTIONS["doctrine"]`:

```
- When doctrinal reference data is provided, ground your analysis in the named positions
- Cite BSK authors with Randziffern: Kessler, BSK OR I, Art. 41 N. 12
- Cite CR authors with Randziffern: Thévenoz, CR CO I, Art. 41 N. 8
- Present doctrinal controversies from the references with named positions on each side
- Do NOT reproduce commentary text — synthesize original analysis
```

Add to `build_evaluator_prompt()` task instructions:

```
- When doctrinal reference data is provided, cross-check cited BSK/CR authors and Randziffern against the reference data
- Reject if BSK/CR positions are cited that don't appear in the references
```

### Config (`agents/config.py`)

Add `commentary_refs_root: Path` defaulting to `Path("scripts/commentary_refs")`.

### No Changes To

- `coordinator.py` — pure orchestration, no content generation
- `translator.py` — translates generated content, not source material
- `bootstrap.py` — calls `generate_layer()` which handles injection
- `generation.py` — calls `generate_layer()` and `evaluate_layer()` which handle injection
- `anthropic_client.py` — transport layer, no content awareness
- `mcp_client.py` — MCP transport
- `tools/` — tool definitions unchanged

## 5. Guidelines Updates

### `guidelines/global.md`

Add to §II.2 (Doktrin) requirements:

- When BSK/CR reference data is available, doctrinal positions must be grounded in the provided references
- BSK citation format: `Kessler, BSK OR I, Art. 41 N. 12`
- CR citation format: `Thévenoz, CR CO I, Art. 41 N. 8`
- Do not paraphrase or reproduce commentary text — synthesize original analysis that cites specific positions

### `guidelines/evaluate.md`

- `keine_unbelegten_rechtsaussagen`: when reference data is available, cited BSK/CR authors and Randziffern must match the reference data
- New soft signal under `akademische_strenge`: does the commentary engage with the doctrinal controversies identified in the references?

### Per-law guidelines

No structural changes needed — they already list BSK as key literature.

## 6. New Dependencies

Add to `pyproject.toml`:

```toml
pymupdf = ">=1.24"
```

## 7. File Summary

| File | Action |
|------|--------|
| `scripts/extract_commentary.py` | New — PDF raw text extraction |
| `scripts/digest_commentary.py` | New — structured digestion via Claude |
| `scripts/commentary_schema.py` | New — Pydantic schema for commentary ref validation |
| `agents/references.py` | New — shared commentary ref loading and formatting |
| `agents/law_agent.py` | Modify — inject commentary refs via `agents/references.py` |
| `agents/evaluator.py` | Modify — inject commentary refs via `agents/references.py` |
| `agents/config.py` | Modify — add `commentary_refs_root` |
| `agents/prompts.py` | Modify — update doctrine/evaluator instructions |
| `guidelines/global.md` | Modify — add BSK/CR citation rules |
| `guidelines/evaluate.md` | Modify — strengthen verification criteria |
| `.gitignore` | Modify — add `data/commentary_pdfs/` and `scripts/commentary_raw/` |
| `pyproject.toml` | Modify — add `pymupdf` dependency |
| `scripts/commentary_refs/*.json` | New — structured reference data (committed) |
| `scripts/commentary_raw/*.json` | New — raw extraction (gitignored) |
| `data/commentary_pdfs/*.pdf` | New — source PDFs (gitignored) |
