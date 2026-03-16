"""Tests for agents/references.py — article text loading and formatting."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from agents.references import format_article_text, load_article_texts


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
