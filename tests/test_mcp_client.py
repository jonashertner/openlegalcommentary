"""Tests for the shared MCP HTTP client."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.mcp_client import mcp_call


def _mock_response(text: str):
    resp = MagicMock()
    resp.json.return_value = {
        "result": {"content": [{"type": "text", "text": text}]}
    }
    resp.raise_for_status = MagicMock()
    return resp


def test_mcp_call_returns_text():
    with patch("agents.mcp_client.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_client.return_value
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.post = AsyncMock(
            return_value=_mock_response("Art. 41 OR text")
        )

        result = asyncio.run(
            mcp_call("https://mcp.test", "get_law", {"abbreviation": "OR"})
        )
        assert "Art. 41" in result


def test_mcp_call_raises_on_error():
    resp = MagicMock()
    resp.json.return_value = {"error": {"code": -1, "message": "Not found"}}
    resp.raise_for_status = MagicMock()

    with patch("agents.mcp_client.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_client.return_value
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.post = AsyncMock(return_value=resp)

        with pytest.raises(RuntimeError, match="MCP error"):
            asyncio.run(
                mcp_call("https://mcp.test", "get_law", {"abbreviation": "OR"})
            )
