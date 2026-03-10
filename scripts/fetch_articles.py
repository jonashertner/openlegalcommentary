"""Fetch article lists and legislation metadata via opencaselaw MCP server."""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import httpx

from scripts.schema import LAWS, SR_NUMBERS

MCP_BASE = "https://mcp.opencaselaw.ch"


def article_dir_name(number: int, suffix: str = "") -> str:
    padded = str(number).zfill(3)
    return f"art-{padded}{suffix}"


def parse_article_list_response(text: str) -> list[dict]:
    articles: list[dict] = []
    seen: set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("- Art."):
            continue
        if re.match(r"^- Art\.\s+\d+\s*(?:–|—|-)\s*\d+", line):
            continue
        match = re.match(r"^- Art\.\s+(\d+)\s*([a-z]*)", line)
        if not match:
            continue
        number = int(match.group(1))
        suffix = match.group(2).strip()
        raw = f"{number}{suffix}"
        if raw in seen:
            continue
        seen.add(raw)
        articles.append({"number": number, "suffix": suffix, "raw": raw})
    articles.sort(key=lambda a: (a["number"], a["suffix"]))
    return articles


async def _mcp_call(client: httpx.AsyncClient, tool: str, args: dict) -> str:
    response = await client.post(
        f"{MCP_BASE}/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
              "params": {"name": tool, "arguments": args}},
        headers={"Content-Type": "application/json"},
    )
    response.raise_for_status()
    result = response.json()
    if "error" in result:
        raise RuntimeError(f"MCP error: {result['error']}")
    content = result.get("result", {}).get("content", [])
    return "\n".join(c["text"] for c in content if c.get("type") == "text")


async def fetch_articles(law: str) -> list[dict]:
    if law not in LAWS:
        raise ValueError(f"Unknown law: {law}")
    async with httpx.AsyncClient(timeout=120.0) as client:
        text = await _mcp_call(client, "get_law", {"abbreviation": law})
        return parse_article_list_response(text)


async def fetch_legislation_metadata(law: str) -> dict:
    sr = SR_NUMBERS[law]
    async with httpx.AsyncClient(timeout=60.0) as client:
        text = await _mcp_call(client, "get_legislation", {"systematic_number": sr})
    meta: dict = {"sr_number": sr, "law": law}
    for line in text.splitlines():
        if line.startswith("**LexFind ID:**"):
            try:
                meta["lexfind_id"] = int(line.split(":")[-1].strip())
            except ValueError:
                pass
        elif line.startswith("**In force since:**"):
            meta["in_force_since"] = line.split(":**")[-1].strip() if ":**" in line else ""
        elif line.startswith("- [DE]"):
            meta["fedlex_url"] = line.split("]")[-1].strip()
        elif line.startswith("- [DE PDF]"):
            meta["lexfind_url"] = line.split("]")[-1].strip()
    return meta


async def fetch_all_laws() -> dict[str, list[dict]]:
    results: dict[str, list[dict]] = {}
    for law in LAWS:
        print(f"Fetching {law}...")
        results[law] = await fetch_articles(law)
        print(f"  -> {len(results[law])} articles")
    return results


if __name__ == "__main__":
    results = asyncio.run(fetch_all_laws())
    output = {}
    for law, articles in results.items():
        output[law] = {
            "sr_number": SR_NUMBERS[law],
            "article_count": len(articles),
            "articles": articles,
        }
    out_path = Path("scripts/article_lists.json")
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nSaved to {out_path}")
    print(f"Total: {sum(len(a) for a in results.values())} articles across {len(results)} laws")
