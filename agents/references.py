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


# --- Commentary references (Doctrinal Sources) ---

_commentary_refs_cache: dict[tuple, dict] = {}


def load_commentary_refs(refs_root: Path, law: str) -> dict:
    """Load and merge Primary + CR commentary references for a law.

    Returns a dict keyed by article number string. When both Primary and CR
    exist for the same article, the value is {"primary": {...}, "cr": {...}}.
    When only one source exists, it's {"primary": {...}} or {"cr": {...}}.
    Returns empty dict if no files exist.
    """
    cache_key = (str(refs_root), law)
    if cache_key in _commentary_refs_cache:
        return _commentary_refs_cache[cache_key]

    merged: dict = {}
    for source in ("primary", "cr"):
        path = refs_root / f"{law.lower()}_{source}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        articles = data.get(law.upper(), {})
        for art_key, art_data in articles.items():
            if art_key not in merged:
                merged[art_key] = {}
            merged[art_key][source] = art_data

    _commentary_refs_cache[cache_key] = merged
    return merged


def _format_single_source(source_label: str, data: dict) -> str:
    """Format a single Primary or CR source block."""
    lines = []
    lines.append(f"### {source_label}")
    lines.append(f"Authors: {', '.join(data.get('authors', []))}")
    lines.append(f"Edition: {data.get('edition', '')}")

    rz_map = data.get("randziffern_map", {})
    if rz_map:
        lines.append("")
        lines.append("Randziffern overview:")
        for rz_range, topic in rz_map.items():
            lines.append(f"- N. {rz_range}: {topic}")

    positions = data.get("positions", [])
    if positions:
        lines.append("")
        lines.append("Key positions:")
        for p in positions:
            lines.append(f"- {p['author']}, {p['n']}: {p['position']}")

    controversies = data.get("controversies", [])
    if controversies:
        lines.append("")
        lines.append("Doctrinal controversies:")
        for c in controversies:
            parts = [
                f"{author}: {pos}"
                for author, pos in c["positions"].items()
            ]
            lines.append(f"- {c['topic']}: {'; '.join(parts)}")

    cross_refs = data.get("cross_refs", [])
    if cross_refs:
        lines.append("")
        lines.append(f"Cross-references: {', '.join(cross_refs)}")

    key_lit = data.get("key_literature", [])
    if key_lit:
        lines.append("")
        lines.append("Key literature:")
        for lit in key_lit:
            lines.append(f"- {lit}")

    return "\n".join(lines)


def format_commentary_refs(
    refs_root: Path, law: str, article_number: int, suffix: str,
) -> str:
    """Format commentary references for prompt injection.

    Returns empty string if no data available.
    """
    refs = load_commentary_refs(refs_root, law)
    key = f"{article_number}{suffix}"
    article_refs = refs.get(key)
    if not article_refs:
        return ""

    blocks = []
    blocks.append("## Doctrinal Reference Data (Doctrinal Sources)")
    blocks.append("")

    for source in ("primary", "cr"):
        if source in article_refs:
            label = "Primary" if source == "primary" else "CR"
            blocks.append(_format_single_source(label, article_refs[source]))
            blocks.append("")

    blocks.append(
        "Use these references to ground your doctrinal analysis. "
        "Cite authors with proper Primary/CR Randziffern."
    )
    blocks.append(
        "Do NOT reproduce commentary text — synthesize original "
        "analysis that cites specific positions."
    )

    return "\n".join(blocks)
