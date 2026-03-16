"""Shared reference loading and formatting for the agent pipeline.

Consolidates article text and commentary reference loading, used by both
the law agent and evaluator.
"""
from __future__ import annotations

import json
from pathlib import Path

ARTICLE_TEXTS_PATH = Path("scripts/article_texts.json")

_article_texts_cache: dict | None = None


def load_article_texts() -> dict:
    """Load article texts from JSON, with module-level caching."""
    global _article_texts_cache
    if _article_texts_cache is not None:
        return _article_texts_cache
    if ARTICLE_TEXTS_PATH.exists():
        _article_texts_cache = json.loads(ARTICLE_TEXTS_PATH.read_text())
        return _article_texts_cache
    _article_texts_cache = {}
    return _article_texts_cache


def format_article_text(law: str, article_number: int, suffix: str) -> str:
    """Format article text from article_texts.json for prompt injection."""
    texts = load_article_texts()
    key = f"{article_number}{suffix}"
    paragraphs = texts.get(law.upper(), {}).get(key, [])
    if not paragraphs:
        return ""
    lines = []
    for p in paragraphs:
        if p.get("type") == "list":
            for item in p.get("items", []):
                lines.append(f"  {item['letter']}. {item['text']}")
        elif p.get("num"):
            lines.append(f"  {p['num']} {p.get('text', '')}")
        else:
            lines.append(p.get("text", ""))
    return "\n".join(lines)
