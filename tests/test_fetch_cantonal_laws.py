"""Tests for cantonal law fetcher."""

import json
from unittest.mock import patch

from scripts.fetch_cantonal_laws import (
    parse_article_list_response,
    parse_article_text,
    parse_single_article_response,
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


def test_parse_article_text_continuation():
    text = "1 Der Kanton Zürich ist ein souveräner\nstand der Eidgenossenschaft."
    result = parse_article_text(text)
    assert len(result) == 1
    assert result[0]["num"] == "1"
    assert "souveräner stand der Eidgenossenschaft." in result[0]["text"]


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


def test_parse_article_list_response():
    text = """# ZH 101
**Verfassung des Kantons Zürich**
Jurisdiction: Canton ZH

**147 articles**

- Art. 1
- Art. 2 Grundsätze
- Art. 3
- Art. 5 Subsidiarität
"""
    articles = parse_article_list_response(text)
    assert len(articles) == 4
    assert articles[0]["number"] == 1
    assert articles[0]["title"] == ""
    assert articles[1]["number"] == 2
    assert articles[1]["title"] == "Grundsätze"
    assert articles[3]["number"] == 5
    assert articles[3]["title"] == "Subsidiarität"


def test_parse_article_list_response_with_paragraphs():
    text = """# LU 1
**Verfassung des Kantons Luzern**

**94 articles**

- § 1 Kanton Luzern
- § 2 Grundsätze staatlichen Handelns
"""
    articles = parse_article_list_response(text)
    assert len(articles) == 2
    assert articles[0]["title"] == "Kanton Luzern"


def test_parse_single_article_response():
    text = """# ZH 101
**Verfassung des Kantons Zürich**
Jurisdiction: Canton ZH

### § 50

1 Der Kantonsrat übt die Gewalt aus.
2 Er ist ein Milizparlament und besteht aus 180 Mitgliedern.

"""
    paragraphs = parse_single_article_response(text)
    assert len(paragraphs) == 2
    assert paragraphs[0]["num"] == "1"
    assert "Kantonsrat" in paragraphs[0]["text"]
    assert paragraphs[1]["num"] == "2"
