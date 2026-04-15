"""Coordinator — finds new decisions and maps them to articles.

The coordinator is pure Python orchestration (no LLM). It:
1. Queries opencaselaw for decisions since a given date
2. Parses the results to extract cited articles
3. Groups affected articles by law for parallel processing
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from scripts.schema import LAWS


@dataclass
class ArticleRef:
    """An article affected by one or more new decisions."""

    law: str
    article_number: int
    article_suffix: str = ""
    decision_refs: list[str] = field(default_factory=list)


def parse_decision_list(text: str) -> list[dict]:
    """Parse opencaselaw search_decisions output into structured dicts.

    Handles the current format with entries like:
        **1. 5A_144/2026** (2026-04-01) [bger] [de]
           ID: bger_5A_144_2026
           Title: ...
           ...snippet text...

    Each decision has: reference, articles (list of {law, article}).
    Articles are extracted from the snippet text when they match the
    form "Art. N LAW" where LAW is in our LAWS list.
    """
    decisions = []
    current = None

    # Entry headers — handle both formats:
    #   Current: **N. 5A_144/2026** or **N. BGE 150 III 182**
    #   Legacy: N. **BGE 130 III 182** or N. **5A_144/2026**
    entry_header = re.compile(
        r"^(?:\*\*\d+\.\s+|\d+\.\s+\*\*)"
        r"([A-Z0-9_]+[_/][A-Z0-9_/]+|BGE\s+\d+\s+\w+\s+\d+)"
        r"\*\*"
    )
    # Legacy BGE inline match (for older response formats)
    bge_inline = re.compile(r"\b(BGE\s+\d+\s+[IVX]+\s+\d+)\b")
    # Article reference patterns — match both orderings:
    #   "Art. 41 OR" (statute-first-last)
    #   "OR Art. 41" (statute-first-last reversed, older format)
    art_then_law = re.compile(
        r"\bArt\.?\s*(\d+)([a-z]*)\s+(?:Abs\.?\s*\d+\s+)?"
        r"([A-Z][A-Za-z]{1,6})\b",
    )
    law_then_art = re.compile(
        r"\b([A-Z][A-Za-z]{1,6})\s+Art\.?\s*(\d+)([a-z]*)\b",
    )
    law_map = {la.upper(): la for la in LAWS}

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Entry header: start a new decision
        header_match = entry_header.match(line)
        if header_match:
            if current:
                decisions.append(current)
            current = {
                "reference": header_match.group(1),
                "articles": [],
            }
            continue

        # Legacy BGE reference in body
        bge_match = bge_inline.search(line)
        if bge_match and not current:
            current = {
                "reference": bge_match.group(1),
                "articles": [],
            }

        # Extract article references from any content line
        if current:
            for art_match in art_then_law.finditer(line):
                law_candidate = art_match.group(3).upper()
                law = law_map.get(law_candidate)
                if law:
                    current["articles"].append({
                        "law": law,
                        "article": int(art_match.group(1)),
                        "suffix": art_match.group(2),
                    })
            for art_match in law_then_art.finditer(line):
                law_candidate = art_match.group(1).upper()
                law = law_map.get(law_candidate)
                if law:
                    current["articles"].append({
                        "law": law,
                        "article": int(art_match.group(2)),
                        "suffix": art_match.group(3),
                    })

    if current:
        decisions.append(current)

    return decisions


def map_decisions_to_articles(
    decisions: list[dict],
) -> list[ArticleRef]:
    """Group decisions by article."""
    article_map: dict[str, ArticleRef] = {}

    for decision in decisions:
        ref = decision["reference"]
        for art in decision.get("articles", []):
            key = (
                f"{art['law']}:{art['article']}"
                f":{art.get('suffix', '')}"
            )
            if key not in article_map:
                article_map[key] = ArticleRef(
                    law=art["law"],
                    article_number=art["article"],
                    article_suffix=art.get("suffix", ""),
                )
            article_map[key].decision_refs.append(ref)

    return sorted(
        article_map.values(),
        key=lambda r: (r.law, r.article_number),
    )


async def find_new_decisions(
    mcp_base: str, since_date: str,
) -> list[dict]:
    """Query opencaselaw for new BGE/BGer decisions since given date.

    Federal commentary only updates for federal court decisions
    (BGE/BGer). Cantonal decisions rarely create new leading cases
    for federal law, so we filter to federal courts. Queries each
    court separately because the tool doesn't support OR filters.

    Uses empty query + sort=date_desc as required by search_decisions
    for "most recent" queries. The previous natural-language query
    ("Neue Entscheide seit ...") returned 0 results because real
    decisions don't contain that phrase.
    """
    import logging

    from agents.mcp_client import mcp_call

    logger = logging.getLogger(__name__)
    all_decisions: list[dict] = []

    for court in ("bge", "bger"):
        text = await mcp_call(
            mcp_base, "search_decisions",
            {
                "query": "",
                "date_from": since_date,
                "sort": "date_desc",
                "court": court,
                "limit": 200,
            },
        )
        parsed = parse_decision_list(text)
        logger.info(
            "find_new_decisions(%s): raw_chars=%d parsed=%d",
            court, len(text), len(parsed),
        )
        all_decisions.extend(parsed)

    logger.info(
        "find_new_decisions total since %s: %d decisions",
        since_date, len(all_decisions),
    )
    return all_decisions


def group_by_law(
    articles: list[ArticleRef],
) -> dict[str, list[ArticleRef]]:
    """Group article references by law for parallel processing."""
    groups: dict[str, list[ArticleRef]] = {}
    for art in articles:
        groups.setdefault(art.law, []).append(art)
    return groups
