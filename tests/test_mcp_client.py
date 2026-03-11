"""Tests for the shared MCP HTTP client."""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.mcp_client import mcp_call


def _mock_sse_response(result: dict):
    """Create a mock httpx response with SSE format."""
    resp = MagicMock()
    data = json.dumps({"jsonrpc": "2.0", "id": 1, "result": result})
    resp.text = f"event: message\ndata: {data}\n\n"
    resp.raise_for_status = MagicMock()
    return resp


def test_mcp_call_returns_text():
    mock_resp = _mock_sse_response({
        "content": [{"type": "text", "text": "Art. 41 OR text"}]
    })

    with patch("agents.mcp_client.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_client.return_value
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.post = AsyncMock(return_value=mock_resp)

        result = asyncio.run(
            mcp_call("https://mcp.test", "get_law", {"abbreviation": "OR"})
        )
        assert "Art. 41" in result


def test_mcp_call_raises_on_error():
    data = json.dumps({
        "jsonrpc": "2.0", "id": 1,
        "error": {"code": -1, "message": "Not found"},
    })
    resp = MagicMock()
    resp.text = f"event: message\ndata: {data}\n\n"
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
