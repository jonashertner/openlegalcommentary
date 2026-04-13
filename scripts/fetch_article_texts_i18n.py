"""Fetch article texts in FR, IT, and EN from opencaselaw MCP.

Reads article_lists.json for the article inventory, then calls the
get_law MCP tool per article per language. Saves to article_texts_{lang}.json
with the same structure as article_texts.json.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from pathlib import Path

from agents.mcp_client import mcp_call

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

MCP_BASE = "https://mcp.opencaselaw.ch"
SCRIPTS_DIR = Path("scripts")
MAX_CONCURRENT = 2
MAX_RETRIES = 5


def _parse_article_text(raw: str) -> list[dict]:
    """Parse MCP get_law response into paragraph structure."""
    paragraphs = []
    # Skip header lines (law title, consolidation date, article heading)
    lines = raw.strip().split("\n")
    body_started = False
    body_lines = []
    for line in lines:
        # Match article headers including suffix articles: ### Art. 5a, ### Art. 10a
        if re.match(r"^###\s+Art\.", line):
            body_started = True
            continue
        if body_started:
            body_lines.append(line)

    text = "\n".join(body_lines).strip()
    if not text:
        return paragraphs

    # Split by paragraph markers (superscript numbers at start)
    # Pattern: lines starting with a number followed by content
    parts = re.split(r'\n(?=\d+\s)', text)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        num_match = re.match(r'^(\d+)\s+(.*)', part, re.DOTALL)
        if num_match:
            paragraphs.append({
                "num": num_match.group(1),
                "text": num_match.group(2).strip(),
            })
        else:
            paragraphs.append({"text": part})

    return paragraphs


async def fetch_article(
    sem: asyncio.Semaphore,
    law: str, article: str, language: str,
) -> tuple[str, str, list[dict]]:
    """Fetch one article text, return (law, article_key, paragraphs)."""
    async with sem:
        for attempt in range(MAX_RETRIES):
            try:
                raw = await mcp_call(MCP_BASE, "get_law", {
                    "abbreviation": law,
                    "article": article,
                    "language": language,
                }, timeout=30.0)
                paragraphs = _parse_article_text(raw)
                return (law, article, paragraphs)
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(2 + attempt * 3)
                    continue
                logger.warning("Failed %s Art. %s (%s): %s", law, article, language, e)
                return (law, article, [])


async def fetch_all(language: str) -> dict:
    """Fetch all article texts for a language."""
    lists_path = SCRIPTS_DIR / "article_lists.json"
    article_lists = json.loads(lists_path.read_text())

    sem = asyncio.Semaphore(MAX_CONCURRENT)
    tasks = []

    for law, data in article_lists.items():
        for entry in data["articles"]:
            key = f"{entry['number']}{entry.get('suffix', '')}"
            tasks.append(fetch_article(sem, law, key, language))

    logger.info("Fetching %d articles in %s...", len(tasks), language)
    results = await asyncio.gather(*tasks)

    texts: dict[str, dict[str, list]] = {}
    fetched = 0
    for law, key, paragraphs in results:
        if law not in texts:
            texts[law] = {}
        texts[law][key] = paragraphs
        if paragraphs:
            fetched += 1

    logger.info("Fetched %d/%d articles with content in %s", fetched, len(tasks), language)
    return texts


async def main():
    for lang in ("fr", "it", "en"):
        texts = await fetch_all(lang)
        out_path = SCRIPTS_DIR / f"article_texts_{lang}.json"
        out_path.write_text(json.dumps(texts, ensure_ascii=False, indent=None))
        logger.info("Saved %s (%.1f MB)", out_path, out_path.stat().st_size / 1e6)


if __name__ == "__main__":
    asyncio.run(main())
