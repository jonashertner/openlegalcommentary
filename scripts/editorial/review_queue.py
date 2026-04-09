"""Review queue for articles flagged for human editorial attention.

Articles enter the queue when:
- Citation verification flags unverifiable references
- Quality score is below threshold after max retries
- Agent evaluation flags content for human review
- A human editor requests re-review

The queue is derived from content metadata — not a separate data store.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from scripts.schema import LAWS

CONTENT_ROOT = Path("content")


@dataclass
class ReviewItem:
    """An article requiring editorial review."""

    law: str
    article: int
    article_suffix: str
    layer: str
    reason: str
    quality_score: float | None
    editorial_status: str
    editor: str


def scan_review_queue(
    law: str | None = None,
    editor: str | None = None,
) -> list[ReviewItem]:
    """Scan content metadata for articles needing review.

    Returns articles where:
    - editorial_status is 'flagged' or 'draft'
    - verified is False
    - quality_score is below threshold
    """
    items: list[ReviewItem] = []
    laws = [law] if law else list(LAWS)

    for law_name in laws:
        law_dir = CONTENT_ROOT / law_name.lower()
        if not law_dir.exists():
            continue

        for art_dir in sorted(law_dir.iterdir()):
            if not art_dir.is_dir() or not art_dir.name.startswith("art-"):
                continue

            meta_path = art_dir / "meta.yaml"
            if not meta_path.exists():
                continue

            meta = yaml.safe_load(meta_path.read_text()) or {}
            article_number = meta.get("article", 0)
            article_suffix = meta.get("article_suffix", "")
            layers = meta.get("layers", {})

            for layer_name, layer_data in layers.items():
                if not isinstance(layer_data, dict):
                    continue

                status = layer_data.get("editorial_status", "draft")
                verified = layer_data.get("verified", False)
                score = layer_data.get("quality_score")
                assigned = layer_data.get("editor", "")

                if editor and assigned != editor:
                    continue

                # Determine if this needs review
                reason = ""
                if status == "flagged":
                    reason = "Flagged for review"
                elif not verified and score is not None:
                    reason = "Citations not verified"
                elif score is not None and score < 0.90:
                    reason = f"Quality below threshold ({score:.2f})"

                if reason:
                    items.append(ReviewItem(
                        law=law_name,
                        article=article_number,
                        article_suffix=article_suffix,
                        layer=layer_name,
                        reason=reason,
                        quality_score=score,
                        editorial_status=status,
                        editor=assigned,
                    ))

    return items


def print_queue(items: list[ReviewItem]) -> None:
    """Print the review queue in a readable format."""
    if not items:
        print("Review queue is empty.")
        return

    print(f"Review Queue: {len(items)} items")
    print(f"{'='*70}")
    print(
        f"{'Law':<6} {'Article':<10} {'Layer':<10} "
        f"{'Score':<8} {'Status':<15} {'Reason'}"
    )
    print(f"{'-'*70}")

    for item in items:
        suffix = item.article_suffix or ""
        score_str = f"{item.quality_score:.2f}" if item.quality_score else "—"
        print(
            f"{item.law:<6} "
            f"Art. {item.article}{suffix:<5} "
            f"{item.layer:<10} "
            f"{score_str:<8} "
            f"{item.editorial_status:<15} "
            f"{item.reason}"
        )
