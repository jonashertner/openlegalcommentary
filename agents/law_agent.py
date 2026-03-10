"""Law agent — generates commentary layers for individual articles.

Each call runs a Claude agent with:
- System prompt built from global + per-law guidelines
- Content tools for reading/writing article files
- opencaselaw tools for fetching article text and case law
"""
from __future__ import annotations

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from agents.config import AgentConfig
from agents.prompts import build_law_agent_prompt
from agents.tools.content import create_content_server
from agents.tools.opencaselaw import create_opencaselaw_server


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

    content_server = create_content_server(config.content_root)
    opencaselaw_server = create_opencaselaw_server(config.mcp_base_url)

    suffix_str = article_suffix or ""
    art_dir = f"{law.lower()}/art-{str(article_number).zfill(3)}{suffix_str}/"
    prompt = (
        f"Generate the {layer_type} layer for "
        f"Art. {article_number}{suffix_str} {law}. "
        f"The article directory is at {art_dir}. "
        f"Use the tools to research the article, "
        f"then write the layer content."
    )
    if feedback:
        prompt += (
            "\n\nYour previous attempt was rejected by the evaluator. "
            f"Fix the following issues:\n{feedback}"
        )

    options = ClaudeAgentOptions(
        mcp_servers={
            "content": content_server,
            "opencaselaw": opencaselaw_server,
        },
        allowed_tools=[
            "mcp__content__read_article_meta",
            "mcp__content__read_layer_content",
            "mcp__content__write_layer_content",
            "mcp__opencaselaw__get_article_text",
            "mcp__opencaselaw__search_decisions",
            "mcp__opencaselaw__find_leading_cases",
            "mcp__opencaselaw__get_decision",
            "mcp__opencaselaw__get_case_brief",
        ],
        system_prompt=system_prompt,
        model=config.model_for_layer(layer_type),
        max_turns=config.max_turns_per_agent,
        max_budget_usd=config.max_budget_per_layer,
        permission_mode="bypassPermissions",
    )

    cost = 0.0
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage) and message.total_cost_usd:
            cost = message.total_cost_usd

    return cost
