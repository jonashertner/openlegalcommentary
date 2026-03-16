# BSK/CR Commentary Integration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate BSK/CR PDF commentaries as structured reference sources into the commentary generation pipeline, grounding doctrine in real, citable author positions.

**Architecture:** Two-pass extraction (PyMuPDF raw text → Claude Sonnet structured digestion) produces per-article reference JSON files. A new `agents/references.py` module loads and formats these references (plus existing article texts) for injection into law agent and evaluator prompts.

**Tech Stack:** Python 3.12, PyMuPDF, Anthropic SDK, Pydantic, pytest

**Spec:** `docs/superpowers/specs/2026-03-16-bsk-commentary-integration-design.md`

---

## Chunk 1: Foundation — Schema, References Module, Config

### Task 1: Pydantic Schema for Commentary References

**Files:**
- Create: `scripts/commentary_schema.py`
- Test: `tests/test_commentary_schema.py`

- [ ] **Step 1: Write failing tests for the schema**

```python
"""Tests for commentary reference schema."""
from __future__ import annotations

import pytest

from scripts.commentary_schema import ArticleRef, Position, Controversy


def test_article_ref_required_fields():
    ref = ArticleRef(authors=["Kessler"], edition="BSK OR I, 7. Aufl. 2019")
    assert ref.authors == ["Kessler"]
    assert ref.edition == "BSK OR I, 7. Aufl. 2019"
    assert ref.positions == []
    assert ref.controversies == []
    assert ref.randziffern_map == {}
    assert ref.cross_refs == []
    assert ref.key_literature == []


def test_article_ref_authors_required_nonempty():
    with pytest.raises(ValueError):
        ArticleRef(authors=[], edition="BSK OR I")


def test_article_ref_edition_required():
    with pytest.raises(ValueError):
        ArticleRef(authors=["Kessler"], edition="")


def test_position_model():
    p = Position(author="Kessler", n="N. 12", topic="Widerrechtlichkeit", position="Erfolgsunrecht genügt")
    assert p.author == "Kessler"
    assert p.n == "N. 12"


def test_controversy_model():
    c = Controversy(
        topic="Organhaftung",
        positions={"Kessler (N. 30)": "lex specialis", "Huguenin": "Parallelanwendung"},
    )
    assert len(c.positions) == 2


def test_article_ref_full():
    ref = ArticleRef(
        authors=["Kessler", "Widmer Lüchinger"],
        edition="BSK OR I, 7. Aufl. 2019",
        randziffern_map={"1-3": "Entstehungsgeschichte", "4-8": "Systematik"},
        positions=[Position(author="Kessler", n="N. 12", topic="Widerrechtlichkeit", position="Erfolgsunrecht genügt")],
        controversies=[Controversy(topic="Organhaftung", positions={"A": "yes", "B": "no"})],
        cross_refs=["Art. 97 OR"],
        key_literature=["Gauch/Schluep/Schmid, OR AT, 11. Aufl. 2020"],
    )
    assert len(ref.positions) == 1
    assert len(ref.controversies) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_commentary_schema.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.commentary_schema'`

- [ ] **Step 3: Implement the schema**

```python
"""Pydantic schema for BSK/CR commentary reference data."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class Position(BaseModel):
    author: str
    n: str
    topic: str
    position: str


class Controversy(BaseModel):
    topic: str
    positions: dict[str, str] = Field(min_length=2)


class ArticleRef(BaseModel):
    authors: list[str] = Field(min_length=1)
    edition: str = Field(min_length=1)
    randziffern_map: dict[str, str] = Field(default_factory=dict)
    positions: list[Position] = Field(default_factory=list)
    controversies: list[Controversy] = Field(default_factory=list)
    cross_refs: list[str] = Field(default_factory=list)
    key_literature: list[str] = Field(default_factory=list)

    @field_validator("authors")
    @classmethod
    def authors_nonempty(cls, v):
        if not v:
            raise ValueError("authors must not be empty")
        return v
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_commentary_schema.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/commentary_schema.py tests/test_commentary_schema.py
git commit -m "feat: add Pydantic schema for BSK/CR commentary references"
```

---

### Task 2: `agents/references.py` — Relocate Article Text Functions

**Files:**
- Create: `agents/references.py`
- Modify: `agents/law_agent.py` (remove `_load_article_texts`, `_format_article_text`, import from `references`)
- Modify: `agents/evaluator.py` (replace `from agents.law_agent import _format_article_text`)
- Test: `tests/test_references.py`

- [ ] **Step 1: Write failing tests for relocated article text functions**

```python
"""Tests for agents/references.py — article text loading and formatting."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from agents.references import load_article_texts, format_article_text


def test_load_article_texts(tmp_path):
    texts = {"OR": {"41": [{"text": "Wer einem andern widerrechtlich Schaden zufügt"}]}}
    texts_path = tmp_path / "article_texts.json"
    texts_path.write_text(json.dumps(texts))
    with patch("agents.references.ARTICLE_TEXTS_PATH", texts_path):
        result = load_article_texts()
        assert "OR" in result
        assert "41" in result["OR"]


def test_load_article_texts_caching(tmp_path):
    texts = {"OR": {"41": [{"text": "Test"}]}}
    texts_path = tmp_path / "article_texts.json"
    texts_path.write_text(json.dumps(texts))
    with patch("agents.references.ARTICLE_TEXTS_PATH", texts_path):
        with patch("agents.references._article_texts_cache", None):
            result1 = load_article_texts()
            result2 = load_article_texts()
            assert result1 is result2


def test_load_article_texts_missing_file():
    with patch("agents.references.ARTICLE_TEXTS_PATH", Path("/nonexistent/path.json")):
        with patch("agents.references._article_texts_cache", None):
            result = load_article_texts()
            assert result == {}


def test_format_article_text_simple(tmp_path):
    texts = {"OR": {"41": [{"text": "Wer einem andern widerrechtlich Schaden zufügt"}]}}
    texts_path = tmp_path / "article_texts.json"
    texts_path.write_text(json.dumps(texts))
    with patch("agents.references.ARTICLE_TEXTS_PATH", texts_path):
        with patch("agents.references._article_texts_cache", None):
            result = format_article_text("OR", 41, "")
            assert "widerrechtlich" in result


def test_format_article_text_with_suffix(tmp_path):
    texts = {"OR": {"6a": [{"text": "Art 6a text"}]}}
    texts_path = tmp_path / "article_texts.json"
    texts_path.write_text(json.dumps(texts))
    with patch("agents.references.ARTICLE_TEXTS_PATH", texts_path):
        with patch("agents.references._article_texts_cache", None):
            result = format_article_text("OR", 6, "a")
            assert "Art 6a text" in result


def test_format_article_text_missing():
    with patch("agents.references.ARTICLE_TEXTS_PATH", Path("/nonexistent/path.json")):
        with patch("agents.references._article_texts_cache", None):
            result = format_article_text("OR", 999, "")
            assert result == ""


def test_format_article_text_list_items(tmp_path):
    texts = {"OR": {"41": [{"type": "list", "items": [{"letter": "a", "text": "First"}, {"letter": "b", "text": "Second"}]}]}}
    texts_path = tmp_path / "article_texts.json"
    texts_path.write_text(json.dumps(texts))
    with patch("agents.references.ARTICLE_TEXTS_PATH", texts_path):
        with patch("agents.references._article_texts_cache", None):
            result = format_article_text("OR", 41, "")
            assert "a. First" in result
            assert "b. Second" in result


def test_format_article_text_numbered_para(tmp_path):
    texts = {"OR": {"41": [{"num": "1", "text": "Para one"}]}}
    texts_path = tmp_path / "article_texts.json"
    texts_path.write_text(json.dumps(texts))
    with patch("agents.references.ARTICLE_TEXTS_PATH", texts_path):
        with patch("agents.references._article_texts_cache", None):
            result = format_article_text("OR", 41, "")
            assert "1 Para one" in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_references.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.references'`

