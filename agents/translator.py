"""Translator agent — translates commentary layers from German to French/Italian.

Uses the translation guidelines from global.md §III and official Fedlex termdat
terminology for legal terms.
"""
from __future__ import annotations

from agents.anthropic_client import run_agent
from agents.config import AgentConfig
from agents.prompts import build_translator_prompt
from agents.tools.content import create_content_tools

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
    content_tools = create_content_tools(config.content_root)

    suffix_str = article_suffix or ""
    lang_name = "French" if target_lang == "fr" else "Italian"
    prompt = (
        f"Translate the {layer_type} layer for "
        f"Art. {article_number}{suffix_str} {law} "
        f"from German to {lang_name}. "
        f"Read the source layer '{layer_type}' and write "
        f"the translation as '{layer_type}.{target_lang}'."
    )

    _, cost = await run_agent(
        system_prompt=system_prompt,
        prompt=prompt,
        model=config.model_translator,
        content_tools=content_tools,
        opencaselaw_tools=None,
        allowed_tools=[
            "read_layer_content",
            "write_layer_content",
        ],
        max_turns=10,
    )

    return cost
