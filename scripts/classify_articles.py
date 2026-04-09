"""Article significance classification for openlegalcommentary.

Classifies articles into tiers based on their importance, which determines
the depth of generated commentary:

  Tier 1: Foundational — most-cited, constitutional keystones (80-150 N.)
  Tier 2: Important — major rights, key provisions (40-80 N.)
  Tier 3: Standard — regular provisions (25-50 N.)
  Tier 4: Brief — transitional, organizational (10-25 N.)

Classification signals:
  - Number of leading cases on opencaselaw (citation authority)
  - Cross-references from other articles
  - Whether the article appears in doctrinal debates
  - Manual overrides for known foundational articles

Usage:
  uv run python -m scripts.classify_articles --law BV
  uv run python -m scripts.classify_articles --all
  uv run python -m scripts.classify_articles --law BV --update-meta
"""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scripts.schema import LAWS

CONTENT_ROOT = Path("content")

# Manual tier overrides for well-known foundational articles.
# These are constitutional/legal keystones that always deserve deep treatment.
TIER_OVERRIDES: dict[str, dict[int, str]] = {
    "BV": {
        # Grundlagen
        1: "tier_2", 2: "tier_2", 3: "tier_2", 4: "tier_2",
        5: "tier_1", 5.1: "tier_2", 6: "tier_2",
        # Grundrechte
        7: "tier_1", 8: "tier_1", 9: "tier_1", 10: "tier_1",
        11: "tier_2", 12: "tier_2", 13: "tier_1", 14: "tier_2",
        15: "tier_2", 16: "tier_2", 17: "tier_2", 18: "tier_2",
        19: "tier_2", 20: "tier_2", 21: "tier_2", 22: "tier_2",
        23: "tier_2", 24: "tier_2", 25: "tier_2", 26: "tier_1",
        27: "tier_1", 28: "tier_2", 29: "tier_1", 30: "tier_2",
        31: "tier_2", 32: "tier_2", 33: "tier_2", 34: "tier_2",
        35: "tier_1", 36: "tier_1",
        # Sozialziele
        41: "tier_2",
        # Bund und Kantone
        49: "tier_1",
        # Politische Rechte
        138: "tier_2", 139: "tier_2", 140: "tier_2",
        # Bundesgericht
        189: "tier_2", 190: "tier_1", 191: "tier_2",
    },
    "OR": {
        # Allgemeiner Teil
        1: "tier_1", 2: "tier_2", 18: "tier_1", 19: "tier_1", 20: "tier_1",
        41: "tier_1", 42: "tier_2", 43: "tier_2", 44: "tier_2",
        55: "tier_1", 58: "tier_1", 97: "tier_1", 98: "tier_2",
        99: "tier_2", 100: "tier_1", 107: "tier_2", 108: "tier_2",
        109: "tier_2", 110: "tier_2", 111: "tier_2", 112: "tier_2",
        # Besonderer Teil
        184: "tier_1", 197: "tier_2", 253: "tier_1", 254: "tier_2",
        256: "tier_2", 257: "tier_2", 261: "tier_2", 266: "tier_2",
        271: "tier_2", 312: "tier_1", 319: "tier_1", 320: "tier_2",
        321: "tier_2", 328: "tier_1", 336: "tier_1", 337: "tier_1",
        363: "tier_2", 394: "tier_1", 398: "tier_2", 399: "tier_2",
        # Gesellschaftsrecht
        620: "tier_2", 660: "tier_2", 680: "tier_2",
        706: "tier_2", 707: "tier_2", 714: "tier_2", 716: "tier_2",
        717: "tier_1", 725: "tier_1", 754: "tier_2",
        772: "tier_2", 798: "tier_2", 808: "tier_2",
    },
    "ZGB": {
        1: "tier_1", 2: "tier_1", 3: "tier_2", 4: "tier_2",
        8: "tier_1", 11: "tier_2", 12: "tier_2", 13: "tier_2",
        28: "tier_1", 47: "tier_2",
        # Familienrecht
        90: "tier_2", 111: "tier_2", 114: "tier_2", 124: "tier_2",
        125: "tier_2", 133: "tier_2", 163: "tier_2", 176: "tier_2",
        # Erbrecht
        470: "tier_2", 471: "tier_2", 473: "tier_2",
        # Sachenrecht
        641: "tier_1", 679: "tier_2", 684: "tier_2",
        712: "tier_2", 793: "tier_2",
        919: "tier_2", 930: "tier_2", 933: "tier_2",
    },
    "StGB": {
        1: "tier_2", 10: "tier_2", 11: "tier_2", 12: "tier_1",
        13: "tier_2", 14: "tier_2", 15: "tier_2", 16: "tier_2",
        17: "tier_2", 18: "tier_2", 19: "tier_1", 20: "tier_2",
        21: "tier_2", 22: "tier_2", 24: "tier_2", 25: "tier_2",
        47: "tier_1", 48: "tier_2", 49: "tier_2",
        # Einzelne Straftatbestände
        111: "tier_1", 112: "tier_2", 122: "tier_2", 123: "tier_2",
        125: "tier_2", 128: "tier_2", 138: "tier_2", 139: "tier_1",
        146: "tier_1", 148: "tier_2", 156: "tier_2", 158: "tier_2",
        173: "tier_2", 174: "tier_2", 177: "tier_2",
        180: "tier_2", 181: "tier_2", 187: "tier_2",
        251: "tier_2", 252: "tier_2", 261: "tier_2",
        305: "tier_2",
    },
    "ZPO": {
        1: "tier_2", 52: "tier_2", 55: "tier_2", 57: "tier_2",
        59: "tier_1", 60: "tier_2", 83: "tier_2", 84: "tier_2",
        88: "tier_2", 90: "tier_2", 91: "tier_2",
        197: "tier_2", 198: "tier_2", 219: "tier_2",
        236: "tier_2", 237: "tier_2", 241: "tier_2",
        252: "tier_2", 254: "tier_2", 255: "tier_2",
        257: "tier_1", 261: "tier_1", 262: "tier_2",
        308: "tier_2", 310: "tier_2", 311: "tier_2",
        317: "tier_2", 319: "tier_2", 326: "tier_2",
    },
    "StPO": {
        3: "tier_2", 6: "tier_2", 10: "tier_2",
        107: "tier_2", 113: "tier_2", 131: "tier_2",
        140: "tier_2", 141: "tier_1", 158: "tier_2",
        196: "tier_2", 197: "tier_2", 221: "tier_1",
        225: "tier_2", 227: "tier_2", 236: "tier_2",
        263: "tier_2", 269: "tier_2",
        319: "tier_2", 324: "tier_2",
        382: "tier_2", 393: "tier_2", 410: "tier_2",
    },
}


