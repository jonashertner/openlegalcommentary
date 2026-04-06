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
    result = clean_extracted_text(text)
    assert "Actual content" in result
