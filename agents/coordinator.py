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

    Each decision has: reference, articles (list of {law, article}).
    """
    decisions = []
    current = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        ref_match = re.search(
            r"\*\*?(BGE\s+\d+\s+\w+\s+\d+)\*\*?", line,
        )
        if ref_match:
            if current:
                decisions.append(current)
            current = {
                "reference": ref_match.group(1),
                "articles": [],
            }
            continue

        urteil_match = re.search(
            r"(Urteil\s+\w+_\d+/\d+)", line,
        )
        if urteil_match and not current:
            current = {
                "reference": urteil_match.group(1),
                "articles": [],
            }
            continue

        if current and ("Art." in line or "art." in line):
            for art_match in re.finditer(
                r"(\w+)\s+Art\.?\s*(\d+)([a-z]*)",
                line, re.IGNORECASE,
            ):
                law_candidate = art_match.group(1).upper()
                law_map = {la.upper(): la for la in LAWS}
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
    """Query opencaselaw for decisions since the given date."""
    from agents.mcp_client import mcp_call

    text = await mcp_call(
        mcp_base, "search_decisions",
        {
            "query": f"Neue Entscheide seit {since_date}",
            "date_from": since_date,
        },
    )
    return parse_decision_list(text)


def group_by_law(
    articles: list[ArticleRef],
) -> dict[str, list[ArticleRef]]:
    """Group article references by law for parallel processing."""
    groups: dict[str, list[ArticleRef]] = {}
    for art in articles:
        groups.setdefault(art.law, []).append(art)
    return groups