- [ ] **Step 3: Implement `agents/references.py` with article text functions**

Move the logic from `agents/law_agent.py` lines 20–51 into `agents/references.py`. The functions become public (no underscore prefix).

```python
"""Shared reference loading and formatting for the agent pipeline.

Consolidates article text and commentary reference loading, used by both
the law agent and evaluator.
"""
from __future__ import annotations

import json
from pathlib import Path

ARTICLE_TEXTS_PATH = Path("scripts/article_texts.json")

_article_texts_cache: dict | None = None


def load_article_texts() -> dict:
    """Load article texts from JSON, with module-level caching."""
    global _article_texts_cache
    if _article_texts_cache is not None:
        return _article_texts_cache
    if ARTICLE_TEXTS_PATH.exists():
        _article_texts_cache = json.loads(ARTICLE_TEXTS_PATH.read_text())
        return _article_texts_cache
    _article_texts_cache = {}
    return _article_texts_cache


def format_article_text(law: str, article_number: int, suffix: str) -> str:
    """Format article text from article_texts.json for prompt injection."""
    texts = load_article_texts()
    key = f"{article_number}{suffix}"
    paragraphs = texts.get(law.upper(), {}).get(key, [])
    if not paragraphs:
        return ""
    lines = []
    for p in paragraphs:
        if p.get("type") == "list":
            for item in p.get("items", []):
                lines.append(f"  {item['letter']}. {item['text']}")
        elif p.get("num"):
            lines.append(f"  {p['num']} {p.get('text', '')}")
        else:
            lines.append(p.get("text", ""))
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_references.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Update `agents/law_agent.py` to import from `references.py`**

Remove `_article_texts_cache`, `_load_article_texts()`, and `_format_article_text()` (lines 20–51). Replace with import:

```python
from agents.references import format_article_text
```

Update the call at line 86 from `_format_article_text(law, article_number, suffix_str)` to `format_article_text(law, article_number, suffix_str)`.

- [ ] **Step 6: Update `agents/evaluator.py` to import from `references.py`**

Replace line 15:
```python
from agents.law_agent import _format_article_text
```
with:
```python
from agents.references import format_article_text
```

Update the call at line 100 from `_format_article_text(...)` to `format_article_text(...)`.

- [ ] **Step 7: Run full test suite to verify no regressions**

Run: `uv run pytest -v`
Expected: All existing tests PASS (test_law_agent, test_evaluator, etc.)

- [ ] **Step 8: Run linter**

Run: `uv run ruff check .`
Expected: No errors

- [ ] **Step 9: Commit**

```bash
git add agents/references.py agents/law_agent.py agents/evaluator.py tests/test_references.py
git commit -m "refactor: extract article text functions into agents/references.py"
```

---

### Task 3: Add Commentary Ref Loading to `agents/references.py`

**Files:**
- Modify: `agents/references.py`
- Test: `tests/test_references.py` (extend)

- [ ] **Step 1: Write failing tests for commentary ref loading and formatting**

Add to `tests/test_references.py`:

```python
from agents.references import load_commentary_refs, format_commentary_refs, _commentary_refs_cache


@pytest.fixture(autouse=True)
def clear_commentary_cache():
    """Clear the module-level commentary refs cache between tests."""
    _commentary_refs_cache.clear()
    yield
    _commentary_refs_cache.clear()


def _make_refs_dir(tmp_path, law, source, data):
    """Helper to write a commentary refs JSON file."""
    refs_dir = tmp_path / "commentary_refs"
    refs_dir.mkdir(exist_ok=True)
    path = refs_dir / f"{law.lower()}_{source}.json"
    path.write_text(json.dumps({law.upper(): data}))
    return refs_dir


def test_load_commentary_refs_bsk(tmp_path):
    data = {"41": {"authors": ["Kessler"], "edition": "BSK OR I, 7. Aufl. 2019"}}
    refs_dir = _make_refs_dir(tmp_path, "or", "bsk", data)
    result = load_commentary_refs(refs_dir, "OR")
    assert "41" in result


def test_load_commentary_refs_missing_law(tmp_path):
    refs_dir = tmp_path / "commentary_refs"
    refs_dir.mkdir()
    result = load_commentary_refs(refs_dir, "ZGB")
    assert result == {}


def test_load_commentary_refs_merges_bsk_and_cr(tmp_path):
    refs_dir = tmp_path / "commentary_refs"
    refs_dir.mkdir()
    bsk = {"OR": {"41": {"authors": ["Kessler"], "edition": "BSK OR I"}}}
    cr = {"OR": {"41": {"authors": ["Thévenoz"], "edition": "CR CO I"}}}
    (refs_dir / "or_bsk.json").write_text(json.dumps(bsk))
    (refs_dir / "or_cr.json").write_text(json.dumps(cr))
    result = load_commentary_refs(refs_dir, "OR")
    assert "41" in result
    assert "bsk" in result["41"]
    assert "cr" in result["41"]


def test_format_commentary_refs_basic(tmp_path):
    data = {
        "41": {
            "authors": ["Kessler"],
            "edition": "BSK OR I, 7. Aufl. 2019",
            "randziffern_map": {"1-3": "Entstehungsgeschichte"},
            "positions": [{"author": "Kessler", "n": "N. 12", "topic": "Widerrechtlichkeit", "position": "Erfolgsunrecht genügt"}],
            "controversies": [],
            "cross_refs": [],
            "key_literature": [],
        }
    }
    refs_dir = _make_refs_dir(tmp_path, "or", "bsk", data)
    result = format_commentary_refs(refs_dir, "OR", 41, "")
    assert "Kessler" in result
    assert "BSK OR I" in result
    assert "N. 12" in result
    assert "Entstehungsgeschichte" in result


def test_format_commentary_refs_empty_for_uncovered_law(tmp_path):
    refs_dir = tmp_path / "commentary_refs"
    refs_dir.mkdir()
    result = format_commentary_refs(refs_dir, "VwVG", 5, "")
    assert result == ""


