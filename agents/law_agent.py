"""Law agent — generates commentary layers for individual articles.

Each call runs a Claude agent with:
- System prompt built from global + per-law guidelines
- Content tools for reading/writing article files
- opencaselaw tools for searching court decisions and case law
- Article text injected directly from article_texts.json
"""
from __future__ import annotations

from agents.anthropic_client import run_agent
from agents.config import AgentConfig
from agents.prompts import build_law_agent_prompt
from agents.references import format_article_text, format_commentary_refs
from agents.tools.content import create_content_tools
from agents.tools.opencaselaw import create_opencaselaw_tools


async def generate_layer(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_type: str,
    feedback: str | None = None,
) -> float:
    """Run the law agent to generate a commentary layer.

    Args:
        config: Pipeline configuration.
        law: Law abbreviation (e.g., "OR").
        article_number: Article number (e.g., 41).
        article_suffix: Article suffix (e.g., "a" for Art. 6a).
        layer_type: One of "summary", "doctrine", "caselaw".
        feedback: Optional feedback from a previous failed evaluation.

    Returns:
        Cost in USD for this generation.
    """
    system_prompt = build_law_agent_prompt(
        config.guidelines_root, law, layer_type,
    )

    content_tools = create_content_tools(config.content_root)
    opencaselaw_tools = create_opencaselaw_tools(config.mcp_base_url)

    suffix_str = article_suffix or ""
    art_dir = f"{law.lower()}/art-{str(article_number).zfill(3)}{suffix_str}/"

    # Inject article text directly so the agent doesn't need get_article_text MCP
    article_text = format_article_text(law, article_number, suffix_str)
    article_text_block = ""
    if article_text:
        article_text_block = (
            f"\n\nHere is the official Gesetzestext of "
            f"Art. {article_number}{suffix_str} {law}:\n\n{article_text}\n"
        )

    # Inject commentary references for doctrine and summary layers
    commentary_refs_block = ""
    if layer_type in ("doctrine", "summary"):
        commentary_refs_block = format_commentary_refs(
            config.commentary_refs_root, law, article_number, suffix_str,
        )

    prompt = (
        f"Generate the {layer_type} layer for "
        f"Art. {article_number}{suffix_str} {law}. "
        f"The article directory is at {art_dir}. "
        f"{article_text_block}"
        f"Use the tools to research case law and write the layer content."
    )
    if commentary_refs_block:
        prompt += f"\n\n{commentary_refs_block}"
    if feedback:
        prompt += (
            "\n\nYour previous attempt was rejected by the evaluator. "
            f"Fix the following issues:\n{feedback}"
        )

    _, cost = await run_agent(
        system_prompt=system_prompt,
        prompt=prompt,
        model=config.model_for_layer(layer_type),
        content_tools=content_tools,
        opencaselaw_tools=opencaselaw_tools,
        allowed_tools=[
            "read_article_meta",
            "read_layer_content",
            "write_layer_content",
            "search_decisions",
            "find_leading_cases",
            "get_decision",
            "get_case_brief",
            "get_doctrine",
            "get_commentary",
        ],
        max_turns=config.max_turns_per_agent,
    )

    return cost
