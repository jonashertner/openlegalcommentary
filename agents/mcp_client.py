"""Shared MCP HTTP client for calling the opencaselaw MCP server.

Used by both scripts/fetch_articles.py and agents/tools/opencaselaw.py
to avoid duplication of the JSON-RPC HTTP transport layer.

The server uses Streamable HTTP transport: POST to root with SSE response format.
"""
from __future__ import annotations

import json

import httpx


async def mcp_call(
    mcp_base: str, tool_name: str, args: dict, timeout: float = 120.0,
) -> str:
    """Call an opencaselaw MCP tool via Streamable HTTP (SSE)."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            f"{mcp_base}/",
            json={
                "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"name": tool_name, "arguments": args},
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
        )
        response.raise_for_status()

        # Parse SSE response: extract JSON from "data:" lines
        result = _parse_sse_response(response.text)
        if "error" in result:
            raise RuntimeError(f"MCP error: {result['error']}")
        content = result.get("result", {}).get("content", [])
        return "\n".join(c["text"] for c in content if c.get("type") == "text")


def _parse_sse_response(text: str) -> dict:
    """Parse an SSE response, extracting the JSON-RPC result from data lines."""
    for line in text.splitlines():
        if line.startswith("data: "):
            return json.loads(line[6:])
    raise RuntimeError(f"No data line in SSE response: {text[:200]}")