def test_format_commentary_refs_empty_for_unknown_article(tmp_path):
    data = {"41": {"authors": ["Kessler"], "edition": "BSK OR I"}}
    refs_dir = _make_refs_dir(tmp_path, "or", "bsk", data)
    result = format_commentary_refs(refs_dir, "OR", 999, "")
    assert result == ""


def test_format_commentary_refs_with_suffix(tmp_path):
    data = {"6a": {"authors": ["Author"], "edition": "BSK OR I"}}
    refs_dir = _make_refs_dir(tmp_path, "or", "bsk", data)
    result = format_commentary_refs(refs_dir, "OR", 6, "a")
    assert "Author" in result


def test_format_commentary_refs_bsk_and_cr(tmp_path):
    refs_dir = tmp_path / "commentary_refs"
    refs_dir.mkdir()
    bsk = {"OR": {"41": {"authors": ["Kessler"], "edition": "BSK OR I", "positions": [{"author": "Kessler", "n": "N. 5", "topic": "T", "position": "P"}]}}}
    cr = {"OR": {"41": {"authors": ["Thévenoz"], "edition": "CR CO I", "positions": [{"author": "Thévenoz", "n": "N. 3", "topic": "T", "position": "P2"}]}}}
    (refs_dir / "or_bsk.json").write_text(json.dumps(bsk))
    (refs_dir / "or_cr.json").write_text(json.dumps(cr))
    result = format_commentary_refs(refs_dir, "OR", 41, "")
    assert "BSK" in result
    assert "CR" in result
    assert "Kessler" in result
    assert "Thévenoz" in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_references.py -v -k "commentary"`
Expected: FAIL — `ImportError: cannot import name 'load_commentary_refs'`

- [ ] **Step 3: Implement commentary ref loading and formatting**

Add to `agents/references.py`:

```python
_commentary_refs_cache: dict[tuple, dict] = {}


def load_commentary_refs(refs_root: Path, law: str) -> dict:
    """Load and merge BSK + CR commentary references for a law.

    Returns a dict keyed by article number string. When both BSK and CR
    exist for the same article, the value is {"bsk": {...}, "cr": {...}}.
    When only one source exists, it's {"bsk": {...}} or {"cr": {...}}.
    Returns empty dict if no files exist.
    """
    cache_key = (str(refs_root), law)
    if cache_key in _commentary_refs_cache:
        return _commentary_refs_cache[cache_key]

    merged: dict = {}
    for source in ("bsk", "cr"):
        path = refs_root / f"{law.lower()}_{source}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        articles = data.get(law.upper(), {})
        for art_key, art_data in articles.items():
            if art_key not in merged:
                merged[art_key] = {}
            merged[art_key][source] = art_data

    _commentary_refs_cache[cache_key] = merged
    return merged


def _format_single_source(source_label: str, data: dict) -> str:
    """Format a single BSK or CR source block."""
    lines = []
    lines.append(f"### {source_label}")
    lines.append(f"Authors: {', '.join(data.get('authors', []))}")
    lines.append(f"Edition: {data.get('edition', '')}")

    rz_map = data.get("randziffern_map", {})
    if rz_map:
        lines.append("")
        lines.append("Randziffern overview:")
        for rz_range, topic in rz_map.items():
            lines.append(f"- N. {rz_range}: {topic}")

    positions = data.get("positions", [])
    if positions:
        lines.append("")
        lines.append("Key positions:")
        for p in positions:
            lines.append(f"- {p['author']}, {p['n']}: {p['position']}")

    controversies = data.get("controversies", [])
    if controversies:
        lines.append("")
        lines.append("Doctrinal controversies:")
        for c in controversies:
            parts = [f"{author}: {pos}" for author, pos in c["positions"].items()]
            lines.append(f"- {c['topic']}: {'; '.join(parts)}")

    cross_refs = data.get("cross_refs", [])
    if cross_refs:
        lines.append("")
        lines.append(f"Cross-references: {', '.join(cross_refs)}")

    key_lit = data.get("key_literature", [])
    if key_lit:
        lines.append("")
        lines.append("Key literature:")
        for lit in key_lit:
            lines.append(f"- {lit}")

    return "\n".join(lines)


def format_commentary_refs(
    refs_root: Path, law: str, article_number: int, suffix: str,
) -> str:
    """Format commentary references for prompt injection.

    Returns empty string if no data available.
    """
    refs = load_commentary_refs(refs_root, law)
    key = f"{article_number}{suffix}"
    article_refs = refs.get(key)
    if not article_refs:
        return ""

    blocks = []
    blocks.append("## Doctrinal Reference Data (BSK / CR)")
    blocks.append("")

    for source in ("bsk", "cr"):
        if source in article_refs:
            label = "BSK" if source == "bsk" else "CR"
            blocks.append(_format_single_source(label, article_refs[source]))
            blocks.append("")

    blocks.append("Use these references to ground your doctrinal analysis. Cite authors with proper BSK/CR Randziffern.")
    blocks.append("Do NOT reproduce commentary text — synthesize original analysis that cites specific positions.")

    return "\n".join(blocks)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_references.py -v`
Expected: All tests PASS (both article text and commentary ref tests)

- [ ] **Step 5: Run full test suite and linter**

Run: `uv run pytest -v && uv run ruff check .`
Expected: All PASS, no lint errors

- [ ] **Step 6: Commit**

```bash
git add agents/references.py tests/test_references.py
git commit -m "feat: add commentary ref loading and formatting to references.py"
```

---

### Task 4: Config and Prompt Updates

**Files:**
- Modify: `agents/config.py`
- Modify: `agents/prompts.py`
- Modify: `agents/law_agent.py` (add commentary ref injection)
- Modify: `agents/evaluator.py` (add commentary ref injection)
- Test: `tests/test_config.py` (extend), `tests/test_prompts.py` (extend)

- [ ] **Step 1: Write failing test for config**

Add to `tests/test_config.py`:

```python
def test_config_has_commentary_refs_root():
    config = AgentConfig()
    assert config.commentary_refs_root == Path("scripts/commentary_refs")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v -k "commentary"`
Expected: FAIL — `AttributeError: 'AgentConfig' has no attribute 'commentary_refs_root'`

- [ ] **Step 3: Add `commentary_refs_root` to config**

In `agents/config.py`, add to the `AgentConfig` dataclass:

```python
commentary_refs_root: Path = field(default_factory=lambda: Path("scripts/commentary_refs"))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Write failing test for updated prompts**

Add to `tests/test_prompts.py`:

