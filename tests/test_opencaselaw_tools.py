"""Tests for opencaselaw MCP wrapper tools."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from agents.tools.opencaselaw import create_opencaselaw_tools


@pytest.fixture
def tools():
    return create_opencaselaw_tools("https://mcp.test.example")


def _patch_mcp(return_text: str):
    """Patch mcp_call to return a given text."""
    return patch("agents.tools.opencaselaw.mcp_call", AsyncMock(return_value=return_text))


def test_search_decisions(tools):
    with _patch_mcp("1. BGE 130 III 182\n2. BGE 133 III 323"):
        result = asyncio.run(
            tools["search_decisions"]({"query": "Art. 41 OR Haftung", "law_abbreviation": "OR"})
        )
        assert "BGE 130 III 182" in result["content"][0]["text"]


def test_find_leading_cases(tools):
    with _patch_mcp("Leading: BGE 130 III 182"):
        result = asyncio.run(
            tools["find_leading_cases"]({"article": "41", "law_abbreviation": "OR"})
        )
        assert "Leading" in result["content"][0]["text"]


def test_get_decision(tools):
    with _patch_mcp("BGE 130 III 182: Haftung..."):
        result = asyncio.run(tools["get_decision"]({"decision_id": "130-III-182"}))
        assert "Haftung" in result["content"][0]["text"]


def test_get_case_brief(tools):
    with _patch_mcp("Brief: Haftungsrecht..."):
        result = asyncio.run(tools["get_case_brief"]({"case": "BGE 130 III 182"}))
        assert "Brief" in result["content"][0]["text"]


def test_get_doctrine(tools):
    with _patch_mcp('{"leading_cases": [], "statute": {}}'):
        result = asyncio.run(tools["get_doctrine"]({"query": "Art. 41 OR"}))
        assert "leading_cases" in result["content"][0]["text"]


def test_get_commentary(tools):
    with _patch_mcp("Commentary text for Art. 1"):
        result = asyncio.run(
            tools["get_commentary"]({"abbreviation": "VwVG", "article": "1"})
        )
        assert "Commentary" in result["content"][0]["text"]


def test_mcp_error_handling(tools):
    with patch(
        "agents.tools.opencaselaw.mcp_call",
        AsyncMock(side_effect=RuntimeError("MCP error")),
    ):
        result = asyncio.run(
            tools["search_decisions"]({"query": "test"})
        )
        assert result.get("is_error") is True
