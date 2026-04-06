# Preparatory Materials Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ingest Swiss Federal Council Botschaften and parliamentary data as structured input to the commentary generation pipeline, grounding doctrine in verifiable legislative history.

**Architecture:** A 5-step pipeline (discover → download → extract → digest → integrate) that produces per-article JSON from parliament.ch API and Federal Gazette PDFs. The JSON is committed and injected into law agent and evaluator prompts alongside existing commentary references.

**Tech Stack:** Python, httpx (parliament API), PyMuPDF (PDF extraction), anthropic SDK (digestion), pytest

**Spec:** `docs/superpowers/specs/2026-04-06-preparatory-materials-pipeline-design.md`

---

## File Structure

| File | Responsibility |
|------|----------------|
| `scripts/discover_botschaften.py` | Query parliament API, build registry of affairs + BBl references |
| `scripts/download_botschaften.py` | Download Botschaft PDFs from admin.ch |
| `scripts/extract_botschaften.py` | PyMuPDF text extraction from PDFs |
| `scripts/digest_botschaften.py` | Claude Opus per-article structured extraction |
| `scripts/preparatory_materials_pipeline.py` | Orchestrates all 4 steps in sequence |
| `scripts/preparatory_materials/registry.json` | Generated: affair metadata per law |
| `scripts/preparatory_materials/{law}.json` | Generated: per-article Botschaft extracts |
| `agents/references.py` | Add `load_preparatory_materials`, `format_preparatory_materials` |
| `agents/law_agent.py` | Inject preparatory materials into prompt |
| `agents/evaluator.py` | Inject preparatory materials for cross-checking |
| `agents/prompts.py` | Extend LAYER_INSTRUCTIONS for Materialien |
| `guidelines/evaluate.md` | Add 6th non-negotiable criterion |
| `tests/test_references.py` | Add tests for new reference functions |
| `tests/test_discover_botschaften.py` | Tests for discovery script |
| `tests/test_extract_botschaften.py` | Tests for extraction script |

---

## Chunk 1: Reference Loading & Integration (Tasks 1–4)

Core pipeline integration — load preparatory materials JSON and inject into prompts.

### Task 1: Add `load_preparatory_materials` and `format_preparatory_materials` to references.py

**Files:**
- Modify: `agents/references.py`
- Modify: `tests/test_references.py`

- [ ] **Step 1: Write failing tests for `load_preparatory_materials`**

Add to `tests/test_references.py`:

```python
from agents.references import (
    _prep_materials_cache,
    format_preparatory_materials,
    load_preparatory_materials,
)


@pytest.fixture(autouse=True)
def clear_prep_cache():
    """Clear the module-level preparatory materials cache between tests."""
    _prep_materials_cache.clear()
    yield
    _prep_materials_cache.clear()


def _make_prep_materials(tmp_path, law, articles_data):
    """Helper to write a preparatory materials JSON file."""
    prep_dir = tmp_path / "preparatory_materials"
    prep_dir.mkdir(exist_ok=True)
    path = prep_dir / f"{law.lower()}.json"
    path.write_text(json.dumps({
        "law": law.upper(),
        "sr_number": "935.61",
        "generated": "2026-04-06T14:00:00Z",
        "articles": articles_data,
    }))
    return prep_dir


def test_load_preparatory_materials_basic(tmp_path):
    articles = {
        "12": {
            "sources": [{
                "bbl_ref": "BBl 1999 6013",
                "bbl_page_refs": ["6045-6048"],
                "legislative_intent": "Art. 12 enthält einen Katalog.",
                "key_arguments": ["Numerus clausus"],
                "design_choices": [],
                "rejected_alternatives": [],
                "general_context": None,
            }],
            "parliamentary_modifications": [],
        },
    }
    prep_dir = _make_prep_materials(tmp_path, "BGFA", articles)
    with patch("agents.references.PREPARATORY_MATERIALS_ROOT", prep_dir):
        result = load_preparatory_materials("BGFA")
        assert "12" in result
        assert result["12"]["sources"][0]["bbl_ref"] == "BBl 1999 6013"


def test_load_preparatory_materials_missing_law(tmp_path):
    prep_dir = tmp_path / "preparatory_materials"
    prep_dir.mkdir()
    with patch("agents.references.PREPARATORY_MATERIALS_ROOT", prep_dir):
        result = load_preparatory_materials("ZGB")
        assert result == {}


def test_load_preparatory_materials_caching(tmp_path):
    articles = {"1": {"sources": [], "parliamentary_modifications": []}}
    prep_dir = _make_prep_materials(tmp_path, "BGFA", articles)
    with patch("agents.references.PREPARATORY_MATERIALS_ROOT", prep_dir):
        result1 = load_preparatory_materials("BGFA")
        result2 = load_preparatory_materials("BGFA")
        assert result1 is result2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_references.py -k "prep" -v`
