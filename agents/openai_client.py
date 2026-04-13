"""OpenAI/xAI API client for cross-model evaluation.

Uses the OpenAI Python SDK, which is compatible with xAI's Grok API
via base_url override. Evaluation-only — no tool use.
"""
from __future__ import annotations

import logging
import os

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


async def run_evaluation(
    *,
    system_prompt: str,
    prompt: str,
    model: str,
    base_url: str,
    api_key_env: str,
) -> tuple[str, float]:
    """Run a single evaluation call against an OpenAI-compatible API.

    Returns (response_text, estimated_cost_usd).
    Raises ValueError if the API key env var is not set.
    """
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise ValueError(
            f"API key environment variable '{api_key_env}' is not set"
        )

    client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        max_tokens=4096,
    )

    text = response.choices[0].message.content or ""
    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0

    cost = (prompt_tokens * 10.0 + completion_tokens * 30.0) / 1_000_000

    logger.info(
        "run_evaluation(%s @ %s) tokens: in=%d out=%d cost=$%.4f",
        model, base_url, prompt_tokens, completion_tokens, cost,
    )

    return text, cost
