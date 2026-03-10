"""Shared MCP HTTP client for calling the opencaselaw MCP server.

Used by both scripts/fetch_articles.py and agents/tools/opencaselaw.py
to avoid duplication of the JSON-RPC HTTP transport layer.
"""
from __future__ import annotations

import httpx


async def mcp_call(
    mcp_base: str, tool_name: str, args: dict, timeout: float = 120.0,
) -> str:
    """Call an opencaselaw MCP tool via JSON-RPC over HTTP."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            f"{mcp_base}/mcp",
            json={
                "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"name": tool_name, "arguments": args},
            },
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        result = await response.json()
        if "error" in result:
            raise RuntimeError(f"MCP error: {result['error']}")
        content = result.get("result", {}).get("content", [])
        return "\n".join(c["text"] for c in content if c.get("type") == "text")