```python
def test_doctrine_instructions_mention_bsk():
    from agents.prompts import LAYER_INSTRUCTIONS
    doctrine = LAYER_INSTRUCTIONS["doctrine"]
    assert "BSK" in doctrine
    assert "synthesize original analysis" in doctrine.lower() or "Do NOT reproduce" in doctrine


def test_evaluator_prompt_mentions_reference_data(tmp_path):
    guidelines = tmp_path / "guidelines"
    guidelines.mkdir()
    (guidelines / "evaluate.md").write_text("# Evaluation\n\nTest rubric.")
    prompt = build_evaluator_prompt(guidelines)
    assert "reference data" in prompt.lower()
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `uv run pytest tests/test_prompts.py -v -k "bsk or reference_data"`
Expected: FAIL

- [ ] **Step 7: Update `agents/prompts.py`**

Add to `LAYER_INSTRUCTIONS["doctrine"]` (before the closing `"""`):

```python
\n
When doctrinal reference data (BSK/CR) is provided in the prompt:
- Ground your analysis in the named positions from the reference data
- Cite BSK authors with Randziffern: Kessler, BSK OR I, Art. 41 N. 12
- Cite CR authors with Randziffern: Thévenoz, CR CO I, Art. 41 N. 8
- Present doctrinal controversies from the references with named positions on each side
- Do NOT reproduce commentary text — synthesize original analysis
```

Add to `build_evaluator_prompt()` task instructions (before the JSON format block):

```python
"7. When doctrinal reference data is provided, cross-check cited BSK/CR "
"authors and Randziffern against the reference data\n"
"8. Reject if BSK/CR positions are cited that don't appear in the references\n"
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `uv run pytest tests/test_prompts.py -v`
Expected: PASS

- [ ] **Step 9: Add commentary ref injection to `agents/law_agent.py`**

Add import at top:
```python
from agents.references import format_commentary_refs
```

In `generate_layer()`, after the `article_text_block` construction (around line 92), add:

```python
    commentary_refs_block = ""
    if layer_type in ("doctrine", "summary"):
        commentary_refs_block = format_commentary_refs(
            config.commentary_refs_root, law, article_number, suffix_str,
        )
```

In the prompt construction, append:
```python
    if commentary_refs_block:
        prompt += f"\n\n{commentary_refs_block}"
```

- [ ] **Step 10: Add commentary ref injection to `agents/evaluator.py`**

Add import at top:
```python
from agents.references import format_commentary_refs
```

In `evaluate_layer()`, after the `article_text_block` construction, add (note: same layer_type filter as law agent — only doctrine and summary):

```python
    commentary_refs_block = ""
    if layer_type in ("doctrine", "summary"):
        commentary_refs_block = format_commentary_refs(
            config.commentary_refs_root, law, article_number, suffix_str,
        )
```

Append to prompt:
```python
    if commentary_refs_block:
        prompt += f"\n\n{commentary_refs_block}"
```

- [ ] **Step 11: Run full test suite and linter**

Run: `uv run pytest -v && uv run ruff check .`
Expected: All PASS, no lint errors

- [ ] **Step 12: Commit**

```bash
git add agents/config.py agents/prompts.py agents/law_agent.py agents/evaluator.py tests/test_config.py tests/test_prompts.py
git commit -m "feat: integrate commentary refs into pipeline prompts and evaluation"
```

---

### Task 5: Guidelines and Gitignore Updates

**Files:**
- Modify: `guidelines/global.md`
- Modify: `guidelines/evaluate.md`
- Modify: `.gitignore`
- Modify: `pyproject.toml`

- [ ] **Step 1: Update `guidelines/global.md`**

Add after §II.2 Doktrin bullet list (after the cross-reference notation line):

```markdown

- Wenn BSK/CR-Referenzdaten verfügbar sind, müssen doktrinäre Positionen auf die Referenzdaten gestützt werden
- BSK-Zitierformat: Kessler, BSK OR I, Art. 41 N. 12
- CR-Zitierformat: Thévenoz, CR CO I, Art. 41 N. 8
- Der Kommentartext darf nicht paraphrasiert oder reproduziert werden — eigenständige Analyse, die spezifische Positionen zitiert
```

- [ ] **Step 2: Update `guidelines/evaluate.md`**

Add to §I.1 "Keine unbelegten Rechtsaussagen" (after the existing Prüfmethode paragraph):

```markdown

**Erweiterung bei BSK/CR-Referenzdaten**: Wenn Referenzdaten bereitgestellt werden, müssen zitierte BSK/CR-Autorinnen/Autoren und Randziffern mit den Referenzdaten übereinstimmen.
```

Add to §II.5 "Akademische Strenge":

```markdown
- Auseinandersetzung mit den in den Referenzdaten identifizierten doktrinären Kontroversen
```

- [ ] **Step 3: Update `.gitignore`**

Add at the end:

```
# Commentary PDFs and raw extraction (not committed)
data/commentary_pdfs/
scripts/commentary_raw/
```

- [ ] **Step 4: Add `pymupdf` to `pyproject.toml`**

Add `"pymupdf>=1.24"` to the `dependencies` list.

- [ ] **Step 5: Run linter and tests**

Run: `uv run ruff check . && uv run pytest -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add guidelines/global.md guidelines/evaluate.md .gitignore pyproject.toml
git commit -m "feat: update guidelines, gitignore, and deps for BSK/CR integration"
```

---

## Chunk 2: PDF Extraction Pipeline

### Task 6: Pass 1 — Raw Text Extraction Script

**Files:**
- Create: `scripts/extract_commentary.py`
- Test: `tests/test_extract_commentary.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for PDF raw text extraction."""
from __future__ import annotations

import json

import pytest

from scripts.extract_commentary import (
    clean_ocr_text,
    split_articles,
    VOLUME_CONFIG,
)


def test_clean_ocr_text_randziffern():
    assert clean_ocr_text("N.  12") == "N. 12"
    assert clean_ocr_text("N.12") == "N. 12"


def test_clean_ocr_text_whitespace():
    assert clean_ocr_text("  foo   bar  ") == "foo bar"
    assert clean_ocr_text("foo\n\n\n\nbar") == "foo\n\nbar"


def test_clean_ocr_text_bge_references():
    assert clean_ocr_text("BGE 130 III  182") == "BGE 130 III 182"


def test_split_articles_basic():
    raw = (
        "Art. 41\n\nKessler\n\nWer einem andern widerrechtlich...\n\n"
        "Art. 42\n\nWidmer\n\nSchadenersatz..."
    )
    articles = split_articles(raw, "OR")
    assert "41" in articles
    assert "42" in articles
    assert "widerrechtlich" in articles["41"]


def test_split_articles_with_suffix():
    raw = "Art. 6a\n\nAuthor\n\nText of 6a...\n\nArt. 7\n\nOther\n\nText of 7..."
    articles = split_articles(raw, "OR")
    assert "6a" in articles
    assert "7" in articles


def test_volume_config_has_all_volumes():
    expected = {"bsk_or_i", "bsk_or_ii", "cr_co_i", "bsk_bv", "bsk_stgb", "bsk_zpo", "bsk_stpo"}
    assert set(VOLUME_CONFIG.keys()) == expected
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_extract_commentary.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement `scripts/extract_commentary.py`**

