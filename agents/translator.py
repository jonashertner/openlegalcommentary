"""Translator agent — translates commentary layers from German to French/Italian.

Uses the translation guidelines from global.md §III and official Fedlex termdat
terminology for legal terms.
"""
from __future__ import annotations

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from agents.config import AgentConfig
from agents.prompts import build_translator_prompt
from agents.tools.content import create_content_server

VALID_LANGUAGES = ("fr", "it")


async def translate_layer(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_type: str,
    target_lang: str,
) -> float:
    """Translate a commentary layer from German to the target language.

    Returns cost in USD.
    """
    if target_lang not in VALID_LANGUAGES:
        raise ValueError(
            f"Unknown target language: {target_lang}. "
            f"Must be one of {VALID_LANGUAGES}"
        )

    system_prompt = build_translator_prompt(
        config.guidelines_root, target_lang,
    )
    content_server = create_content_server(config.content_root)

    suffix_str = article_suffix or ""
    lang_name = "French" if target_lang == "fr" else "Italian"
    prompt = (
        f"Translate the {layer_type} layer for "
        f"Art. {article_number}{suffix_str} {law} "
        f"from German to {lang_name}. "
        f"Read the source layer '{layer_type}' and write "
        f"the translation as '{layer_type}.{target_lang}'."
    )

    options = ClaudeAgentOptions(
        mcp_servers={"content": content_server},
        allowed_tools=[
            "mcp__content__read_layer_content",
            "mcp__content__write_layer_content",
        ],
        system_prompt=system_prompt,
        model=config.model_translator,
        max_turns=10,
        max_budget_usd=0.20,
        permission_mode="bypassPermissions",
    )

    cost = 0.0
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage) and message.total_cost_usd:
            cost = message.total_cost_usd

    return cost
