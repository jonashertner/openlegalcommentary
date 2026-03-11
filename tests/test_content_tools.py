"""Tests for content read/write tools."""
from __future__ import annotations

import asyncio

import pytest

from agents.tools.content import create_content_tools


@pytest.fixture
def content_root(tmp_path):
    art_dir = tmp_path / "or" / "art-041"
    art_dir.mkdir(parents=True)
    (art_dir / "meta.yaml").write_text(
        "law: OR\narticle: 41\ntitle: Test\n"
        "sr_number: '220'\nabsatz_count: 1\n"
        "fedlex_url: https://example.com\nlayers: {}\n"
    )
    (art_dir / "summary.md").write_text("# Übersicht\n\nTest summary.")
    return tmp_path


def test_read_article_meta(content_root):
    tools = create_content_tools(content_root)
    result = asyncio.run(
        tools["read_article_meta"](
            {"law": "OR", "article_number": 41, "article_suffix": ""}
        )
    )
    assert "law: OR" in result["content"][0]["text"]


def test_read_layer_content(content_root):
    tools = create_content_tools(content_root)
    result = asyncio.run(
        tools["read_layer_content"](
            {"law": "OR", "article_number": 41, "article_suffix": "", "layer": "summary"}
        )
    )
    assert "Test summary" in result["content"][0]["text"]


def test_write_layer_content(content_root):
    tools = create_content_tools(content_root)
    new_content = "# Doktrin\n\n**N. 1** Test doctrine."
    asyncio.run(
        tools["write_layer_content"](
            {
                "law": "OR", "article_number": 41, "article_suffix": "",
                "layer": "doctrine", "content": new_content,
            }
        )
    )
    written = (content_root / "or" / "art-041" / "doctrine.md").read_text()
    assert written == new_content


def test_read_missing_meta(content_root):
    tools = create_content_tools(content_root)
    result = asyncio.run(
        tools["read_article_meta"](
            {"law": "OR", "article_number": 999, "article_suffix": ""}
        )
    )
    assert result.get("is_error") is True
