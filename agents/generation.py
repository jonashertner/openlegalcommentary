"""Generation loop — generate, evaluate, retry, translate.

Orchestrates the per-article workflow:
1. Generate a layer with the law agent
2. Evaluate with the evaluator
3. If rejected, retry with feedback (max 3 attempts)
4. If approved, translate to FR and IT
5. Update meta.yaml with results
"""
from __future__ import annotations

import hashlib
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


def _layer_file_path(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_type: str,
):
    """Return the absolute path to a layer markdown file."""
    dir_name = article_dir_name(article_number, article_suffix)
    return config.content_root / law.lower() / dir_name / f"{layer_type}.md"


def _layer_file_hash(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_type: str,
) -> str | None:
    """Return a SHA-256 hash of the target layer markdown file, or ``None``
    if the file does not exist.

    Used by the write-skip safeguard in ``generate_and_evaluate`` to detect
    law-agent runs that completed without calling ``write_layer_content`` on
    the target layer. Observed on Sonnet 4.6 in ~1 of 3 BGFA Art. 12 runs —
    the agent's final text response was delivered without a
    ``write_layer_content`` tool call, leaving the on-disk content
    unchanged. The evaluator then silently scored the pre-existing content.
    """
    layer_path = _layer_file_path(
        config, law, article_number, article_suffix, layer_type,
    )
    if not layer_path.exists():
        return None
    return hashlib.sha256(layer_path.read_bytes()).hexdigest()


def _read_layer_snapshot(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_type: str,
) -> bytes | None:
    """Return raw bytes of the target layer file, or ``None`` if it doesn't
    exist. Used to capture a rollback snapshot before ``generate_and_evaluate``
    so the pre-regeneration content can be restored if every retry fails.
    """
    layer_path = _layer_file_path(
        config, law, article_number, article_suffix, layer_type,
    )
    if not layer_path.exists():
        return None
    return layer_path.read_bytes()


def _restore_layer_snapshot(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_type: str,
    snapshot: bytes | None,
) -> None:
    """Restore a layer file from a snapshot captured before regeneration.

    If ``snapshot`` is ``None`` the layer file did not exist before
    regeneration, so any file on disk now is a partial write from a failed
    attempt — we remove it rather than leaving a broken stub.
    """
    layer_path = _layer_file_path(
        config, law, article_number, article_suffix, layer_type,
    )
    if snapshot is None:
        if layer_path.exists():
            layer_path.unlink()
        return
    layer_path.write_bytes(snapshot)


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

    # Capture a snapshot of the target layer file *before* any generation
    # attempts. If every retry fails we restore this snapshot so the article
    # is never left worse than its pre-regeneration state. Observed concretely
    # on BV Art. 118 during Phase 1b: attempt 1 hit the write-skip safeguard,
    # attempts 2 and 3 were evaluator-rejected, and the pipeline left the
    # last rejected content on disk — audit went from 8 flagged to 12 (worse
    # than baseline). This safeguard makes the full-retry-failure case
    # content-neutral instead of content-regressive.
    rollback_snapshot = _read_layer_snapshot(
        config, law, article_number, article_suffix, layer_type,
    )

    for attempt in range(1, config.max_retries + 1):
        logger.info(
            "Generating %s for Art. %d%s %s (attempt %d/%d)",
            layer_type, article_number, article_suffix,
            law, attempt, config.max_retries,
        )

        before_hash = _layer_file_hash(
            config, law, article_number, article_suffix, layer_type,
        )

        gen_cost = await generate_layer(
            config, law, article_number, article_suffix,
            layer_type, feedback=feedback,
        )
        total_cost += gen_cost

        after_hash = _layer_file_hash(
            config, law, article_number, article_suffix, layer_type,
        )
        if before_hash == after_hash:
            # Write-skip safeguard: the law agent's loop completed without
            # modifying the target layer file on disk. This happens when
            # the agent produces its final text response without calling
            # ``write_layer_content``. Without this check the evaluator
            # would silently score the pre-existing content, the pipeline
            # would report PASS, and no new content would actually ship.
            # Treat it as a failed attempt and retry with explicit
            # feedback telling the agent what it missed.
            logger.warning(
                "Write-skip detected on %s Art. %d%s %s "
                "(attempt %d/%d); target file unchanged — retrying",
                layer_type, article_number, article_suffix, law,
                attempt, config.max_retries,
            )
            feedback = (
                "Your previous attempt finished without calling the "
                "write_layer_content tool to save the new layer content. "
                f"You MUST call write_layer_content with your generated "
                f"content for layer '{layer_type}' as part of this run. "
                "The task is not complete without this tool call. Start "
                "fresh and ensure your final action is a write_layer_content "
                "call that actually writes the layer content to disk."
            )
            continue

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
    # Roll back to the pre-regeneration snapshot so the article is never left
    # worse than its baseline state after a total-retry failure. Without this
    # the last rejected attempt's content would persist on disk.
    _restore_layer_snapshot(
        config, law, article_number, article_suffix, layer_type,
        rollback_snapshot,
    )
    logger.info(
        "Rolled back %s for Art. %d%s %s to pre-regeneration snapshot",
        layer_type, article_number, article_suffix, law,
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

            for lang in ("fr", "it", "en"):
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
