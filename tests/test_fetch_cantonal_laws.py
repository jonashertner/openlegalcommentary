"""Tests for cantonal law fetcher."""

import json
from unittest.mock import patch

from scripts.fetch_cantonal_laws import (
    _extract_html_number,
    _extract_html_text_content,
    _html_to_text,
    parse_article_text,
    save_cantonal_law,
)


def test_parse_article_text_numbered_paragraphs():
    text = "1 Der Kanton ist souverän.\n2 Er gründet auf Eigenverantwortung."
    result = parse_article_text(text)
    assert len(result) == 2
    assert result[0] == {"num": "1", "text": "Der Kanton ist souverän."}
    assert result[1] == {"num": "2", "text": "Er gründet auf Eigenverantwortung."}


def test_parse_article_text_single_unnumbered():
    text = "Die Landessprachen sind Deutsch, Französisch und Italienisch."
    result = parse_article_text(text)
    assert len(result) == 1
    assert result[0] == {"num": None, "text": text}


def test_parse_article_text_empty():
    assert parse_article_text("") == []
    assert parse_article_text("  ") == []


def test_parse_article_text_continuation():
    text = "1 Der Kanton ist ein souveräner\nstand der Eidgenossenschaft."
    result = parse_article_text(text)
    assert len(result) == 1
    assert result[0]["num"] == "1"
    assert "souveräner stand" in result[0]["text"]


def test_save_cantonal_law(tmp_path):
    with patch("scripts.fetch_cantonal_laws.CANTONAL_DIR", tmp_path):
        path = save_cantonal_law(
            canton="ZH",
            title="Verfassung des Kantons Zürich",
            sr_number="101",
            language="de",
            articles=[{"number": 1, "suffix": "", "raw": "1", "title": "Kanton Zürich"}],
            article_texts={"1": [{"num": "1", "text": "Test text"}]},
            source="test",
        )
        assert path.name == "zh-kv.json"
        data = json.loads(path.read_text())
        assert data["canton"] == "ZH"
        assert data["law_key"] == "zh-kv"
        assert data["article_count"] == 1
        assert data["source"] == "test"
        assert data["article_texts"]["1"][0]["text"] == "Test text"


def test_extract_html_number():
    html = "<span class='number'>1</span>"
    assert _extract_html_number(html) == "1"
    assert _extract_html_number("<p>no number</p>") == ""


def test_extract_html_text_content():
    html = (
        "<div class='paragraph'>"
        "<span class='number'>1</span>"
        "<p><span class='text_content'>Der Kanton.</span></p>"
        "</div>"
    )
    text = _extract_html_text_content(html)
    assert "Der Kanton." in text
    # Number should be stripped
    assert not text.startswith("1")


def test_html_to_text():
    html = "<p>Hello <b>world</b></p>"
    assert "Hello world" in _html_to_text(html)