Expected: FAIL with ImportError (functions don't exist yet)

- [ ] **Step 3: Implement `load_preparatory_materials` in references.py**

Add at the end of `agents/references.py`:

```python
# --- Preparatory materials (Botschaften, parliamentary data) ---

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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_references.py -k "prep" -v`
Expected: 3 passed

- [ ] **Step 5: Write failing tests for `format_preparatory_materials`**

Add to `tests/test_references.py`:

```python
def test_format_preparatory_materials_basic(tmp_path):
    articles = {
        "12": {
            "sources": [{
                "bbl_ref": "BBl 1999 6013",
                "bbl_page_refs": ["6045-6048"],
                "legislative_intent": "Art. 12 enthält einen abschliessenden Katalog.",
                "key_arguments": ["Numerus clausus", "Bundesrechtlich abschliessend"],
                "design_choices": ["Abschliessender Katalog statt Mindeststandards"],
                "rejected_alternatives": ["Selbstregulierung abgelehnt"],
                "general_context": None,
            }],
            "parliamentary_modifications": [
                {
                    "council": "Nationalrat",
                    "date": "1999-09-01",
                    "change": "Beschluss abweichend vom Entwurf",
                },
            ],
        },
    }
    prep_dir = _make_prep_materials(tmp_path, "BGFA", articles)
    with patch("agents.references.PREPARATORY_MATERIALS_ROOT", prep_dir):
        result = format_preparatory_materials("BGFA", 12, "")
        assert "BBl 1999 6013" in result
        assert "abschliessenden Katalog" in result
        assert "Numerus clausus" in result
        assert "Abschliessender Katalog" in result
        assert "Selbstregulierung" in result
        assert "Nationalrat" in result
        assert "Materialien" in result


def test_format_preparatory_materials_empty_for_unknown(tmp_path):
    prep_dir = tmp_path / "preparatory_materials"
    prep_dir.mkdir()
    with patch("agents.references.PREPARATORY_MATERIALS_ROOT", prep_dir):
        result = format_preparatory_materials("BGFA", 999, "")
        assert result == ""


def test_format_preparatory_materials_multiple_sources(tmp_path):
    articles = {
        "12": {
            "sources": [
                {
                    "bbl_ref": "BBl 1999 6013",
                    "bbl_page_refs": ["6045"],
                    "legislative_intent": "Original intent.",
                    "key_arguments": [],
                    "design_choices": [],
                    "rejected_alternatives": [],
                    "general_context": None,
                },
                {
                    "bbl_ref": "BBl 2020 1234",
                    "bbl_page_refs": ["15-16"],
                    "legislative_intent": "Amendment intent.",
                    "key_arguments": [],
                    "design_choices": [],
                    "rejected_alternatives": [],
                    "general_context": None,
                },
            ],
            "parliamentary_modifications": [],
        },
    }
    prep_dir = _make_prep_materials(tmp_path, "BGFA", articles)
    with patch("agents.references.PREPARATORY_MATERIALS_ROOT", prep_dir):
        result = format_preparatory_materials("BGFA", 12, "")
        assert "BBl 1999 6013" in result
        assert "BBl 2020 1234" in result
        assert "Original intent" in result
        assert "Amendment intent" in result
```

- [ ] **Step 6: Implement `format_preparatory_materials` in references.py**

Add after `load_preparatory_materials` in `agents/references.py`:

```python
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

- [ ] **Step 7: Run all tests to verify**

Run: `uv run pytest tests/test_references.py -v`
Expected: All pass (existing + 6 new)

- [ ] **Step 8: Commit**

```bash
git add agents/references.py tests/test_references.py
git commit -m "feat: add preparatory materials loading and formatting to references.py"
```

---

### Task 2: Extend prompts and guidelines for preparatory materials

**Files:**
- Modify: `agents/prompts.py`
- Modify: `guidelines/evaluate.md`
- Modify: `tests/test_prompts.py`

- [ ] **Step 1: Read current evaluate.md to find insertion point**

Read `guidelines/evaluate.md` to find the non-negotiable criteria section and the end of criterion 5.

- [ ] **Step 2: Add 6th non-negotiable to evaluate.md**

After the 5th non-negotiable criterion (`Strukturelle Vollständigkeit`), add:

```markdown
6. **Korrekte Materialien** (Correct preparatory materials)
   Wenn Materialien-Referenzdaten bereitgestellt werden:
   - Zitierte BBl-Seitenverweise müssen mit den Referenzdaten übereinstimmen
   - Aussagen zur Gesetzgebungsabsicht müssen auf die bereitgestellten Botschaftsauszüge zurückführbar sein
   - Aussagen zu parlamentarischen Änderungen müssen mit den Abstimmungsdaten übereinstimmen
   - Keine Botschaftszitate erfinden, die nicht in den Referenzdaten enthalten sind
```

- [ ] **Step 3: Extend doctrine LAYER_INSTRUCTIONS in prompts.py**

In `agents/prompts.py`, append to the `"doctrine"` entry in `LAYER_INSTRUCTIONS` (after the existing BSK/CR block ending at "synthesize original analysis"):

```python
"""

When preparatory materials (Materialien) are provided in the prompt:
- Ground the Entstehungsgeschichte section in actual Botschaft quotes
- Cite with exact BBl page references: "BBl 1999 6045"
- Include the Federal Council's stated intent for the provision
- Note where the parliamentary process modified the Federal Council's proposal
- In the Norminhalt and Streitstände sections, trace where judicial interpretation
  has confirmed, narrowed, or expanded the original legislative intent
- Do NOT reproduce Botschaft text verbatim — synthesize and cite"""
```

- [ ] **Step 4: Extend summary LAYER_INSTRUCTIONS in prompts.py**

Append to the `"summary"` entry in `LAYER_INSTRUCTIONS` (after "Write the summary layer using write_layer_content"):

```python
"""

When preparatory materials are provided:
- Use the Botschaft's own plain-language explanation as a starting point
- The summary should reflect what the legislature intended, not just what the text says"""
```

- [ ] **Step 5: Update evaluator prompt in prompts.py**

In `build_evaluator_prompt`, after the existing point 7 about rejecting BSK/CR mismatches (line ~137), add point 8:

```python
        "8. When preparatory materials reference data is provided, verify that "
        "cited BBl page references and legislative intent claims match the "
        "reference data. Reject fabricated Botschaft quotes.\n"
```

And renumber the existing point 8 (JSON output) to point 9.

- [ ] **Step 6: Run existing prompt tests**

Run: `uv run pytest tests/test_prompts.py -v`
Expected: All pass (no tests should break from additive changes)

- [ ] **Step 7: Commit**

```bash
git add agents/prompts.py guidelines/evaluate.md
git commit -m "feat: extend prompts and evaluation rubric for preparatory materials"
```

---

### Task 3: Inject preparatory materials into law agent and evaluator

**Files:**
- Modify: `agents/law_agent.py`
- Modify: `agents/evaluator.py`

- [ ] **Step 1: Add import in law_agent.py**

In `agents/law_agent.py`, add to the import from `agents.references` (line 14):

```python
from agents.references import format_article_text, format_commentary_refs, format_preparatory_materials
```

- [ ] **Step 2: Inject preparatory materials in law_agent.py**

After the commentary refs block (lines 59-64), add the preparatory materials block:

```python
    # Inject preparatory materials for doctrine and summary layers
    prep_materials_block = ""
    if layer_type in ("doctrine", "summary"):
        prep_materials_block = format_preparatory_materials(
            law, article_number, suffix_str,
        )
```

And after line 74 (`prompt += f"\n\n{commentary_refs_block}"`), add:

```python
    if prep_materials_block:
        prompt += f"\n\n{prep_materials_block}"
```

- [ ] **Step 3: Add import in evaluator.py**

In `agents/evaluator.py`, add `format_preparatory_materials` to the import from `agents.references`.

- [ ] **Step 4: Inject preparatory materials in evaluator.py**

After the commentary refs block (lines 108-113), add:

```python
    # Inject preparatory materials for cross-checking
    prep_materials_block = ""
    if layer_type in ("doctrine", "summary"):
        prep_materials_block = format_preparatory_materials(
            law, article_number, suffix_str,
        )
```

And after line 126 (`prompt += f"\n\n{commentary_refs_block}"`), add:

```python
    if prep_materials_block:
        prompt += f"\n\n{prep_materials_block}"
```

- [ ] **Step 5: Run existing agent tests**

Run: `uv run pytest tests/test_law_agent.py tests/test_evaluator.py -v`
Expected: All pass (format_preparatory_materials returns "" when no data exists)

- [ ] **Step 6: Commit**

```bash
git add agents/law_agent.py agents/evaluator.py
git commit -m "feat: inject preparatory materials into law agent and evaluator prompts"
```

---

### Task 4: Add gitignore entry for botschaften data

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add data/botschaften/ to .gitignore**

Append after the existing `scripts/commentary_raw/` line:

```
# Botschaft PDFs and raw text extraction (not committed)
data/botschaften/
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: add data/botschaften/ to gitignore"
```

---

## Chunk 2: Discovery & Download Scripts (Tasks 5–7)

Parliament API integration — discover affairs, download Botschaft PDFs.

### Task 5: Discovery script — query parliament API for Botschaften

**Files:**
- Create: `scripts/discover_botschaften.py`
- Create: `tests/test_discover_botschaften.py`

- [ ] **Step 1: Write failing tests for registry building**

Create `tests/test_discover_botschaften.py`:

```python
"""Tests for scripts/discover_botschaften.py — parliament API registry builder."""
from __future__ import annotations

import json

import pytest

from scripts.discover_botschaften import (
    SEED_AFFAIRS,
    extract_affair_data,
    normalize_bbl_ref,
)


def test_seed_affairs_has_all_laws():
    expected_laws = {"BV", "ZGB", "OR", "ZPO", "StGB", "StPO", "SchKG", "VwVG", "BGFA"}
    assert set(SEED_AFFAIRS.keys()) == expected_laws


def test_seed_affairs_values_are_nonempty():
    for law, ids in SEED_AFFAIRS.items():
        assert len(ids) > 0, f"{law} has no seed affair IDs"
        for aid in ids:
            assert aid.isdigit(), f"{law} has non-numeric affair ID: {aid}"


def test_normalize_bbl_ref_modern():
    assert normalize_bbl_ref("BBl 2017 399") == "bbl-2017-399"


def test_normalize_bbl_ref_old_format():
    assert normalize_bbl_ref("BBl 1999 IV 4462") == "bbl-1999-IV-4462"


def test_normalize_bbl_ref_with_extra_spaces():
    assert normalize_bbl_ref("BBl  1999  6013") == "bbl-1999-6013"


def test_extract_affair_data_minimal():
    """Test extraction from a minimal affair JSON structure."""
    affair_json = {
        "id": 19990027,
        "title": "Freizügigkeit der Anwältinnen und Anwälte. Bundesgesetz",
        "shortId": "99.027",
        "affairType": {"abbreviation": "BRG", "id": 1, "name": "Geschäft des Bundesrates"},
        "state": {"id": 229, "name": "Erledigt"},
        "drafts": [
            {
                "references": [
                    {
                        "title": "Botschaft vom 28. April 1999 zum BGFA",
                        "publication": {
                            "source": "BBl 1999 6013",
                            "url": "http://www.admin.ch/opc/de/federal-gazette/1999/6013.pdf",
                            "year": "1999",
                            "page": "6013",
                            "type": {"shortName": "BBl"},
                        },
                        "date": "/Date(925336800000+0200)/",
                        "type": {"id": 1},
                    },
                ],
                "consultation": {
                    "resolutions": [
                        {
                            "council": {"name": "Nationalrat"},
                            "date": "1999-09-01T00:00:00Z",
                            "text": "Beschluss abweichend vom Entwurf",
                        },
                    ],
                },
                "preConsultations": [],
                "links": [],
                "texts": [{"type": {"id": 2}, "value": "Botschaft zum BGFA"}],
            },
        ],
        "relatedAffairs": [],
    }
    result = extract_affair_data(affair_json)
    assert result["id"] == "19990027"
    assert result["short_id"] == "99.027"
    assert len(result["botschaften"]) == 1
    assert result["botschaften"][0]["bbl_ref"] == "BBl 1999 6013"
    assert result["botschaften"][0]["bbl_ref_normalized"] == "bbl-1999-6013"
    assert "6013.pdf" in result["botschaften"][0]["pdf_url"]
    assert len(result["resolutions"]) == 1
    assert result["resolutions"][0]["council"] == "Nationalrat"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_discover_botschaften.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Implement discover_botschaften.py**

Create `scripts/discover_botschaften.py`:

```python
"""Discover Botschaften for all covered laws via the Swiss Parliament API.

Queries ws-old.parlament.ch for each seed affair, extracts BBl references
and parliamentary resolution data, follows relatedAffairs to find amendments.

Output: scripts/preparatory_materials/registry.json
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

PARLIAMENT_API_BASE = "https://ws-old.parlament.ch"
OUTPUT_DIR = Path("scripts/preparatory_materials")
REGISTRY_PATH = OUTPUT_DIR / "registry.json"

SEED_AFFAIRS: dict[str, list[str]] = {
    "BV":    ["19960091"],
    "ZGB":   ["19940083", "20150046", "20180069"],
    "OR":    ["20160077", "20080064"],
    "ZPO":   ["20060062"],
    "StGB":  ["19990063", "20100050"],
    "StPO":  ["20060013"],
    "SchKG": ["19910089"],
    "VwVG":  ["19650079"],
    "BGFA":  ["19990027"],
}

SR_NUMBERS: dict[str, str] = {
    "BV": "101", "ZGB": "210", "OR": "220", "ZPO": "272",
    "StGB": "311.0", "StPO": "312.0", "SchKG": "281.1",
    "VwVG": "172.021", "BGFA": "935.61",
}


def normalize_bbl_ref(ref: str) -> str:
    """Normalize a BBl reference to a filesystem-safe string.

    'BBl 1999 6013' -> 'bbl-1999-6013'
    'BBl 1999 IV 4462' -> 'bbl-1999-IV-4462'
    """
    parts = ref.split()
    # Filter empty strings from double spaces
    parts = [p for p in parts if p]
    # Skip 'BBl' prefix, join rest with dash
    return "bbl-" + "-".join(parts[1:])


def _parse_dotnet_date(date_str: str) -> str | None:
    """Parse .NET JSON date format '/Date(1234567890000+0200)/' to ISO date."""
    match = re.search(r"/Date\((\d+)", date_str)
    if match:
        ts = int(match.group(1)) / 1000
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
    return None


def extract_affair_data(affair: dict) -> dict:
    """Extract structured data from a parliament API affair response."""
    result = {
        "id": str(affair["id"]),
        "short_id": affair.get("shortId", ""),
        "title": affair.get("title", ""),
        "type": affair.get("affairType", {}).get("abbreviation", ""),
        "botschaften": [],
        "resolutions": [],
        "committees": [],
        "debate_documents": [],
        "enactment_ref": None,
    }

    for draft in affair.get("drafts", []):
        # Extract BBl references (Botschaften)
        for ref in draft.get("references", []):
            pub = ref.get("publication", {})
            pub_type = pub.get("type", {}).get("shortName", "")
            source = pub.get("source", "")

            if pub_type == "BBl" and source and "null" not in source:
                bbl_entry = {
                    "title": ref.get("title", ""),
                    "bbl_ref": source,
                    "bbl_ref_normalized": normalize_bbl_ref(source),
                    "pdf_url": pub.get("url", ""),
                    "date": None,
                }
                raw_date = ref.get("date", "")
                if isinstance(raw_date, str) and "/Date(" in raw_date:
                    bbl_entry["date"] = _parse_dotnet_date(raw_date)
                elif isinstance(raw_date, str) and "T" in raw_date:
                    bbl_entry["date"] = raw_date[:10]
                result["botschaften"].append(bbl_entry)

            # Check for AS (Amtliche Sammlung) reference
            if pub_type == "AS" and source:
                result["enactment_ref"] = source

        # Extract resolutions
        for res in draft.get("consultation", {}).get("resolutions", []):
            council = res.get("council", {}).get("name", "")
            date_str = res.get("date", "")
            if isinstance(date_str, str) and "T" in date_str:
                date_str = date_str[:10]
            result["resolutions"].append({
                "council": council,
                "date": date_str,
                "text": res.get("text", ""),
            })

        # Extract committee assignments
        for pre in draft.get("preConsultations", []):
            committee = pre.get("committee", {})
            if committee.get("name"):
                result["committees"].append({
                    "name": committee["name"],
                    "abbreviation": committee.get("abbreviation1", ""),
                })

        # Extract debate document links
        for link in draft.get("links", []):
            if link.get("url"):
                result["debate_documents"].append({
                    "title": link.get("title", ""),
                    "url": link["url"],
                })

    # Deduplicate committees
    seen = set()
    unique_committees = []
    for c in result["committees"]:
        key = c["abbreviation"] or c["name"]
        if key not in seen:
            seen.add(key)
            unique_committees.append(c)
    result["committees"] = unique_committees

    return result


async def fetch_affair(client: httpx.AsyncClient, affair_id: str) -> dict | None:
    """Fetch a single affair from the parliament API."""
    url = f"{PARLIAMENT_API_BASE}/affairs/{affair_id}"
    try:
        resp = await client.get(url, params={"format": "json", "lang": "de"})
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, json.JSONDecodeError) as e:
        print(f"  Warning: failed to fetch affair {affair_id}: {e}", file=sys.stderr)
        return None


async def discover_affairs_for_law(
    client: httpx.AsyncClient, law: str, seed_ids: list[str],
) -> list[dict]:
    """Discover all relevant affairs for a law starting from seed IDs."""
    visited: set[str] = set()
    affairs: list[dict] = []
    queue = list(seed_ids)

    depth = 0
    max_depth = 2

    while queue and depth <= max_depth:
        next_queue: list[str] = []
        for affair_id in queue:
            if affair_id in visited:
                continue
            visited.add(affair_id)

            await asyncio.sleep(1.0)  # Rate limiting
            raw = await fetch_affair(client, affair_id)
            if raw is None:
                continue

            # Only include BRG (Geschäft des Bundesrates) — these carry Botschaften
            affair_type = raw.get("affairType", {}).get("abbreviation", "")
            data = extract_affair_data(raw)

            if affair_type == "BRG" and data["botschaften"]:
                affairs.append(data)
                print(f"  Found: {data['short_id']} — {data['title'][:80]}")

            # Follow related affairs for next depth level
            for related in raw.get("relatedAffairs", []):
                related_id = str(related.get("id", ""))
                if related_id and related_id not in visited:
                    next_queue.append(related_id)

        queue = next_queue
        depth += 1

    return affairs


async def build_registry() -> dict:
    """Build the full registry for all covered laws."""
    registry = {
        "generated": datetime.now(tz=timezone.utc).isoformat(),
        "laws": {},
    }

    async with httpx.AsyncClient(
        headers={"Accept": "application/json"},
        timeout=30.0,
    ) as client:
        for law, seed_ids in SEED_AFFAIRS.items():
            print(f"\nDiscovering affairs for {law} (SR {SR_NUMBERS[law]})...")
            affairs = await discover_affairs_for_law(client, law, seed_ids)
            registry["laws"][law] = {
                "sr_number": SR_NUMBERS[law],
                "affairs": affairs,
            }
            print(f"  Total: {len(affairs)} affairs with Botschaften")

    return registry


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    registry = asyncio.run(build_registry())
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2, ensure_ascii=False))
    print(f"\nRegistry saved to {REGISTRY_PATH}")

    # Summary
    total_botschaften = sum(
        len(a["botschaften"])
        for law_data in registry["laws"].values()
        for a in law_data["affairs"]
    )
    print(f"Total: {total_botschaften} Botschaften across {len(registry['laws'])} laws")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_discover_botschaften.py -v`
Expected: All 7 tests pass

- [ ] **Step 5: Commit**

```bash
git add scripts/discover_botschaften.py tests/test_discover_botschaften.py
git commit -m "feat: add discovery script for parliament API Botschaften"
```

---

### Task 6: Download script — fetch Botschaft PDFs

**Files:**
- Create: `scripts/download_botschaften.py`

- [ ] **Step 1: Implement download script**

Create `scripts/download_botschaften.py`:

```python
"""Download Botschaft PDFs referenced in the registry.

Reads scripts/preparatory_materials/registry.json, downloads each unique
Botschaft PDF to data/botschaften/{bbl_ref_normalized}.pdf.
Skips already-downloaded files.

Output: data/botschaften/*.pdf
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

REGISTRY_PATH = Path("scripts/preparatory_materials/registry.json")
OUTPUT_DIR = Path("data/botschaften")


def collect_botschaften(registry: dict) -> list[dict]:
    """Collect all unique Botschaften from the registry."""
    seen: set[str] = set()
    botschaften: list[dict] = []
    for law_data in registry.get("laws", {}).values():
        for affair in law_data.get("affairs", []):
            for b in affair.get("botschaften", []):
                key = b["bbl_ref_normalized"]
                if key not in seen:
                    seen.add(key)
                    botschaften.append(b)
    return botschaften


def download_pdf(client: httpx.Client, url: str, dest: Path) -> bool:
    """Download a PDF to the destination path. Returns True on success."""
    try:
        resp = client.get(url, follow_redirects=True)
        resp.raise_for_status()
        if b"%PDF" not in resp.content[:10]:
            print(f"  Warning: response is not a PDF: {url}", file=sys.stderr)
            return False
        dest.write_bytes(resp.content)
        return True
    except httpx.HTTPError as e:
        print(f"  Warning: download failed for {url}: {e}", file=sys.stderr)
        return False


def main() -> None:
    if not REGISTRY_PATH.exists():
        print("Registry not found. Run discover_botschaften.py first.", file=sys.stderr)
        sys.exit(1)

    registry = json.loads(REGISTRY_PATH.read_text())
    botschaften = collect_botschaften(registry)
    print(f"Found {len(botschaften)} unique Botschaften in registry")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    skipped = 0
    failed = 0

    with httpx.Client(timeout=60.0) as client:
        for b in botschaften:
            dest = OUTPUT_DIR / f"{b['bbl_ref_normalized']}.pdf"
            if dest.exists():
                skipped += 1
                continue

            url = b["pdf_url"]
            if not url or "null" in url:
                print(f"  Skipping {b['bbl_ref']}: no valid URL", file=sys.stderr)
                failed += 1
                continue

            # Ensure HTTPS
            url = url.replace("http://", "https://")

            print(f"  Downloading {b['bbl_ref']}...")
            if download_pdf(client, url, dest):
                downloaded += 1
            else:
                failed += 1

    print(f"\nDone: {downloaded} downloaded, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add scripts/download_botschaften.py
git commit -m "feat: add download script for Botschaft PDFs"
```

---

### Task 7: Extraction script — PyMuPDF text extraction

**Files:**
- Create: `scripts/extract_botschaften.py`
- Create: `tests/test_extract_botschaften.py`

- [ ] **Step 1: Write failing test for text extraction**

Create `tests/test_extract_botschaften.py`:

```python
"""Tests for scripts/extract_botschaften.py — PDF text extraction."""
from __future__ import annotations

from scripts.extract_botschaften import clean_extracted_text


def test_clean_extracted_text_removes_hyphenation():
    text = "Bundes-\nverfassung"
    result = clean_extracted_text(text)
    assert "Bundesverfassung" in result


def test_clean_extracted_text_preserves_normal_newlines():
    text = "First paragraph.\n\nSecond paragraph."
    result = clean_extracted_text(text)
    assert "First paragraph." in result
    assert "Second paragraph." in result


def test_clean_extracted_text_strips_page_headers():
    text = "6013\n\nBBl 1999\n\nActual content here."
    # Page headers with just numbers or short BBl refs are common
    result = clean_extracted_text(text)
    assert "Actual content" in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_extract_botschaften.py -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Implement extract script**

Create `scripts/extract_botschaften.py`:

```python
"""Extract text from Botschaft PDFs using PyMuPDF.

Reads PDFs from data/botschaften/, extracts text with page markers,
cleans up OCR artifacts.

Output: data/botschaften/{bbl_ref_normalized}.txt
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pymupdf

PDF_DIR = Path("data/botschaften")


def clean_extracted_text(text: str) -> str:
    """Clean extracted PDF text.

    - Rejoin hyphenated line breaks (e.g., 'Bundes-\\nverfassung')
    - Remove repeated page headers
    - Normalize whitespace
    """
    # Rejoin hyphenated words at line breaks
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # Remove short lines that are just page numbers or BBl headers
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Skip lines that are just a number (page number) or short BBl ref
        if re.match(r"^\d{1,5}$", stripped):
            continue
        if re.match(r"^BBl\s+\d{4}(\s+[IVX]+)?$", stripped):
            continue
        cleaned.append(line)

    return "\n".join(cleaned)


def extract_pdf(pdf_path: Path) -> str:
    """Extract text from a PDF with page markers."""
    doc = pymupdf.open(pdf_path)
    pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        if text.strip():
            pages.append(f"[Page {page_num + 1}]\n{text}")
    doc.close()
    return clean_extracted_text("\n\n".join(pages))


def main() -> None:
    if not PDF_DIR.exists():
        print("PDF directory not found. Run download_botschaften.py first.", file=sys.stderr)
        sys.exit(1)

    pdfs = sorted(PDF_DIR.glob("*.pdf"))
    if not pdfs:
        print("No PDFs found in data/botschaften/", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(pdfs)} PDFs to extract")

    extracted = 0
    skipped = 0
    flagged = 0

    for pdf_path in pdfs:
        txt_path = pdf_path.with_suffix(".txt")
        if txt_path.exists():
            skipped += 1
            continue

        print(f"  Extracting {pdf_path.name}...")
        text = extract_pdf(pdf_path)
        txt_path.write_text(text, encoding="utf-8")
        extracted += 1

        # Quality check: flag if average chars per page is low
        page_count = text.count("[Page ")
        if page_count > 0 and len(text) / page_count < 1000:
            print(f"    Warning: low text density — may be scanned/OCR", file=sys.stderr)
            flagged += 1

    print(f"\nDone: {extracted} extracted, {skipped} skipped, {flagged} flagged")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_extract_botschaften.py -v`
Expected: All 3 tests pass

- [ ] **Step 5: Commit**

```bash
git add scripts/extract_botschaften.py tests/test_extract_botschaften.py
git commit -m "feat: add PyMuPDF text extraction for Botschaft PDFs"
```

---

## Chunk 3: Digestion & Orchestration (Tasks 8–9)

Claude-powered per-article extraction and full pipeline orchestrator.

### Task 8: Digestion script — Claude per-article extraction

**Files:**
- Create: `scripts/digest_botschaften.py`

- [ ] **Step 1: Implement digestion script**

Create `scripts/digest_botschaften.py`:

```python
"""Digest Botschaft texts into per-article structured JSON using Claude.

For each law, processes all extracted Botschaft texts and produces
per-article legislative intent, arguments, and design choices.

Output: scripts/preparatory_materials/{law}.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic

REGISTRY_PATH = Path("scripts/preparatory_materials/registry.json")
TEXT_DIR = Path("data/botschaften")
OUTPUT_DIR = Path("scripts/preparatory_materials")
ARTICLE_LISTS_PATH = Path("scripts/article_lists.json")

DIGEST_SYSTEM_PROMPT = """You are a legal document analyst for openlegalcommentary.ch. You are processing \
a Swiss Federal Council Botschaft (legislative message) to extract per-article \
legislative intent and rationale.

The Botschaft typically has this structure:
1. Allgemeiner Teil — general context, problem statement, international comparison
2. Besonderer Teil — article-by-article commentary with the Federal Council's rationale
3. Auswirkungen — financial, personnel, cantonal effects

For each article in the provided list, extract:

1. legislative_intent: What did the Federal Council intend with this provision? \
Be specific and cite the Botschaft's own language where possible.
2. key_arguments: The main arguments for the chosen design (list of strings)
3. design_choices: What alternatives were considered and why this design was chosen
4. rejected_alternatives: Specific alternatives mentioned and reasons for rejection
5. bbl_page_refs: Exact page references in the Botschaft (e.g., "6045-6048"). \
Use the [Page N] markers in the text to determine page numbers.
6. general_context: Relevant points from the Allgemeiner Teil that apply to this article

If an article is not discussed in this Botschaft, set all fields to null.

Return valid JSON with this structure:
{
  "general_context": {
    "problem_statement": "...",
    "solution_overview": "...",
    "international_comparison": "..."
  },
  "articles": {
    "1": {
      "provisions_discussed": ["Art. 1"],
      "legislative_intent": "...",
      "key_arguments": ["..."],
      "design_choices": ["..."],
      "rejected_alternatives": ["..."],
      "bbl_page_refs": ["..."],
      "general_context": "..."
    }
  }
}

Be precise. Preserve the Botschaft's original German phrasing in quotes. \
Only include articles that are actually discussed in the Botschaft."""


def load_article_numbers(law: str) -> list[str]:
    """Load article numbers for a law from article_lists.json."""
    if not ARTICLE_LISTS_PATH.exists():
        return []
    data = json.loads(ARTICLE_LISTS_PATH.read_text())
    law_data = data.get(law.upper(), {})
    articles = law_data.get("articles", [])
    return [str(a.get("number", "")) for a in articles if a.get("number")]


def digest_botschaft(
    client: anthropic.Anthropic,
    botschaft_text: str,
    bbl_ref: str,
    article_numbers: list[str],
    model: str = "claude-opus-4-20250514",
) -> dict:
    """Send a Botschaft text to Claude for per-article extraction."""
    user_prompt = (
        f"Here is the text of the Botschaft ({bbl_ref}):\n\n"
        f"{botschaft_text}\n\n"
        f"Extract per-article data for these article numbers: {', '.join(article_numbers)}\n\n"
        f"Return JSON only."
    )

    response = client.messages.create(
        model=model,
        max_tokens=16384,
        system=DIGEST_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    # Extract JSON from response
    text = response.content[0].text
    # Try to find JSON block
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]

    return json.loads(text)


def merge_digests(
    existing: dict, new_digest: dict, bbl_ref: str,
) -> dict:
    """Merge a new Botschaft digest into existing per-article data."""
    general = new_digest.get("general_context", {})
    new_articles = new_digest.get("articles", {})

    for art_num, art_data in new_articles.items():
        if art_data is None or art_data.get("legislative_intent") is None:
            continue

        source_entry = {
            "bbl_ref": bbl_ref,
            "bbl_page_refs": art_data.get("bbl_page_refs", []),
            "legislative_intent": art_data.get("legislative_intent"),
            "key_arguments": art_data.get("key_arguments", []),
            "design_choices": art_data.get("design_choices", []),
            "rejected_alternatives": art_data.get("rejected_alternatives", []),
            "general_context": art_data.get("general_context"),
        }

        if art_num not in existing:
            existing[art_num] = {
                "provisions_discussed": art_data.get("provisions_discussed", []),
                "sources": [],
                "parliamentary_modifications": [],
            }
        existing[art_num]["sources"].append(source_entry)

    return existing


def add_parliamentary_data(articles: dict, registry_affairs: list[dict]) -> dict:
    """Add parliamentary resolution data from the registry to articles."""
    # Collect all resolutions across affairs
    all_resolutions = []
    for affair in registry_affairs:
        for res in affair.get("resolutions", []):
            all_resolutions.append(res)

    # Add to each article (resolutions apply to the whole law, not per-article)
    for art_data in articles.values():
        art_data["parliamentary_modifications"] = all_resolutions

    return articles


def main() -> None:
    parser = argparse.ArgumentParser(description="Digest Botschaft texts per article")
    parser.add_argument("--law", help="Process only this law (e.g., BGFA)")
    parser.add_argument("--max-budget", type=float, default=50.0, help="Max budget in USD")
    parser.add_argument("--model", default="claude-opus-4-20250514", help="Model to use")
    args = parser.parse_args()

    if not REGISTRY_PATH.exists():
        print("Registry not found. Run discover_botschaften.py first.", file=sys.stderr)
        sys.exit(1)

    registry = json.loads(REGISTRY_PATH.read_text())
    client = anthropic.Anthropic()
    total_cost = 0.0

    laws_to_process = [args.law.upper()] if args.law else list(registry["laws"].keys())

    for law in laws_to_process:
        law_data = registry["laws"].get(law)
        if not law_data:
            print(f"Warning: {law} not found in registry", file=sys.stderr)
            continue

        print(f"\nDigesting Botschaften for {law}...")
        article_numbers = load_article_numbers(law)
        if not article_numbers:
            print(f"  Warning: no article list found for {law}", file=sys.stderr)
            continue

        articles: dict = {}

        for affair in law_data["affairs"]:
            for b in affair["botschaften"]:
                txt_path = TEXT_DIR / f"{b['bbl_ref_normalized']}.txt"
                if not txt_path.exists():
                    print(f"  Skipping {b['bbl_ref']}: text not extracted", file=sys.stderr)
                    continue

                if total_cost >= args.max_budget:
                    print(f"  Budget limit reached (${total_cost:.2f})", file=sys.stderr)
                    break

                print(f"  Processing {b['bbl_ref']}...")
                text = txt_path.read_text(encoding="utf-8")

                digest = digest_botschaft(
                    client, text, b["bbl_ref"], article_numbers, args.model,
                )

                # Rough cost estimate (Opus input + output)
                input_tokens = len(text) // 4 + 2000  # ~4 chars per token + system prompt
                output_tokens = 4000  # rough estimate
                cost = (input_tokens * 15 + output_tokens * 75) / 1_000_000
                total_cost += cost
                print(f"    Estimated cost: ${cost:.2f} (total: ${total_cost:.2f})")

                articles = merge_digests(articles, digest, b["bbl_ref"])

        # Add parliamentary resolution data
        articles = add_parliamentary_data(articles, law_data["affairs"])

        # Write output
        output = {
            "law": law,
            "sr_number": law_data["sr_number"],
            "generated": datetime.now(tz=timezone.utc).isoformat(),
            "articles": articles,
        }
        output_path = OUTPUT_DIR / f"{law.lower()}.json"
        output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
        print(f"  Saved to {output_path} ({len(articles)} articles)")

    print(f"\nTotal estimated cost: ${total_cost:.2f}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit**

```bash
git add scripts/digest_botschaften.py
git commit -m "feat: add Claude digestion script for per-article Botschaft extraction"
```

---

### Task 9: Pipeline orchestrator and CLAUDE.md update

**Files:**
- Create: `scripts/preparatory_materials_pipeline.py`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Create pipeline orchestrator**

Create `scripts/preparatory_materials_pipeline.py`:

```python
"""Orchestrate the full preparatory materials pipeline.

Runs all steps in sequence: discover → download → extract → digest.

Usage:
    uv run python -m scripts.preparatory_materials_pipeline
    uv run python -m scripts.preparatory_materials_pipeline --law BGFA
"""
from __future__ import annotations

import argparse
import subprocess
import sys


def run_step(name: str, cmd: list[str]) -> bool:
    """Run a pipeline step and return True on success."""
    print(f"\n{'='*60}")
    print(f"  Step: {name}")
    print(f"{'='*60}\n")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"\nStep '{name}' failed with exit code {result.returncode}", file=sys.stderr)
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full preparatory materials pipeline")
    parser.add_argument("--law", help="Process only this law (e.g., BGFA)")
    parser.add_argument("--max-budget", type=float, default=50.0, help="Max digestion budget in USD")
    parser.add_argument("--skip-discover", action="store_true", help="Skip discovery step")
    parser.add_argument("--skip-download", action="store_true", help="Skip download step")
    parser.add_argument("--skip-extract", action="store_true", help="Skip extraction step")
    args = parser.parse_args()

    steps = []

    if not args.skip_discover:
        steps.append(("Discover Botschaften", [sys.executable, "-m", "scripts.discover_botschaften"]))

    if not args.skip_download:
        steps.append(("Download PDFs", [sys.executable, "-m", "scripts.download_botschaften"]))

    if not args.skip_extract:
        steps.append(("Extract text", [sys.executable, "-m", "scripts.extract_botschaften"]))

    digest_cmd = [sys.executable, "-m", "scripts.digest_botschaften", "--max-budget", str(args.max_budget)]
    if args.law:
        digest_cmd.extend(["--law", args.law])
    steps.append(("Digest per article", digest_cmd))

    for name, cmd in steps:
        if not run_step(name, cmd):
            sys.exit(1)

    print(f"\n{'='*60}")
    print("  Pipeline complete!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Update CLAUDE.md with new commands**

In `CLAUDE.md`, after the existing pipeline commands section, add:

```markdown
- `uv run python -m scripts.discover_botschaften` — discover Botschaften via parliament API
- `uv run python -m scripts.download_botschaften` — download Botschaft PDFs
- `uv run python -m scripts.extract_botschaften` — extract text from Botschaft PDFs
- `uv run python -m scripts.digest_botschaften` — digest Botschaften per article (uses Claude API)
- `uv run python -m scripts.preparatory_materials_pipeline` — run full preparatory materials pipeline
- `uv run python -m scripts.preparatory_materials_pipeline --law BGFA` — run pipeline for one law
```

- [ ] **Step 3: Run all tests to verify nothing is broken**

Run: `uv run pytest -v`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add scripts/preparatory_materials_pipeline.py CLAUDE.md
git commit -m "feat: add pipeline orchestrator and update CLAUDE.md with new commands"
```

---

## Chunk 4: End-to-End Verification (Task 10)

### Task 10: Run discovery for BGFA as proof-of-concept

**Files:**
- Generated: `scripts/preparatory_materials/registry.json`

- [ ] **Step 1: Create preparatory_materials directory**

```bash
mkdir -p scripts/preparatory_materials
```

- [ ] **Step 2: Run discovery for BGFA**

```bash
uv run python -m scripts.discover_botschaften
```

Expected: Registry saved with at least 1 Botschaft for BGFA (BBl 1999 6013).

- [ ] **Step 3: Verify registry content**

Check that `scripts/preparatory_materials/registry.json` contains:
- BGFA entry with affair 19990027
- Botschaft reference BBl 1999 6013
- PDF URL pointing to admin.ch
- Parliamentary resolutions (at least the Schlussabstimmung entries)

- [ ] **Step 4: Commit registry**

```bash
git add scripts/preparatory_materials/registry.json
git commit -m "data: add parliament API registry for all covered laws"
```

- [ ] **Step 5: Run download for BGFA Botschaft**

```bash
mkdir -p data/botschaften
uv run python -m scripts.download_botschaften
```

Expected: PDF downloaded to `data/botschaften/bbl-1999-6013.pdf`

- [ ] **Step 6: Run text extraction**

```bash
uv run python -m scripts.extract_botschaften
```

Expected: Text file at `data/botschaften/bbl-1999-6013.txt` with [Page N] markers and readable German text.

- [ ] **Step 7: Run digestion for BGFA**

```bash
uv run python -m scripts.digest_botschaften --law BGFA
```

Expected: `scripts/preparatory_materials/bgfa.json` with per-article legislative intent for BGFA articles.

- [ ] **Step 8: Verify digestion quality**

Check that `bgfa.json` contains:
- Article 12 with legislative_intent mentioning Berufsregeln
- Article 13 with legislative_intent mentioning Berufsgeheimnis
- BBl page references that are plausible (6000-range)
- Parliamentary modifications from registry

- [ ] **Step 9: Commit digested data**

```bash
git add scripts/preparatory_materials/bgfa.json
git commit -m "data: add BGFA preparatory materials (Botschaft BBl 1999 6013)"
```

- [ ] **Step 10: Run full test suite**

```bash
uv run pytest -v
uv run ruff check .
```

Expected: All tests pass, no lint errors.

---

## Task Dependency Summary

```
Chunk 1 (integration):     Task 1 → Task 2 → Task 3 → Task 4
Chunk 2 (scripts):         Task 5 → Task 6 → Task 7
Chunk 3 (digestion):       Task 8 → Task 9
Chunk 4 (verification):    Task 10 (requires all above)

Chunks 1 and 2 can run in parallel.
Chunk 3 depends on Chunk 2.
Chunk 4 depends on all.
```