```python
"""Pass 1: Extract raw text from BSK/CR PDFs and split into per-article chunks.

Usage:
    uv run python -m scripts.extract_commentary data/commentary_pdfs/bsk_or_i.pdf --volume bsk_or_i
    uv run python -m scripts.extract_commentary --all  # process all PDFs in data/commentary_pdfs/
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

VOLUME_CONFIG: dict[str, dict] = {
    "bsk_or_i": {"law": "OR", "source": "bsk", "article_range": (1, 529)},
    "bsk_or_ii": {"law": "OR", "source": "bsk", "article_range": (530, 1186)},
    "cr_co_i": {"law": "OR", "source": "cr", "article_range": (1, 529)},
    "bsk_bv": {"law": "BV", "source": "bsk", "article_range": (1, 197)},
    "bsk_stgb": {"law": "StGB", "source": "bsk", "article_range": (1, 401)},
    "bsk_zpo": {"law": "ZPO", "source": "bsk", "article_range": (1, 408)},
    "bsk_stpo": {"law": "StPO", "source": "bsk", "article_range": (1, 457)},
}

# Regex for article headers — matches "Art. 41", "Art. 6a", "Art. 706b" etc.
ART_HEADER_RE = re.compile(r"^Art\.\s+(\d+[a-z]?)\b", re.MULTILINE)


def clean_ocr_text(text: str) -> str:
    """Fix common OCR artifacts in extracted text."""
    # Normalize Randziffern spacing
    text = re.sub(r"N\.\s*(\d+)", r"N. \1", text)
    # Fix BGE double spaces
    text = re.sub(r"(BGE\s+\d+\s+[IVX]+)\s{2,}(\d+)", r"\1 \2", text)
    # Collapse excessive whitespace
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def split_articles(raw_text: str, law: str) -> dict[str, str]:
    """Split raw text into per-article chunks keyed by article number."""
    matches = list(ART_HEADER_RE.finditer(raw_text))
    if not matches:
        logger.warning("No article headers found in text for %s", law)
        return {}

    articles = {}
    for i, match in enumerate(matches):
        art_key = match.group(1)
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
        articles[art_key] = clean_ocr_text(raw_text[start:end])

    return articles


def extract_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF using PyMuPDF."""
    import pymupdf

    doc = pymupdf.open(str(pdf_path))
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return "\n".join(pages)


def process_volume(pdf_path: Path, volume_name: str, output_dir: Path) -> Path:
    """Extract and split a single BSK/CR volume."""
    config = VOLUME_CONFIG[volume_name]
    law = config["law"]
    source = config["source"]

    logger.info("Extracting %s (%s %s)...", volume_name, law, source)
    raw_text = extract_pdf(pdf_path)
    articles = split_articles(raw_text, law)
    logger.info("Found %d articles in %s", len(articles), volume_name)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{law.lower()}_{source}.json"

    # Merge with existing data (for multi-volume laws like OR I + OR II)
    existing = {}
    if output_path.exists():
        data = json.loads(output_path.read_text())
        existing = data.get(law.upper(), {})

    existing.update(articles)
    output = {law.upper(): existing}
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    logger.info("Wrote %s", output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Extract raw text from BSK/CR PDFs")
    parser.add_argument("pdf_path", nargs="?", type=Path, help="Path to a single PDF")
    parser.add_argument("--volume", choices=VOLUME_CONFIG.keys(), help="Volume identifier")
    parser.add_argument("--all", action="store_true", help="Process all PDFs in data/commentary_pdfs/")
    parser.add_argument("--output-dir", type=Path, default=Path("scripts/commentary_raw"))
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if args.all:
        pdf_dir = Path("data/commentary_pdfs")
        for volume_name, config in VOLUME_CONFIG.items():
            pdf_path = pdf_dir / f"{volume_name}.pdf"
            if pdf_path.exists():
                process_volume(pdf_path, volume_name, args.output_dir)
            else:
                logger.warning("PDF not found: %s", pdf_path)
    elif args.pdf_path and args.volume:
        process_volume(args.pdf_path, args.volume, args.output_dir)
    else:
        parser.error("Provide --all or both pdf_path and --volume")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_extract_commentary.py -v`
