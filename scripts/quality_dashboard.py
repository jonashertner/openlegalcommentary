"""Quality metrics dashboard for openlegalcommentary.

Aggregates quality scores, citation verification rates, editorial status,
and translation coverage across all content.

Usage:
  uv run python -m scripts.quality_dashboard
  uv run python -m scripts.quality_dashboard --law BV
  uv run python -m scripts.quality_dashboard --json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from scripts.schema import LAWS

CONTENT_ROOT = Path("content")
LAYERS = ("summary", "doctrine", "caselaw")
TRANSLATIONS = ("fr", "it", "en")


def collect_metrics(law: str | None = None) -> dict:
    """Collect quality metrics across all content."""
    laws = [law] if law else list(LAWS)
    metrics: dict = {
        "laws": {},
        "totals": {
            "articles": 0,
            "with_content": 0,
            "layers_total": 0,
            "layers_by_status": {},
            "layers_verified": 0,
            "layers_unverified": 0,
            "quality_scores": [],
            "translations": {"fr": 0, "it": 0, "en": 0},
            "by_tier": {},
        },
    }

    for law_name in laws:
        law_dir = CONTENT_ROOT / law_name.lower()
        if not law_dir.exists():
            continue

        law_metrics: dict = {
            "articles": 0,
            "with_content": 0,
            "layers": 0,
            "layers_by_status": {},
            "layers_verified": 0,
            "quality_scores": [],
            "translations": {"fr": 0, "it": 0, "en": 0},
            "by_tier": {},
        }

        for art_dir in sorted(law_dir.iterdir()):
            if not art_dir.is_dir() or not art_dir.name.startswith("art-"):
                continue

            law_metrics["articles"] += 1
            metrics["totals"]["articles"] += 1

            meta_path = art_dir / "meta.yaml"
            if not meta_path.exists():
                continue

            meta = yaml.safe_load(meta_path.read_text()) or {}
            layers_meta = meta.get("layers", {})
            tier = meta.get("significance", "tier_3")

            has_content = False

            for layer_name in LAYERS:
                layer_path = art_dir / f"{layer_name}.md"
                if not layer_path.exists():
                    continue

                content = layer_path.read_text()
                lines = [ln for ln in content.strip().split("\n") if ln.strip()]
                is_placeholder = (
                    len(lines) <= 3
                    and sum(len(ln) for ln in lines) <= 200
                )

                if not is_placeholder:
                    has_content = True
                    law_metrics["layers"] += 1
                    metrics["totals"]["layers_total"] += 1

                    layer_data = layers_meta.get(layer_name, {})
                    if isinstance(layer_data, dict):
                        status = layer_data.get("editorial_status", "draft")
                        law_metrics["layers_by_status"][status] = (
                            law_metrics["layers_by_status"].get(status, 0) + 1
                        )
                        metrics["totals"]["layers_by_status"][status] = (
                            metrics["totals"]["layers_by_status"].get(status, 0) + 1
                        )

                        if layer_data.get("verified"):
                            law_metrics["layers_verified"] += 1
                            metrics["totals"]["layers_verified"] += 1
                        elif layer_data.get("quality_score") is not None:
                            metrics["totals"]["layers_unverified"] += 1

                        score = layer_data.get("quality_score")
                        if score is not None:
                            law_metrics["quality_scores"].append(score)
                            metrics["totals"]["quality_scores"].append(score)

                # Check translations
                for lang in TRANSLATIONS:
                    trans_path = art_dir / f"{layer_name}.{lang}.md"
                    if trans_path.exists() and trans_path.stat().st_size > 50:
                        law_metrics["translations"][lang] += 1
                        metrics["totals"]["translations"][lang] += 1

            if has_content:
                law_metrics["with_content"] += 1
                metrics["totals"]["with_content"] += 1

            # Track by tier
            law_metrics["by_tier"][tier] = (
                law_metrics["by_tier"].get(tier, 0) + 1
            )
            metrics["totals"]["by_tier"][tier] = (
                metrics["totals"]["by_tier"].get(tier, 0) + 1
            )

        metrics["laws"][law_name] = law_metrics

    return metrics


def print_dashboard(metrics: dict) -> None:
    """Print a formatted quality dashboard."""
    totals = metrics["totals"]

    print("\n" + "=" * 60)
    print("  OPEN LEGAL COMMENTARY — Quality Dashboard")
    print("=" * 60)

    # Overview
    print("\n  Content Coverage")
    print(f"  {'-'*40}")
    print(f"  Total articles:     {totals['articles']:>6}")
    print(f"  With content:       {totals['with_content']:>6}")
    if totals["articles"] > 0:
        pct = totals["with_content"] / totals["articles"] * 100
        print(f"  Coverage:           {pct:>5.1f}%")
    print(f"  Total layers:       {totals['layers_total']:>6}")

    # Per-law breakdown
    print("\n  Per-Law Breakdown")
    print(f"  {'-'*40}")
    print(f"  {'Law':<8} {'Articles':>8} {'Content':>8} {'Layers':>8}")
    for law_name, lm in sorted(metrics["laws"].items()):
        print(
            f"  {law_name:<8} {lm['articles']:>8} "
            f"{lm['with_content']:>8} {lm['layers']:>8}"
        )

    # Editorial status
    if totals["layers_by_status"]:
        print("\n  Editorial Status")
        print(f"  {'-'*40}")
        for status, count in sorted(totals["layers_by_status"].items()):
            print(f"  {status:<20} {count:>6}")

    # Quality scores
    scores = totals["quality_scores"]
    if scores:
        avg = sum(scores) / len(scores)
        min_s = min(scores)
        max_s = max(scores)
        print("\n  Quality Scores")
        print(f"  {'-'*40}")
        print(f"  Layers scored:  {len(scores):>6}")
        print(f"  Average:        {avg:>6.3f}")
        print(f"  Min:            {min_s:>6.3f}")
        print(f"  Max:            {max_s:>6.3f}")

    # Citation verification
    print("\n  Citation Verification")
    print(f"  {'-'*40}")
    print(f"  Verified:       {totals['layers_verified']:>6}")
    print(f"  Unverified:     {totals['layers_unverified']:>6}")

    # Translation coverage
    print("\n  Translation Coverage (layers translated)")
    print(f"  {'-'*40}")
    for lang, count in totals["translations"].items():
        lang_name = {"fr": "French", "it": "Italian", "en": "English"}[lang]
        print(f"  {lang_name:<12}     {count:>6}")

    # Significance tiers
    if totals["by_tier"]:
        print("\n  Significance Tiers")
        print(f"  {'-'*40}")
        tier_labels = {
            "tier_1": "Foundational",
            "tier_2": "Important",
            "tier_3": "Standard",
            "tier_4": "Brief",
        }
        for tier in ("tier_1", "tier_2", "tier_3", "tier_4"):
            count = totals["by_tier"].get(tier, 0)
            label = tier_labels.get(tier, tier)
            print(f"  {tier} ({label:12s}) {count:>6}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Quality metrics dashboard",
    )
    parser.add_argument("--law", help="Filter by law")
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON",
    )

    args = parser.parse_args()
    metrics = collect_metrics(law=args.law)

    if args.json:
        # Remove non-serializable parts for JSON output
        output = {
            "laws": {},
            "totals": {
                k: v for k, v in metrics["totals"].items()
                if k != "quality_scores"
            },
        }
        for law, lm in metrics["laws"].items():
            output["laws"][law] = {
                k: v for k, v in lm.items()
                if k != "quality_scores"
            }
            if lm["quality_scores"]:
                output["laws"][law]["avg_quality"] = (
                    sum(lm["quality_scores"]) / len(lm["quality_scores"])
                )
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print_dashboard(metrics)


if __name__ == "__main__":
    main()
