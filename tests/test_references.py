"""Tests for agents/references.py — article text loading and formatting."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from agents.references import (
    _commentary_refs_cache,
    _prep_materials_cache,
    format_article_text,
    format_commentary_refs,
    format_preparatory_materials,
    load_article_texts,
    load_commentary_refs,
    load_preparatory_materials,
)


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
    texts = {
        "OR": {"41": [{"type": "list", "items": [
            {"letter": "a", "text": "First"},
            {"letter": "b", "text": "Second"},
        ]}]},
    }
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


# --- Commentary refs tests ---


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


def test_load_commentary_primary_refs(tmp_path):
    data = {
        "41": {"authors": ["Kessler"], "edition": "Doctrinal OR I, 7. Aufl. 2019"},
    }
    refs_dir = _make_refs_dir(tmp_path, "or", "primary", data)
    result = load_commentary_refs(refs_dir, "OR")
    assert "41" in result


def test_load_commentary_primary_missing_law(tmp_path):
    refs_dir = tmp_path / "commentary_refs"
    refs_dir.mkdir()
    result = load_commentary_refs(refs_dir, "ZGB")
    assert result == {}


def test_load_commentary_merges_primary_and_cr(tmp_path):
    refs_dir = tmp_path / "commentary_refs"
    refs_dir.mkdir()
    refs = {"OR": {"41": {"authors": ["Kessler"], "edition": "Doctrinal OR I"}}}
    cr = {"OR": {"41": {"authors": ["Thévenoz"], "edition": "CR CO I"}}}
    (refs_dir / "or_primary.json").write_text(json.dumps(refs))
    (refs_dir / "or_cr.json").write_text(json.dumps(cr))
    result = load_commentary_refs(refs_dir, "OR")
    assert "41" in result
    assert "primary" in result["41"]
    assert "cr" in result["41"]


def test_format_commentary_refs_basic(tmp_path):
    data = {
        "41": {
            "authors": ["Kessler"],
            "edition": "Doctrinal OR I, 7. Aufl. 2019",
            "randziffern_map": {"1-3": "Entstehungsgeschichte"},
            "positions": [
                {
                    "author": "Kessler", "n": "N. 12",
                    "topic": "Widerrechtlichkeit",
                    "position": "Erfolgsunrecht genügt",
                },
            ],
            "controversies": [],
            "cross_refs": [],
            "key_literature": [],
        },
    }
    refs_dir = _make_refs_dir(tmp_path, "or", "primary", data)
    result = format_commentary_refs(refs_dir, "OR", 41, "")
    assert "Kessler" in result
    assert "Doctrinal OR I" in result
    assert "N. 12" in result
    assert "Entstehungsgeschichte" in result


def test_format_commentary_refs_empty_for_uncovered_law(tmp_path):
    refs_dir = tmp_path / "commentary_refs"
    refs_dir.mkdir()
    result = format_commentary_refs(refs_dir, "VwVG", 5, "")
    assert result == ""


def test_format_commentary_refs_empty_for_unknown_article(tmp_path):
    data = {
        "41": {"authors": ["Kessler"], "edition": "Doctrinal OR I"},
    }
    refs_dir = _make_refs_dir(tmp_path, "or", "primary", data)
    result = format_commentary_refs(refs_dir, "OR", 999, "")
    assert result == ""


def test_format_commentary_refs_with_suffix(tmp_path):
    data = {"6a": {"authors": ["Author"], "edition": "Doctrinal OR I"}}
    refs_dir = _make_refs_dir(tmp_path, "or", "primary", data)
    result = format_commentary_refs(refs_dir, "OR", 6, "a")
    assert "Author" in result


def test_format_commentary_refs_primary_and_cr(tmp_path):
    refs_dir = tmp_path / "commentary_refs"
    refs_dir.mkdir()
    refs = {"OR": {"41": {
        "authors": ["Kessler"], "edition": "Doctrinal OR I",
        "positions": [
            {"author": "Kessler", "n": "N. 5", "topic": "T", "position": "P"},
        ],
    }}}
    cr = {"OR": {"41": {
        "authors": ["Thévenoz"], "edition": "CR CO I",
        "positions": [
            {"author": "Thévenoz", "n": "N. 3", "topic": "T", "position": "P2"},
        ],
    }}}
    (refs_dir / "or_primary.json").write_text(json.dumps(refs))
    (refs_dir / "or_cr.json").write_text(json.dumps(cr))
    result = format_commentary_refs(refs_dir, "OR", 41, "")
    assert "Doctrinal" in result
    assert "CR" in result
    assert "Kessler" in result
    assert "Thévenoz" in result


# --- Preparatory materials tests ---


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
