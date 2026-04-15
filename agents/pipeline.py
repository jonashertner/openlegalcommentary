"""Pipeline CLI — entry point for daily runs, bootstrap, and single-article generation.

Subcommands:
  daily       Run the daily pipeline (find new decisions, update affected articles)
  bootstrap   Generate all layers for all articles (initial one-time run)
  single      Generate layers for a single article
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
from datetime import date, timedelta
from pathlib import Path

from agents.bootstrap import BootstrapState
from agents.config import AgentConfig
from agents.coordinator import (
    find_new_decisions,
    group_by_law,
    map_decisions_to_articles,
)
from agents.generation import LayerResult, process_article

logger = logging.getLogger(__name__)


async def bootstrap_article(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
) -> list[LayerResult]:
    """Generate all three layers for a single article."""
    return await process_article(
        config, law, article_number, article_suffix,
        layer_types=["caselaw", "doctrine", "summary"],
    )


async def daily_pipeline(
    config: AgentConfig,
    since_date: str | None = None,
) -> dict:
    """Run the daily pipeline.

    1. Find new decisions since last run
    2. Map decisions to affected articles
    3. Update caselaw layer for each affected article
    4. Cascade to doctrine+summary if new leading cases
    5. Return statistics
    """
    if since_date is None:
        since_date = (
            date.today() - timedelta(days=1)
        ).isoformat()

    logger.info(
        "Daily pipeline: searching for decisions since %s",
        since_date,
    )

    decisions = await find_new_decisions(
        config.mcp_base_url, since_date,
    )
    if not decisions:
        logger.info("No new decisions found.")
        return {
            "articles_processed": 0,
            "decisions_found": 0,
            "cost_usd": 0.0,
        }

    articles = map_decisions_to_articles(decisions)

    # Safety guard — never process more than 50 articles in one daily
    # run. If we hit this, something's wrong (parser regression,
    # bad date_from, etc.) — fail loud rather than burn hundreds of
    # dollars on a bad run.
    max_daily_articles = 50
    if len(articles) > max_daily_articles:
        logger.error(
            "Daily pipeline aborting: %d articles exceeds safety "
            "limit of %d. Review decisions_found=%d.",
            len(articles), max_daily_articles, len(decisions),
        )
        return {
            "articles_processed": 0,
            "decisions_found": len(decisions),
            "cost_usd": 0.0,
            "aborted": "exceeded_max_articles",
            "articles_seen": len(articles),
        }

    by_law = group_by_law(articles)

    all_results: list[LayerResult] = []

    async def _process_law(law, law_articles):
        results = []
        for art in law_articles:
            caselaw_results = await process_article(
                config, art.law, art.article_number,
                art.article_suffix, layer_types=["caselaw"],
            )
            results.extend(caselaw_results)

            caselaw_passed = any(
                r.success for r in caselaw_results
            )
            if caselaw_passed and len(art.decision_refs) > 0:
                logger.info(
                    "New leading cases for Art. %d%s %s "
                    "— cascading to doctrine+summary",
                    art.article_number,
                    art.article_suffix, art.law,
                )
                cascade_results = await process_article(
                    config, art.law, art.article_number,
                    art.article_suffix,
                    layer_types=["doctrine", "summary"],
                )
                results.extend(cascade_results)

        return results

    law_tasks = [
        _process_law(law, arts)
        for law, arts in by_law.items()
    ]
    law_results = await asyncio.gather(*law_tasks)
    for results in law_results:
        all_results.extend(results)

    total_cost = sum(r.cost_usd for r in all_results)

    stats = {
        "date": since_date,
        "decisions_found": len(decisions),
        "articles_processed": len(articles),
        "layers_generated": len(all_results),
        "layers_passed": sum(
            1 for r in all_results if r.success
        ),
        "layers_failed": sum(
            1 for r in all_results if not r.success
        ),
        "flagged_for_review": sum(
            1 for r in all_results if r.flagged_for_review
        ),
        "cost_usd": total_cost,
    }
    logger.info(
        "Daily pipeline complete: %s",
        json.dumps(stats, indent=2),
    )
    return stats


async def bootstrap_law(
    config: AgentConfig, law: str,
) -> list[LayerResult]:
    """Bootstrap all articles for a single law."""
    import yaml

    law_dir = config.content_root / law.lower()
    if not law_dir.exists():
        logger.error(
            "No content directory for %s at %s", law, law_dir,
        )
        return []

    results = []
    for art_dir in sorted(law_dir.iterdir()):
        if not art_dir.is_dir():
            continue
        if not art_dir.name.startswith("art-"):
            continue

        meta_path = art_dir / "meta.yaml"
        if not meta_path.exists():
            continue

        meta = yaml.safe_load(meta_path.read_text()) or {}
        article_number = meta.get("article", 0)
        article_suffix = meta.get("article_suffix", "")

        if article_number <= 0:
            continue

        art_results = await bootstrap_article(
            config, law, article_number, article_suffix,
        )
        results.extend(art_results)

    return results


async def bootstrap_law_resumable(
    config: AgentConfig,
    law: str,
    state: BootstrapState,
    max_concurrent: int = 3,
    max_budget: float = 1000.0,
    layer_types: list[str] | None = None,
) -> list[LayerResult]:
    """Bootstrap a law with resumability and concurrency.

    Skips articles already completed in state.
    Stops if cost budget is exceeded.
    Saves state after each article completes.
    """
    import yaml

    law_dir = config.content_root / law.lower()
    if not law_dir.exists():
        logger.error(
            "No content directory for %s at %s", law, law_dir,
        )
        return []

    # Register all articles in state (idempotent)
    for art_dir in sorted(law_dir.iterdir()):
        if not art_dir.is_dir():
            continue
        if not art_dir.name.startswith("art-"):
            continue
        meta_path = art_dir / "meta.yaml"
        if not meta_path.exists():
            continue
        meta = yaml.safe_load(meta_path.read_text()) or {}
        article_number = meta.get("article", 0)
        article_suffix = meta.get("article_suffix", "")
        if article_number > 0:
            state.add_article(
                law, article_number, article_suffix,
            )

    state.save()

    # Filter to pending articles for this law
    pending = [
        a for a in state.get_pending() if a.law == law
    ]

    if not pending:
        logger.info("No pending articles for %s", law)
        return []

    logger.info(
        "Bootstrap %s: %d pending articles "
        "(max_concurrent=%d, max_budget=$%.2f)",
        law, len(pending), max_concurrent, max_budget,
    )

    results: list[LayerResult] = []

    for article in pending:
        if state.budget_exceeded(max_budget):
            logger.warning(
                "Budget exceeded ($%.2f > $%.2f). Stopping.",
                state.total_cost, max_budget,
            )
            break

        logger.info(
            "Processing Art. %d%s %s (%d/%d)",
            article.article_number,
            article.article_suffix,
            article.law,
            state.completed + 1,
            state.total,
        )

        try:
            layers = layer_types or ["caselaw", "doctrine", "summary"]
            art_results = await process_article(
                config, article.law,
                article.article_number,
                article.article_suffix,
                layers,
            )
            cost = sum(r.cost_usd for r in art_results)
            all_passed = all(
                r.success for r in art_results
            )

            if all_passed:
                state.mark_completed(
                    article.law,
                    article.article_number,
                    article.article_suffix,
                    cost=cost,
                )
            else:
                state.mark_failed(
                    article.law,
                    article.article_number,
                    article.article_suffix,
                    error="One or more layers failed",
                )

            state.save()
            results.extend(art_results)

        except Exception as e:
            logger.exception(
                "Error processing Art. %d%s %s",
                article.article_number,
                article.article_suffix,
                article.law,
            )
            state.mark_failed(
                article.law,
                article.article_number,
                article.article_suffix,
                error=str(e),
            )
            state.save()

    logger.info(
        "Bootstrap %s complete: %s",
        law, json.dumps(state.summary()),
    )
    return results


def main():
    parser = argparse.ArgumentParser(
        description="openlegalcommentary agent pipeline",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    daily_parser = sub.add_parser(
        "daily", help="Run daily update pipeline",
    )
    daily_parser.add_argument(
        "--since", help="Date to search from (YYYY-MM-DD)",
    )

    boot_parser = sub.add_parser(
        "bootstrap", help="Bootstrap all articles",
    )
    boot_parser.add_argument(
        "--law", help="Only bootstrap a specific law",
    )
    boot_parser.add_argument(
        "--state-file",
        default="bootstrap_state.json",
        help="Path to bootstrap state file for resumability",
    )
    boot_parser.add_argument(
        "--max-concurrent", type=int, default=3,
        help="Max articles to process in parallel",
    )
    boot_parser.add_argument(
        "--max-budget", type=float, default=1000.0,
        help="Max USD budget before stopping",
    )
    boot_parser.add_argument(
        "--layers", nargs="+",
        default=["caselaw", "doctrine", "summary"],
        help="Layer types to generate (default: all three)",
    )

    single_parser = sub.add_parser(
        "single", help="Generate layers for one article",
    )
    single_parser.add_argument(
        "law", help="Law abbreviation (e.g., OR)",
    )
    single_parser.add_argument(
        "article", type=int, help="Article number",
    )
    single_parser.add_argument(
        "--suffix", default="",
        help="Article suffix (e.g., a)",
    )
    single_parser.add_argument(
        "--layers", nargs="+",
        default=["caselaw", "doctrine", "summary"],
        help="Layer types to generate",
    )

    parser.add_argument(
        "--content-root", default="content",
        help="Content directory",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config = AgentConfig(content_root=Path(args.content_root))

    if args.command == "daily":
        stats = asyncio.run(
            daily_pipeline(config, since_date=args.since),
        )
        print(json.dumps(stats, indent=2))

    elif args.command == "bootstrap":
        from scripts.schema import LAWS

        state_path = Path(args.state_file)
        if state_path.exists():
            state = BootstrapState.load(state_path)
            logger.info(
                "Resuming bootstrap from %s: %s",
                state_path,
                json.dumps(state.summary()),
            )
        else:
            state = BootstrapState(state_path)

        laws = [args.law] if args.law else list(LAWS)
        for law in laws:
            if state.budget_exceeded(args.max_budget):
                logger.warning("Budget exceeded. Stopping.")
                break
            logger.info("Bootstrapping %s...", law)
            results = asyncio.run(
                bootstrap_law_resumable(
                    config, law, state,
                    max_concurrent=args.max_concurrent,
                    max_budget=args.max_budget,
                    layer_types=args.layers,
                )
            )
            passed = sum(1 for r in results if r.success)
            logger.info(
                "%s: %d/%d layers passed",
                law, passed, len(results),
            )

        print(json.dumps(state.summary(), indent=2))

    elif args.command == "single":
        results = asyncio.run(
            process_article(
                config, args.law, args.article,
                args.suffix, args.layers,
            )
        )
        for r in results:
            status = "PASS" if r.success else "FAIL"
            print(
                f"{status} {r.layer_type}: "
                f"{r.attempts} attempts, ${r.cost_usd:.2f}"
            )


if __name__ == "__main__":
    main()