def classify_article(
    law: str,
    article_number: int,
    caselaw_count: int = 0,
) -> str:
    """Classify an article into a significance tier.

    Priority:
    1. Manual override (if exists)
    2. Case law volume heuristic
    3. Default tier_3
    """
    # Check manual override
    overrides = TIER_OVERRIDES.get(law, {})
    if article_number in overrides:
        return overrides[article_number]

    # Heuristic based on case law volume
    if caselaw_count >= 50:
        return "tier_1"
    elif caselaw_count >= 20:
        return "tier_2"
    elif caselaw_count >= 5:
        return "tier_3"
    else:
        return "tier_4"


def classify_law(law: str, update_meta: bool = False) -> dict[str, str]:
    """Classify all articles in a law.

    Returns dict of article_key -> tier.
    """
    law_dir = CONTENT_ROOT / law.lower()
    if not law_dir.exists():
        print(f"No content directory for {law}")
        return {}

    results: dict[str, str] = {}

    for art_dir in sorted(law_dir.iterdir()):
        if not art_dir.is_dir() or not art_dir.name.startswith("art-"):
            continue

        meta_path = art_dir / "meta.yaml"
        if not meta_path.exists():
            continue

        meta = yaml.safe_load(meta_path.read_text()) or {}
        article_number = meta.get("article", 0)
        article_suffix = meta.get("article_suffix", "")

        # Count case law citations as a signal (from caselaw.md content)
        caselaw_count = 0
        caselaw_path = art_dir / "caselaw.md"
        if caselaw_path.exists():
            content = caselaw_path.read_text()
            from scripts.citation_patterns import BGE_PATTERN
            caselaw_count = len(BGE_PATTERN.findall(content))

        tier = classify_article(law, article_number, caselaw_count)
        key = f"{article_number}{article_suffix}"
        results[key] = tier

        if update_meta:
            meta["significance"] = tier
            meta_path.write_text(yaml.dump(
                meta, default_flow_style=False,
                allow_unicode=True, sort_keys=False,
            ))

    return results


def print_classification(law: str, results: dict[str, str]) -> None:
    """Print classification results."""
    tier_counts: dict[str, int] = {}
    for tier in results.values():
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

    print(f"\n{law} Article Classification")
    print(f"{'='*40}")
    for tier in ("tier_1", "tier_2", "tier_3", "tier_4"):
        count = tier_counts.get(tier, 0)
        label = {
            "tier_1": "Foundational",
            "tier_2": "Important",
            "tier_3": "Standard",
            "tier_4": "Brief",
        }[tier]
        print(f"  {tier} ({label:12s}): {count:>4} articles")
    print(f"  {'Total':26s}: {sum(tier_counts.values()):>4} articles")

    # Show tier 1 articles
    tier_1 = [k for k, v in results.items() if v == "tier_1"]
    if tier_1:
        print("\nTier 1 articles:")
        for art in sorted(tier_1, key=lambda x: int("".join(c for c in x if c.isdigit()) or "0")):
            print(f"  Art. {art} {law}")


def main():
    parser = argparse.ArgumentParser(
        description="Classify articles by significance tier",
    )
    parser.add_argument("--law", help="Law to classify")
    parser.add_argument("--all", action="store_true", help="Classify all laws")
    parser.add_argument(
        "--update-meta", action="store_true",
        help="Write tier to meta.yaml",
    )

    args = parser.parse_args()

    if not args.law and not args.all:
        parser.error("Specify --law or --all")

    laws = list(LAWS) if args.all else [args.law]

    for law in laws:
        results = classify_law(law, update_meta=args.update_meta)
        if results:
            print_classification(law, results)
            if args.update_meta:
                print("  (meta.yaml updated)")


if __name__ == "__main__":
    main()
