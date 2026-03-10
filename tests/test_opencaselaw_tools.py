"""Tests for opencaselaw MCP wrapper tools."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from agents.tools.opencaselaw import create_opencaselaw_tools


def _mock_mcp_response(text: str) -> dict:
    return {
        "result": {
            "content": [{"type": "text", "text": text}]
        }
    }


@pytest.fixture
def tools():
    return create_opencaselaw_tools("https://mcp.test.example")


def test_get_article_text(tools):
    mock_resp = AsyncMock()
    mock_resp.json.return_value = _mock_mcp_response("Art. 41\n1 Wer einem andern...")
    mock_resp.raise_for_status = lambda: None

    with patch("agents.mcp_client.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.post = AsyncMock(return_value=mock_resp)

        result = asyncio.run(tools["get_article_text"]({"law_abbreviation": "OR"}))
        assert "Art. 41" in result["content"][0]["text"]


def test_search_decisions(tools):
    mock_resp = AsyncMock()
    mock_resp.json.return_value = _mock_mcp_response("1. BGE 130 III 182\n2. BGE 133 III 323")
    mock_resp.raise_for_status = lambda: None

    with patch("agents.mcp_client.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.post = AsyncMock(return_value=mock_resp)

        result = asyncio.run(
            tools["search_decisions"]({"query": "Art. 41 OR Haftung", "law_abbreviation": "OR"})
        )
        assert "BGE 130 III 182" in result["content"][0]["text"]


def test_find_leading_cases(tools):
    mock_resp = AsyncMock()
    mock_resp.json.return_value = _mock_mcp_response("Leading: BGE 130 III 182")
    mock_resp.raise_for_status = lambda: None

    with patch("agents.mcp_client.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.post = AsyncMock(return_value=mock_resp)

        result = asyncio.run(
            tools["find_leading_cases"]({"article": "Art. 41", "law_abbreviation": "OR"})
        )
        assert "Leading" in result["content"][0]["text"]


def test_get_decision(tools):
    mock_resp = AsyncMock()
    mock_resp.json.return_value = _mock_mcp_response("BGE 130 III 182: Haftung...")
    mock_resp.raise_for_status = lambda: None

    with patch("agents.mcp_client.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.post = AsyncMock(return_value=mock_resp)

        result = asyncio.run(tools["get_decision"]({"decision_id": "130-III-182"}))
        assert "Haftung" in result["content"][0]["text"]


def test_get_case_brief(tools):
    mock_resp = AsyncMock()
    mock_resp.json.return_value = _mock_mcp_response("Brief: Haftungsrecht...")
    mock_resp.raise_for_status = lambda: None

    with patch("agents.mcp_client.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.post = AsyncMock(return_value=mock_resp)

        result = asyncio.run(tools["get_case_brief"]({"decision_id": "130-III-182"}))
        assert "Brief" in result["content"][0]["text"]


def test_mcp_error_handling(tools):
    mock_resp = AsyncMock()
    mock_resp.json.return_value = {"error": {"code": -1, "message": "Tool not found"}}
    mock_resp.raise_for_status = lambda: None

    with patch("agents.mcp_client.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.post = AsyncMock(return_value=mock_resp)

        result = asyncio.run(tools["get_article_text"]({"law_abbreviation": "OR"}))
        assert result.get("is_error") is True


def test_create_opencaselaw_server():
    from agents.tools.opencaselaw import create_opencaselaw_server
    server = create_opencaselaw_server("https://mcp.test.example")
    assert server is not None
