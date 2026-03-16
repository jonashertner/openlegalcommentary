"""Tests for PDF raw text extraction."""
from __future__ import annotations

from scripts.extract_commentary import (
    VOLUME_CONFIG,
    clean_ocr_text,
    parse_article_key_from_filename,
    split_articles,
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
    raw = (
        "Art. 6a\n\nAuthor\n\nText of 6a...\n\n"
        "Art. 7\n\nOther\n\nText of 7..."
    )
    articles = split_articles(raw, "OR")
    assert "6a" in articles
    assert "7" in articles


def test_volume_config_has_all_volumes():
    expected = {
        "bsk_or_i", "bsk_or_ii", "cr_co_i",
        "bsk_bv", "bsk_stgb", "bsk_zpo", "bsk_stpo",
    }
    assert set(VOLUME_CONFIG.keys()) == expected


def test_parse_article_key_simple():
    assert parse_article_key_from_filename("BSK-BV-Achermann-Art-121.pdf") == "121"


def test_parse_article_key_with_suffix():
    assert parse_article_key_from_filename("BSK-BV-Alig-Griffel-Art-75b.pdf") == "75b"


def test_parse_article_key_with_ziff():
    assert parse_article_key_from_filename(
        "BSK-BV-Achermann-Art-197-Ziff-8.pdf",
    ) == "197ziff8"


def test_parse_article_key_with_compound_ziff():
    assert parse_article_key_from_filename(
        "BSK-BV-Epiney-Art-196-Ziff-1-2.pdf",
    ) == "196ziff1-2"


def test_parse_article_key_non_article():
    assert parse_article_key_from_filename("BSK-BV-1-Abschnitt.pdf") is None
    assert parse_article_key_from_filename("BSK-BV-Inhaltsverzeichnis.pdf") is None
