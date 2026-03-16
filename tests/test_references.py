"""Tests for agents/references.py — article text loading and formatting."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from agents.references import (
    _commentary_refs_cache,
    format_article_text,
    format_commentary_refs,
    load_article_texts,
    load_commentary_refs,
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


def test_load_commentary_refs_bsk(tmp_path):
    data = {
        "41": {"authors": ["Kessler"], "edition": "BSK OR I, 7. Aufl. 2019"},
    }
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
    data = {
        "41": {"authors": ["Kessler"], "edition": "BSK OR I"},
    }
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
    bsk = {"OR": {"41": {
        "authors": ["Kessler"], "edition": "BSK OR I",
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
    (refs_dir / "or_bsk.json").write_text(json.dumps(bsk))
    (refs_dir / "or_cr.json").write_text(json.dumps(cr))
    result = format_commentary_refs(refs_dir, "OR", 41, "")
    assert "BSK" in result
    assert "CR" in result
    assert "Kessler" in result
    assert "Thévenoz" in result
