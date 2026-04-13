"""Tests for cantonal law fetcher."""

import json
from unittest.mock import patch

from scripts.fetch_cantonal_laws import (
    parse_article_text,
    parse_legislation_response,
    save_cantonal_law,
)


def test_parse_article_text_numbered_paragraphs():
    text = "1 Der Kanton Zürich ist ein souveräner Stand.\n2 Er gründet auf der Eigenverantwortung."
    result = parse_article_text(text)
    assert len(result) == 2
    assert result[0] == {"num": "1", "text": "Der Kanton Zürich ist ein souveräner Stand."}
    assert result[1] == {"num": "2", "text": "Er gründet auf der Eigenverantwortung."}


def test_parse_article_text_single_unnumbered():
    text = "Die Landessprachen sind Deutsch, Französisch, Italienisch und Rätoromanisch."
    result = parse_article_text(text)
    assert len(result) == 1
    assert result[0] == {"num": None, "text": text}


def test_parse_article_text_empty():
    assert parse_article_text("") == []
    assert parse_article_text("  ") == []


def test_save_cantonal_law(tmp_path):
    with patch("scripts.fetch_cantonal_laws.CANTONAL_DIR", tmp_path):
        path = save_cantonal_law(
            canton="ZH",
            title="Verfassung des Kantons Zürich",
            sr_number="101",
            lexfind_id=21736,
            language="de",
            articles=[{"number": 1, "suffix": "", "raw": "1", "title": "Kanton Zürich"}],
            article_texts={"1": [{"num": "1", "text": "Test text"}]},
        )
        assert path.name == "zh-kv.json"
        data = json.loads(path.read_text())
        assert data["canton"] == "ZH"
        assert data["law_key"] == "zh-kv"
        assert data["article_count"] == 1
        assert data["article_texts"]["1"][0]["text"] == "Test text"


def test_parse_legislation_response():
    response = {
        "articles": [
            {
                "article_num": "1",
                "heading": "Kanton Zürich",
                "text": "1 Souveräner Stand.\n2 Eigenverantwortung.",
            },
            {"article_num": "2", "heading": "Grundsätze", "text": "Grundlage ist das Recht."},
        ]
    }
    articles, texts = parse_legislation_response("ZH", response)
    assert len(articles) == 2
    assert articles[0]["number"] == 1
    assert articles[0]["title"] == "Kanton Zürich"
    assert len(texts["1"]) == 2
    assert texts["2"][0]["num"] is None


def test_parse_legislation_response_skips_invalid():
    response = {
        "articles": [
            {"article_num": "1", "heading": "Valid", "text": "Text"},
            {"article_num": "Übergangsbestimmung", "heading": "Invalid", "text": "Skipped"},
        ]
    }
    articles, texts = parse_legislation_response("ZH", response)
    assert len(articles) == 1
    assert articles[0]["raw"] == "1"