Expected: PASS (tests that don't need actual PDFs)

- [ ] **Step 5: Run linter**

Run: `uv run ruff check scripts/extract_commentary.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add scripts/extract_commentary.py tests/test_extract_commentary.py
git commit -m "feat: add PDF raw text extraction script (Pass 1)"
```

---

### Task 7: Pass 2 — Structured Digestion Script

**Files:**
- Create: `scripts/digest_commentary.py`
- Test: `tests/test_digest_commentary.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for structured commentary digestion."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from scripts.digest_commentary import (
    build_digestion_prompt,
    parse_digest_response,
    chunk_long_article,
    merge_chunk_results,
    estimate_tokens,
    DigestState,
)
from scripts.commentary_schema import ArticleRef, Position, Controversy


def test_build_digestion_prompt():
    prompt = build_digestion_prompt("Art. 41\n\nKessler\n\nSome commentary text...", "OR", "de")
    assert "Art. 41" in prompt
    assert "authors" in prompt.lower()
    assert "randziffern" in prompt.lower()


def test_build_digestion_prompt_french():
    prompt = build_digestion_prompt("Art. 41\n\nThévenoz\n\nTexte...", "OR", "fr")
    assert "German" in prompt  # output should be in German


def test_parse_digest_response_valid():
    response = json.dumps({
        "authors": ["Kessler"],
        "edition": "BSK OR I, 7. Aufl. 2019",
        "randziffern_map": {"1-3": "Entstehungsgeschichte"},
        "positions": [{"author": "Kessler", "n": "N. 12", "topic": "Test", "position": "Pos"}],
        "controversies": [],
        "cross_refs": [],
        "key_literature": [],
    })
    result = parse_digest_response(response)
    assert isinstance(result, ArticleRef)
    assert result.authors == ["Kessler"]


def test_parse_digest_response_with_markdown():
    inner = json.dumps({"authors": ["Kessler"], "edition": "BSK OR I", "positions": []})
    response = f"Here is the result:\n```json\n{inner}\n```"
    result = parse_digest_response(response)
    assert result.authors == ["Kessler"]


def test_parse_digest_response_invalid():
    with pytest.raises(ValueError):
        parse_digest_response("not json at all")


def test_parse_digest_response_missing_required():
    response = json.dumps({"edition": "BSK OR I"})  # missing authors
    with pytest.raises(ValueError):
        parse_digest_response(response)


def test_estimate_tokens():
    # ~4 chars per token
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("a" * 400) == 100


def test_chunk_short_article():
    text = "N. 1 Short article text N. 2 more text"
    chunks = chunk_long_article(text, max_tokens=10000)
    assert len(chunks) == 1
    assert chunks[0][1] is None  # No primary range needed


def test_chunk_long_article():
    # Build a text that exceeds max_tokens with Randziffern markers
    parts = []
    for i in range(1, 51):
        parts.append(f"N. {i} " + "x" * 2000)
    text = "\n".join(parts)
    chunks = chunk_long_article(text, max_tokens=5000)
    assert len(chunks) > 1
    # Each chunk should have a primary range
    for _, primary_range in chunks:
        assert primary_range is not None
        assert primary_range[0] <= primary_range[1]


def test_merge_chunk_results_deduplicates():
    ref1 = ArticleRef(
        authors=["Kessler"], edition="BSK OR I",
        positions=[Position(author="Kessler", n="N. 5", topic="T", position="P1")],
        cross_refs=["Art. 97 OR"],
        key_literature=["Gauch"],
    )
    ref2 = ArticleRef(
        authors=["Kessler"], edition="BSK OR I",
        positions=[Position(author="Kessler", n="N. 15", topic="T2", position="P2")],
        cross_refs=["Art. 97 OR", "Art. 55 OR"],  # Art. 97 is duplicate
        key_literature=["Gauch", "Schwenzer"],  # Gauch is duplicate
    )
    result = merge_chunk_results([(ref1, (1, 10)), (ref2, (11, 20))])
    assert len(result.cross_refs) == 2  # Art. 97, Art. 55
    assert len(result.key_literature) == 2  # Gauch, Schwenzer
    assert len(result.positions) == 2  # N. 5 from chunk1, N. 15 from chunk2


class TestDigestState:
    def test_load_new(self, tmp_path):
        state = DigestState.load(tmp_path / "state.json")
        assert state.completed_keys == set()

    def test_save_and_load(self, tmp_path):
        path = tmp_path / "state.json"
        state = DigestState.load(path)
        state.mark_completed("41")
        state.mark_completed("42")
        state.save()
        loaded = DigestState.load(path)
        assert loaded.completed_keys == {"41", "42"}

    def test_is_completed(self, tmp_path):
        state = DigestState.load(tmp_path / "state.json")
        assert not state.is_completed("41")
        state.mark_completed("41")
        assert state.is_completed("41")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_digest_commentary.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement `scripts/digest_commentary.py`**

```python
"""Pass 2: Digest raw commentary text into structured reference data via Claude.

Usage:
    uv run python -m scripts.digest_commentary scripts/commentary_raw/or_bsk.json
    uv run python -m scripts.digest_commentary --all
    uv run python -m scripts.digest_commentary scripts/commentary_raw/or_bsk.json --resume
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import anthropic

from scripts.commentary_schema import ArticleRef, Controversy, Position

logger = logging.getLogger(__name__)

DIGESTION_PROMPT_TEMPLATE = """You are extracting structured reference data from a legal commentary article.

The text below is from a {source_type} commentary on Swiss law ({law}).
{lang_note}

Extract the following as JSON — do NOT summarize or paraphrase the text. Identify:

1. **authors**: List of author names for this article
2. **edition**: Full edition string (e.g., "BSK OR I, 7. Aufl. 2019")
3. **randziffern_map**: Map of N. ranges to topics (e.g., "1-3": "Entstehungsgeschichte")
4. **positions**: List of named doctrinal positions, each with:
   - author: who holds this position
   - n: the Randziffer reference (e.g., "N. 12")
   - topic: what the position is about
   - position: one-sentence summary of the position
5. **controversies**: Doctrinal disagreements with at least 2 named positions
   - topic: what the debate is about
   - positions: dict mapping "Author (citation)" to their position
6. **cross_refs**: List of articles referenced (e.g., "Art. 97 OR")
7. **key_literature**: List of secondary sources cited

Return ONLY valid JSON matching this schema. No markdown, no explanation.

---

{text}"""


def build_digestion_prompt(text: str, law: str, lang: str) -> str:
    """Build the prompt for structured extraction."""
    source_type = "Basler Kommentar (BSK)" if lang == "de" else "Commentaire Romand (CR)"
    lang_note = ""
    if lang == "fr":
        lang_note = "The source text is in French. Output all position summaries in German."
    return DIGESTION_PROMPT_TEMPLATE.format(
        source_type=source_type, law=law, lang_note=lang_note, text=text,
    )


def parse_digest_response(response_text: str) -> ArticleRef:
    """Parse Claude's JSON response into a validated ArticleRef."""
    json_match = re.search(r"```json\s*([\s\S]*?)```", response_text)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        json_match = re.search(r"\{[\s\S]*\}", response_text)
        if json_match:
            json_str = json_match.group(0)
        else:
            raise ValueError(f"No JSON found in response: {response_text[:200]}")

    data = json.loads(json_str)
    return ArticleRef(**data)


@dataclass
class DigestState:
    """Track which articles have been digested for resume support."""

    path: Path
    completed_keys: set[str] = field(default_factory=set)

    @classmethod
    def load(cls, path: Path) -> DigestState:
        state = cls(path=path)
        if path.exists():
            data = json.loads(path.read_text())
            state.completed_keys = set(data.get("completed", []))
        return state

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(
            {"completed": sorted(self.completed_keys)}, indent=2,
        ))

    def mark_completed(self, key: str) -> None:
        self.completed_keys.add(key)

    def is_completed(self, key: str) -> bool:
        return key in self.completed_keys


DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_MAX_INPUT_TOKENS = 20000
# Rough estimate: 1 token ≈ 4 chars for European languages
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Rough token count estimate."""
    return len(text) // CHARS_PER_TOKEN


def chunk_long_article(text: str, max_tokens: int) -> list[tuple[str, tuple[int, int] | None]]:
    """Split a long article into overlapping chunks with primary ranges.

    Returns list of (chunk_text, primary_n_range) tuples.
    primary_n_range is (start_n, end_n) — the N. range this chunk "owns"
    for deduplication. None if no chunking needed.
    """
    if estimate_tokens(text) <= max_tokens:
        return [(text, None)]

    # Find all Randziffern to determine split points
    rz_matches = list(re.finditer(r"\bN\.\s*(\d+)\b", text))
    if not rz_matches:
        # No Randziffern found — can't split intelligently, send as-is
        return [(text, None)]

    rz_numbers = [int(m.group(1)) for m in rz_matches]
    max_rz = max(rz_numbers)
    min_rz = min(rz_numbers)

    # Split into roughly equal chunks by Randziffern range
    chunk_size_chars = max_tokens * CHARS_PER_TOKEN
    overlap_chars = chunk_size_chars // 5  # 20% overlap

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size_chars, len(text))
        chunk_text = text[start:end]

        # Determine primary N. range for this chunk
        chunk_rz = [m for m in rz_matches if start <= m.start() < end - overlap_chars]
        if chunk_rz:
            primary_start = int(chunk_rz[0].group(1))
            primary_end = int(chunk_rz[-1].group(1))
        else:
            primary_start = min_rz
            primary_end = max_rz

        chunks.append((chunk_text, (primary_start, primary_end)))

        if end >= len(text):
            break
        start = end - overlap_chars

    return chunks


def merge_chunk_results(chunk_results: list[tuple[ArticleRef, tuple[int, int] | None]]) -> ArticleRef:
    """Merge multiple chunk digestion results into a single ArticleRef.

    Deduplication: positions/controversies are kept from the chunk whose
    primary range contains the referenced N. number. Cross-refs and literature
    are deduplicated by string equality.
    """
    if len(chunk_results) == 1:
        return chunk_results[0][0]

    # Use first chunk as base for authors/edition
    base = chunk_results[0][0]
    merged_rz_map: dict[str, str] = {}
    merged_positions: list[dict] = []
    merged_controversies: list[dict] = []
    seen_cross_refs: set[str] = set()
    seen_literature: set[str] = set()
    cross_refs: list[str] = []
    key_literature: list[str] = []

    for ref, primary_range in chunk_results:
        merged_rz_map.update(ref.randziffern_map)

        for p in ref.positions:
            # Extract N. number from position
            n_match = re.search(r"(\d+)", p.n)
            if n_match and primary_range:
                n_num = int(n_match.group(1))
                if not (primary_range[0] <= n_num <= primary_range[1]):
                    continue  # Skip — belongs to another chunk's primary range
            merged_positions.append(p.model_dump())

        for c in ref.controversies:
            merged_controversies.append(c.model_dump())

        for cr in ref.cross_refs:
            if cr not in seen_cross_refs:
                seen_cross_refs.add(cr)
                cross_refs.append(cr)

        for lit in ref.key_literature:
            if lit not in seen_literature:
                seen_literature.add(lit)
                key_literature.append(lit)

    return ArticleRef(
        authors=base.authors,
        edition=base.edition,
        randziffern_map=merged_rz_map,
        positions=[Position(**p) for p in merged_positions],
        controversies=[Controversy(**c) for c in merged_controversies],
        cross_refs=cross_refs,
        key_literature=key_literature,
    )


async def digest_article(
    client: anthropic.AsyncAnthropic,
    text: str,
    law: str,
    lang: str,
    model: str = DEFAULT_MODEL,
    max_input_tokens: int = DEFAULT_MAX_INPUT_TOKENS,
) -> ArticleRef:
    """Send a single article to Claude for structured extraction.

    Long articles are split into overlapping chunks and merged.
    """
    chunks = chunk_long_article(text, max_input_tokens)

    if len(chunks) == 1:
        prompt = build_digestion_prompt(chunks[0][0], law, lang)
        response = await client.messages.create(
            model=model, max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return parse_digest_response(response.content[0].text)

    # Multi-chunk: digest each, then merge
    logger.info("Splitting long article into %d chunks", len(chunks))
    chunk_results = []
    for chunk_text, primary_range in chunks:
        prompt = build_digestion_prompt(chunk_text, law, lang)
        response = await client.messages.create(
            model=model, max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        ref = parse_digest_response(response.content[0].text)
        chunk_results.append((ref, primary_range))

    return merge_chunk_results(chunk_results)


async def process_file(
    raw_path: Path,
    output_dir: Path,
    resume: bool = False,
    lang: str = "de",
    model: str = DEFAULT_MODEL,
    max_input_tokens: int = DEFAULT_MAX_INPUT_TOKENS,
) -> None:
    """Digest all articles in a raw extraction file."""
    data = json.loads(raw_path.read_text())
    # File has one top-level key (the law abbreviation)
    law = next(iter(data))
    articles = data[law]

    source = "bsk" if "_bsk" in raw_path.name else "cr"
    state_path = raw_path.parent / f"{law.lower()}_{source}_digest_state.json"
    state = DigestState.load(state_path) if resume else DigestState(state_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{law.lower()}_{source}.json"

    # Load existing output for incremental writes
    existing = {}
    if output_path.exists():
        existing_data = json.loads(output_path.read_text())
        existing = existing_data.get(law, {})

    client = anthropic.AsyncAnthropic()
    total = len(articles)
    completed = 0

    for art_key, text in articles.items():
        if state.is_completed(art_key):
            completed += 1
            continue

        try:
            ref = await digest_article(client, text, law, lang, model, max_input_tokens)
            existing[art_key] = ref.model_dump()
            state.mark_completed(art_key)
            completed += 1
            logger.info("[%d/%d] Digested %s Art. %s", completed, total, law, art_key)
        except Exception:
            logger.exception("Failed to digest %s Art. %s", law, art_key)

        # Save after each article for crash safety
        output_path.write_text(json.dumps(
            {law: existing}, indent=2, ensure_ascii=False,
        ))
        state.save()

    logger.info("Done: %d/%d articles for %s %s", completed, total, law, source)


def main():
    parser = argparse.ArgumentParser(description="Digest raw commentary into structured refs")
    parser.add_argument("raw_path", nargs="?", type=Path, help="Path to raw extraction JSON")
    parser.add_argument("--all", action="store_true", help="Process all files in scripts/commentary_raw/")
    parser.add_argument("--output-dir", type=Path, default=Path("scripts/commentary_refs"))
    parser.add_argument("--resume", action="store_true", help="Resume from previous state")
    parser.add_argument("--lang", default="de", choices=["de", "fr"], help="Source language")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Claude model for digestion")
    parser.add_argument("--max-input-tokens", type=int, default=DEFAULT_MAX_INPUT_TOKENS, help="Max tokens per chunk")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if args.all:
        raw_dir = Path("scripts/commentary_raw")
        for path in sorted(raw_dir.glob("*.json")):
            if "_digest_state" in path.name:
                continue
            lang = "fr" if "_cr" in path.name else "de"
            asyncio.run(process_file(path, args.output_dir, args.resume, lang, args.model, args.max_input_tokens))
    elif args.raw_path:
        asyncio.run(process_file(args.raw_path, args.output_dir, args.resume, args.lang, args.model, args.max_input_tokens))
    else:
        parser.error("Provide --all or a raw_path")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_digest_commentary.py -v`
Expected: All tests PASS

- [ ] **Step 5: Run linter**

Run: `uv run ruff check scripts/digest_commentary.py`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add scripts/digest_commentary.py tests/test_digest_commentary.py
git commit -m "feat: add structured digestion script (Pass 2)"
```

---

## Chunk 3: Integration Testing and End-to-End Verification

### Task 8: Integration Tests — Full Pipeline with Commentary Refs

**Files:**
- Create: `tests/test_commentary_integration.py`

- [ ] **Step 1: Write integration tests**

These test the full flow: commentary ref files exist → law agent gets them in the prompt → evaluator gets them in the prompt.

```python
"""Integration tests: commentary refs flow through the pipeline."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from agents.config import AgentConfig
from agents.law_agent import generate_layer
from agents.evaluator import evaluate_layer


