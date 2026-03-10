"""Generation loop — generate, evaluate, retry, translate.

Orchestrates the per-article workflow:
1. Generate a layer with the law agent
2. Evaluate with the evaluator
3. If rejected, retry with feedback (max 3 attempts)
4. If approved, translate to FR and IT
5. Update meta.yaml with results
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

import yaml

from agents.config import AgentConfig
from agents.evaluator import EvalResult, evaluate_layer
from agents.law_agent import generate_layer
from agents.translator import translate_layer
from scripts.fetch_articles import article_dir_name

logger = logging.getLogger(__name__)


@dataclass
class LayerResult:
    """Result of generating and evaluating a single layer."""

    law: str
    article_number: int
    article_suffix: str
    layer_type: str
    success: bool
    attempts: int
    eval_result: EvalResult | None
    cost_usd: float
    flagged_for_review: bool


async def generate_and_evaluate(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_type: str,
) -> LayerResult:
    """Generate a layer, evaluate it, retry on failure."""
    total_cost = 0.0
    feedback = None
    eval_result = None

    for attempt in range(1, config.max_retries + 1):
        logger.info(
            "Generating %s for Art. %d%s %s (attempt %d/%d)",
            layer_type, article_number, article_suffix,
            law, attempt, config.max_retries,
        )

        gen_cost = await generate_layer(
            config, law, article_number, article_suffix,
            layer_type, feedback=feedback,
        )
        total_cost += gen_cost

        logger.info(
            "Evaluating %s for Art. %d%s %s",
            layer_type, article_number, article_suffix, law,
        )
        eval_result = await evaluate_layer(
            config, law, article_number, article_suffix,
            layer_type,
        )

        if eval_result.passed:
            logger.info("Pass: %s passed evaluation", layer_type)
            return LayerResult(
                law=law, article_number=article_number,
                article_suffix=article_suffix,
                layer_type=layer_type, success=True,
                attempts=attempt, eval_result=eval_result,
                cost_usd=total_cost, flagged_for_review=False,
            )

        feedback = eval_result.feedback_text()
        logger.warning(
            "Fail: %s rejected (attempt %d/%d): %s",
            layer_type, attempt, config.max_retries,
            feedback[:200],
        )

    logger.error(
        "Fail: %s for Art. %d%s %s flagged for review after %d attempts",
        layer_type, article_number, article_suffix,
        law, config.max_retries,
    )
    return LayerResult(
        law=law, article_number=article_number,
        article_suffix=article_suffix,
        layer_type=layer_type, success=False,
        attempts=config.max_retries,
        eval_result=eval_result, cost_usd=total_cost,
        flagged_for_review=True,
    )


def _update_meta_layer(
    config: AgentConfig, law: str, article_number: int,
    article_suffix: str, layer_type: str,
    eval_result: EvalResult,
) -> None:
    """Update meta.yaml with layer generation results."""
    dir_name = article_dir_name(article_number, article_suffix)
    meta_path = (
        config.content_root / law.lower() / dir_name / "meta.yaml"
    )

    if meta_path.exists():
        meta = yaml.safe_load(meta_path.read_text()) or {}
    else:
        meta = {}

    if "layers" not in meta:
        meta["layers"] = {}

    existing = meta["layers"].get(layer_type, {})
    version = existing.get("version", 0) + 1

    meta["layers"][layer_type] = {
        "last_generated": date.today().isoformat(),
        "version": version,
        "quality_score": (
            min(eval_result.scores.values())
            if eval_result.scores else None
        ),
    }

    meta_path.write_text(
        yaml.dump(
            meta, default_flow_style=False,
            allow_unicode=True, sort_keys=False,
        )
    )


async def process_article(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_types: list[str],
) -> list[LayerResult]:
    """Generate, evaluate, and translate all requested layers."""
    results = []

    for layer_type in layer_types:
        result = await generate_and_evaluate(
            config, law, article_number, article_suffix,
            layer_type,
        )
        results.append(result)

        if result.success and result.eval_result:
            _update_meta_layer(
                config, law, article_number, article_suffix,
                layer_type, result.eval_result,
            )

            for lang in ("fr", "it"):
                try:
                    await translate_layer(
                        config, law, article_number,
                        article_suffix, layer_type, lang,
                    )
                    logger.info(
                        "Translated %s to %s for Art. %d%s %s",
                        layer_type, lang, article_number,
                        article_suffix, law,
                    )
                except Exception:
                    logger.exception(
                        "Translation failed: %s -> %s for Art. %d%s %s",
                        layer_type, lang, article_number,
                        article_suffix, law,
                    )

    return results
