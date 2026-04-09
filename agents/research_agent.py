"""Research agent — collects structured research briefs before generation.

The research agent runs BEFORE the law agent. It gathers all available
information for an article into a structured brief, which is then injected
into the generation prompt for higher-quality output.

Research brief includes:
- Statute text
- Legislative history (from preparatory materials)
- Leading cases with holdings (from opencaselaw)
- Doctrinal positions (from BSK/CR reference data)
- Article significance tier
- Cross-references to related provisions

The brief is stored at content/{law}/art-{n}/.research.json
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from agents.config import AgentConfig
from agents.references import (
    format_article_text,
    load_commentary_refs,
    load_preparatory_materials,
)

logger = logging.getLogger(__name__)


async def build_research_brief(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    use_opencaselaw: bool = True,
) -> dict:
    """Build a structured research brief for an article.

    Args:
        config: Pipeline configuration.
        law: Law abbreviation (e.g., "OR").
        article_number: Article number.
        article_suffix: Article suffix (e.g., "a").
        use_opencaselaw: Whether to query opencaselaw for case law.

    Returns:
        Structured research brief dict.
    """
    suffix_str = article_suffix or ""
    article_key = f"{article_number}{suffix_str}"

    brief: dict = {
        "law": law,
        "article": article_number,
        "article_suffix": suffix_str,
        "statute_text": "",
        "legislative_history": {},
        "leading_cases": [],
        "doctrinal_positions": [],
        "significance_tier": "tier_3",
        "cross_references": [],
    }

    # 1. Statute text
    article_text = format_article_text(law, article_number, suffix_str)
    brief["statute_text"] = article_text

    # 2. Legislative history from preparatory materials
    prep_materials = load_preparatory_materials(law)
    article_prep = prep_materials.get(article_key, {})
    if article_prep:
        sources = article_prep.get("sources", [])
        if sources:
            first_source = sources[0]
            brief["legislative_history"] = {
                "bbl_ref": first_source.get("bbl_ref", ""),
                "intent": first_source.get("legislative_intent", ""),
                "key_arguments": first_source.get("key_arguments", []),
                "design_choices": first_source.get("design_choices", []),
                "bbl_pages": first_source.get("bbl_page_refs", []),
            }
        mods = article_prep.get("parliamentary_modifications", [])
        if mods:
            brief["legislative_history"]["parliamentary_modifications"] = mods

    # 3. Doctrinal positions from commentary refs
    refs = load_commentary_refs(config.commentary_refs_root, law)
    article_refs = refs.get(article_key, {})
    positions = []
    for source_key in ("primary", "cr"):
        source_data = article_refs.get(source_key, {})
        for pos in source_data.get("positions", []):
            positions.append({
                "source": "BSK" if source_key == "primary" else "CR",
                "author": pos.get("author", ""),
                "randziffer": pos.get("n", ""),
                "position": pos.get("position", ""),
            })
        for controversy in source_data.get("controversies", []):
            for author, stance in controversy.get("positions", {}).items():
                positions.append({
                    "source": "BSK" if source_key == "primary" else "CR",
                    "author": author,
                    "topic": controversy.get("topic", ""),
                    "position": stance,
                })
    brief["doctrinal_positions"] = positions

    # 4. Leading cases via opencaselaw (if available)
    if use_opencaselaw:
        try:
            from agents.mcp_client import mcp_call
            leading_text = await mcp_call(
                config.mcp_base_url,
                "find_leading_cases",
                {
                    "article": str(article_number),
                    "law_code": law,
                },
            )
            brief["leading_cases_raw"] = leading_text[:5000]
        except Exception as e:
            logger.warning(
                "Could not fetch leading cases for Art. %d%s %s: %s",
                article_number, suffix_str, law, e,
            )

    # 5. Significance tier
    try:
        from scripts.classify_articles import classify_article
        brief["significance_tier"] = classify_article(
            law, article_number,
        )
    except Exception:
        pass

    return brief


def save_research_brief(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    brief: dict,
) -> Path:
    """Save a research brief to the article directory."""
    from scripts.fetch_articles import article_dir_name

    suffix_str = article_suffix or ""
    dir_name = article_dir_name(article_number, suffix_str)
    art_dir = config.content_root / law.lower() / dir_name
    art_dir.mkdir(parents=True, exist_ok=True)

    brief_path = art_dir / ".research.json"
    brief_path.write_text(
        json.dumps(brief, indent=2, ensure_ascii=False),
    )

    logger.info(
        "Saved research brief for Art. %d%s %s at %s",
        article_number, suffix_str, law, brief_path,
    )
    return brief_path


def load_research_brief(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
) -> dict | None:
    """Load an existing research brief, if available."""
    from scripts.fetch_articles import article_dir_name

    suffix_str = article_suffix or ""
    dir_name = article_dir_name(article_number, suffix_str)
    brief_path = (
        config.content_root / law.lower() / dir_name / ".research.json"
    )

    if not brief_path.exists():
        return None

    return json.loads(brief_path.read_text())


def format_research_brief_for_prompt(brief: dict) -> str:
    """Format a research brief for injection into a generation prompt."""
    parts = []

    parts.append("## Research Brief")
    parts.append(f"Article: Art. {brief['article']}"
                 f"{brief.get('article_suffix', '')} {brief['law']}")
    parts.append(f"Significance: {brief.get('significance_tier', 'tier_3')}")

    if brief.get("statute_text"):
        parts.append(f"\n### Statute Text\n{brief['statute_text']}")

    lh = brief.get("legislative_history", {})
    if lh.get("intent"):
        parts.append("\n### Legislative History")
        if lh.get("bbl_ref"):
            parts.append(f"Botschaft: {lh['bbl_ref']}")
        parts.append(f"Intent: {lh['intent']}")
        for arg in lh.get("key_arguments", []):
            parts.append(f"- {arg}")

    positions = brief.get("doctrinal_positions", [])
    if positions:
        parts.append(f"\n### Doctrinal Positions ({len(positions)})")
        for p in positions[:20]:
            source = p.get("source", "")
            author = p.get("author", "")
            pos_text = p.get("position", "")
            parts.append(f"- {author} ({source}): {pos_text}")

    if brief.get("leading_cases_raw"):
        parts.append("\n### Leading Cases (from opencaselaw)")
        parts.append(brief["leading_cases_raw"][:3000])

    return "\n".join(parts)