@pytest.fixture
def config_with_refs(tmp_path):
    """Config with content, guidelines, and commentary refs."""
    # Content
    content_root = tmp_path / "content"
    art_dir = content_root / "or" / "art-041"
    art_dir.mkdir(parents=True)
    (art_dir / "meta.yaml").write_text(
        "law: OR\narticle: 41\ntitle: Haftung\n"
        "sr_number: '220'\nabsatz_count: 2\n"
        "fedlex_url: https://example.com\nlayers: {}\n"
    )
    (art_dir / "doctrine.md").write_text("# Doktrin\n\nPlaceholder.")

    # Guidelines
    guidelines = tmp_path / "guidelines"
    guidelines.mkdir()
    (guidelines / "global.md").write_text("# Global\n\nTest guidelines.")
    (guidelines / "or.md").write_text("# OR\n\nTest OR guidelines.")
    (guidelines / "evaluate.md").write_text("# Evaluation\n\nTest rubric.")

    # Commentary refs
    refs_dir = tmp_path / "commentary_refs"
    refs_dir.mkdir()
    refs_data = {
        "OR": {
            "41": {
                "authors": ["Kessler", "Widmer Lüchinger"],
                "edition": "BSK OR I, 7. Aufl. 2019",
                "randziffern_map": {"1-3": "Entstehungsgeschichte"},
                "positions": [
                    {"author": "Kessler", "n": "N. 12", "topic": "Widerrechtlichkeit",
                     "position": "Erfolgsunrecht genügt bei absoluten Rechtsgütern"},
                ],
                "controversies": [
                    {"topic": "Organhaftung", "positions": {
                        "Kessler (N. 30)": "Art. 55 ist lex specialis",
                        "Huguenin": "Parallelanwendung möglich",
                    }},
                ],
                "cross_refs": ["Art. 97 OR"],
                "key_literature": ["Gauch/Schluep/Schmid, OR AT"],
            }
        }
    }
    (refs_dir / "or_bsk.json").write_text(json.dumps(refs_data))

    return AgentConfig(
        content_root=content_root,
        guidelines_root=guidelines,
        commentary_refs_root=refs_dir,
    )


def test_generate_doctrine_includes_commentary_refs(config_with_refs):
    """Commentary refs appear in the prompt for doctrine layers."""
    mock_run = AsyncMock(return_value=("Generated content.", 0.05))
    with patch("agents.law_agent.run_agent", mock_run):
        asyncio.run(generate_layer(config_with_refs, "OR", 41, "", "doctrine"))
        prompt = mock_run.call_args.kwargs["prompt"]
        assert "Kessler" in prompt
        assert "BSK OR I" in prompt
        assert "N. 12" in prompt
        assert "Organhaftung" in prompt


def test_generate_caselaw_excludes_commentary_refs(config_with_refs):
    """Commentary refs are NOT injected for caselaw layers."""
    mock_run = AsyncMock(return_value=("Generated content.", 0.05))
    with patch("agents.law_agent.run_agent", mock_run):
        asyncio.run(generate_layer(config_with_refs, "OR", 41, "", "caselaw"))
        prompt = mock_run.call_args.kwargs["prompt"]
        assert "BSK OR I" not in prompt


def test_evaluator_includes_commentary_refs(config_with_refs):
    """Commentary refs are injected into evaluator prompt."""
    verdict = json.dumps({
        "verdict": "publish",
        "non_negotiables": {"keine_unbelegten_rechtsaussagen": True},
        "scores": {"praezision": 0.96},
        "feedback": {"blocking_issues": []},
    })
    mock_run = AsyncMock(return_value=(verdict, 0.05))
    with patch("agents.evaluator.run_agent", mock_run):
        asyncio.run(evaluate_layer(config_with_refs, "OR", 41, "", "doctrine"))
        prompt = mock_run.call_args.kwargs["prompt"]
        assert "Kessler" in prompt
        assert "BSK OR I" in prompt


def test_generate_doctrine_no_refs_for_uncovered_law(config_with_refs):
    """No crash when law has no commentary refs."""
    # Create ZGB content dir (no BSK refs for ZGB)
    art_dir = config_with_refs.content_root / "zgb" / "art-001"
    art_dir.mkdir(parents=True)
    (art_dir / "meta.yaml").write_text(
        "law: ZGB\narticle: 1\ntitle: Test\n"
        "sr_number: '210'\nabsatz_count: 1\n"
        "fedlex_url: https://example.com\nlayers: {}\n"
    )
    guidelines = config_with_refs.guidelines_root
    (guidelines / "zgb.md").write_text("# ZGB\n\nTest.")

    mock_run = AsyncMock(return_value=("Generated content.", 0.05))
    with patch("agents.law_agent.run_agent", mock_run):
        asyncio.run(generate_layer(config_with_refs, "ZGB", 1, "", "doctrine"))
        prompt = mock_run.call_args.kwargs["prompt"]
        assert "BSK" not in prompt  # no BSK data for ZGB
```

- [ ] **Step 2: Run integration tests**

Run: `uv run pytest tests/test_commentary_integration.py -v`
Expected: All 4 tests PASS

- [ ] **Step 3: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests PASS (old + new)

- [ ] **Step 4: Run linter on everything**

Run: `uv run ruff check .`
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add tests/test_commentary_integration.py
git commit -m "test: add integration tests for commentary ref pipeline"
```

---

### Task 9: Create Directory Structure and Verify

**Files:**
- Create: `scripts/commentary_refs/.gitkeep` (committed — this dir holds generated reference data)

Note: `data/commentary_pdfs/` and `scripts/commentary_raw/` are gitignored, so no `.gitkeep` — they're created locally by the user or extraction scripts.

- [ ] **Step 1: Create directories**

```bash
mkdir -p data/commentary_pdfs scripts/commentary_refs scripts/commentary_raw
touch scripts/commentary_refs/.gitkeep
```

- [ ] **Step 2: Verify gitignore works**

```bash
git status
# data/commentary_pdfs/ should NOT appear (gitignored)
# scripts/commentary_raw/ should NOT appear (gitignored)
# scripts/commentary_refs/.gitkeep SHOULD appear (committed)
```

- [ ] **Step 3: Run full test suite one final time**

Run: `uv run pytest -v && uv run ruff check .`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add scripts/commentary_refs/.gitkeep
git commit -m "chore: scaffold commentary refs directory structure"
```

---

## Execution Notes

### After all tasks are complete:

1. **Place PDFs** in `data/commentary_pdfs/` using the filenames from the spec (`bsk_or_i.pdf`, etc.)
2. **Run Pass 1** extraction: `uv run python -m scripts.extract_commentary --all`
3. **Run Pass 2** digestion: `uv run python -m scripts.digest_commentary --all --resume`
4. **Verify** a sample: check `scripts/commentary_refs/or_bsk.json` has structured data for Art. 41
5. **Test generation** with refs: `uv run python -m agents.pipeline single OR 41` and inspect the output for BSK citations
