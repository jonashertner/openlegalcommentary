"""A/B test: Opus 4.6 extended thinking vs Sonnet 4.6 for doctrine generation.

Test articles: BV Art. 99, 36, 10
Runs triple-evaluator pipeline on each.
"""
from __future__ import annotations

import asyncio
import logging
import time

from agents.config import AgentConfig
from agents.evaluator import evaluate_layer
from agents.generation import generate_layer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
logger = logging.getLogger(__name__)


async def run_generation(config: AgentConfig, art: int, model: str) -> float:
    """Generate doctrine for a BV article with given model. Returns cost."""
    logger.info("=== Generating BV Art. %d with %s ===", art, model)
    start = time.time()
    cost = await generate_layer(config, "BV", art, "", "doctrine")
    elapsed = time.time() - start
    logger.info(
        "Generation done: Art. %d, model=%s, cost=$%.4f, time=%.0fs",
        art, model, cost, elapsed,
    )
    return cost


async def run_evaluation(config: AgentConfig, art: int) -> dict:
    """Evaluate BV article with triple evaluator. Returns result dict."""
    logger.info("=== Evaluating BV Art. %d ===", art)
    start = time.time()
    result = await evaluate_layer(config, "BV", art, "", "doctrine")
    elapsed = time.time() - start
    logger.info(
        "Evaluation done: Art. %d, verdict=%s, scores=%s, time=%.0fs",
        art, result.verdict, result.scores, elapsed,
    )
    return {
        "verdict": result.verdict,
        "scores": result.scores,
        "non_negotiables": result.non_negotiables,
        "feedback": result.feedback,
        "time_s": elapsed,
    }


async def main():
    articles = [99, 36, 10]

    # Phase 1: Evaluate existing Sonnet versions
    print("\n" + "=" * 60)
    print("PHASE 1: Evaluate existing Sonnet 4.6 versions")
    print("=" * 60)

    config = AgentConfig()
    sonnet_results = {}
    for art in articles:
        sonnet_results[art] = await run_evaluation(config, art)
        print(f"  Art. {art}: {sonnet_results[art]['verdict']} "
              f"scores={sonnet_results[art]['scores']}")

    # Phase 2: Generate with Opus thinking + evaluate
    print("\n" + "=" * 60)
    print("PHASE 2: Generate with Opus 4.6 extended thinking")
    print("=" * 60)

    config_opus = AgentConfig(model_doctrine="opus-thinking")
    opus_results = {}
    for art in [99, 36]:  # Art. 10 skip generation (compare eval only)
        gen_cost = await run_generation(config_opus, art, "opus-thinking")
        eval_result = await run_evaluation(config, art)
        opus_results[art] = {
            **eval_result,
            "gen_cost": gen_cost,
        }
        print(f"  Art. {art}: {opus_results[art]['verdict']} "
              f"scores={opus_results[art]['scores']} "
              f"gen_cost=${gen_cost:.4f}")

    # Summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)

    print("\nSonnet 4.6 (existing):")
    for art, r in sonnet_results.items():
        scores_str = " ".join(f"{k}={v:.2f}" for k, v in r["scores"].items())
        print(f"  Art. {art}: {r['verdict']}  {scores_str}  ({r['time_s']:.0f}s eval)")

    print("\nOpus 4.6 extended thinking:")
    for art, r in opus_results.items():
        scores_str = " ".join(f"{k}={v:.2f}" for k, v in r["scores"].items())
        print(f"  Art. {art}: {r['verdict']}  {scores_str}  "
              f"(gen=${r['gen_cost']:.2f}, {r['time_s']:.0f}s eval)")


if __name__ == "__main__":
    asyncio.run(main())
