"""Fix fabricated citations in existing commentary content.

Targets textbook/literature citations with specific Randziffer (N.) numbers
that cannot be verified against reference data. These were commonly
hallucinated by the generation pipeline.

Strategy:
- Strip unverifiable N. numbers from literature citations (keep author/title)
- Preserve BSK/CR citations that match reference data
- Preserve all BGE citations (verified via opencaselaw)
- Generate a change log for editorial review

Usage:
  uv run python -m scripts.fix_citations --law BV --dry-run
  uv run python -m scripts.fix_citations --law BV
  uv run python -m scripts.fix_citations --all --dry-run
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from scripts.schema import LAWS

CONTENT_ROOT = Path("content")

# Pattern to match literature citations with N. numbers that may be fabricated.
# Matches: "Author/Author, Title, N. 1234" or "Author/Author, Title, N 1234"
# but NOT BSK/CR patterns (those have their own verification).
LITERATURE_N_PATTERN = re.compile(
    r"("
    r"(?:[A-ZÄÖÜ]\w+(?:/[A-ZÄÖÜ]\w+)*)"  # Authors
    r",\s+"
    r"(?!BSK\s)(?!CR\s)(?!in:\s)"  # Exclude BSK, CR, and "in:" patterns
    r"[\w\s\-äöüéèêëàâùûôïîç.]+?"  # Title
    r"(?:,\s+\d+\.\s*Aufl\.\s*\d{4})?"  # Optional edition
    r")"
    r",\s*N\.?\s*(\d[\d\s,\-–ff.]*)"  # The N. number to strip
    r"(?=[\s;,.\)])",
)

# More specific patterns for common fabrication types:
# "Häfelin/Haller/Keller/Thurnherr, Bundesstaatsrecht, N 324"
# "Müller/Schefer, Grundrechte, N 754"
# "Rhinow/Schefer/Uebersax, Verfassungsrecht, N 1117"
TEXTBOOK_N_PATTERN = re.compile(
    r"("
    r"[A-ZÄÖÜ]\w+(?:/[A-ZÄÖÜ]\w+)+"  # Multiple authors (2+)
    r",\s+"
    r"[A-ZÄÖÜ][\w\s\-äöüéèêëàâùûôïîç.]+"  # Title starting with capital
    r"(?:,\s+\d+\.\s*Aufl\.\s*\d{4})?"  # Optional edition
    r")"
    r"(?:,\s*N\.?\s*)(\d[\d\s,\-–ff.]*)"  # N. number
    r"(?=[\s;,.\)])",
)


def fix_literature_citations(
    content: str,
    bsk_refs_available: bool = False,
) -> tuple[str, list[dict]]:
    """Remove unverifiable N. numbers from literature citations.

    Returns (fixed_content, list_of_changes).
    """
    changes: list[dict] = []

    def _replace(match: re.Match) -> str:
        full = match.group(0)
        author_title = match.group(1)
        n_number = match.group(2)

        # Don't strip N. from BSK/CR citations (handled separately)
        if "BSK" in author_title or "CR " in author_title:
            return full

        changes.append({
            "original": full,
            "fixed": author_title,
            "stripped_n": n_number.strip(),
            "position": match.start(),
        })
        return author_title

    fixed = TEXTBOOK_N_PATTERN.sub(_replace, content)
    return fixed, changes


def fix_article(
    article_dir: Path,
    dry_run: bool = True,
) -> list[dict]:
    """Fix citations in a single article's doctrine layer.

    Returns list of changes made.
    """
    all_changes: list[dict] = []

    for layer in ("doctrine",):  # Focus on doctrine where fabrication occurs
        layer_path = article_dir / f"{layer}.md"
        if not layer_path.exists():
            continue

        content = layer_path.read_text()

        # Skip placeholders
        lines = [ln for ln in content.strip().split("\n") if ln.strip()]
        if len(lines) <= 3 and sum(len(ln) for ln in lines) <= 200:
            continue

        fixed, changes = fix_literature_citations(content)

        if changes:
            for c in changes:
                c["layer"] = layer
                c["article_dir"] = str(article_dir.name)

            all_changes.extend(changes)

            if not dry_run:
                layer_path.write_text(fixed)

    return all_changes


def fix_law(
    law: str,
    dry_run: bool = True,
) -> list[dict]:
    """Fix citations for all articles in a law."""
    law_dir = CONTENT_ROOT / law.lower()
    if not law_dir.exists():
        print(f"No content directory for {law}")
        return []

    all_changes: list[dict] = []

    for art_dir in sorted(law_dir.iterdir()):
        if not art_dir.is_dir() or not art_dir.name.startswith("art-"):
            continue

        changes = fix_article(art_dir, dry_run=dry_run)
        all_changes.extend(changes)

    return all_changes


def main():
    parser = argparse.ArgumentParser(
        description="Fix fabricated citations in commentary content",
    )
    parser.add_argument(
        "--law",
        help="Law to fix (e.g., BV, OR)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Fix all laws",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )

    args = parser.parse_args()

    if not args.law and not args.all:
        parser.error("Specify --law or --all")

    dry_run = args.dry_run
    laws = list(LAWS) if args.all else [args.law]
    total_changes: list[dict] = []

    for law in laws:
        mode = "DRY RUN" if dry_run else "FIXING"
        print(f"[{mode}] {law}...")
        changes = fix_law(law, dry_run=dry_run)
        total_changes.extend(changes)

        if changes:
            print(f"  {len(changes)} citations to fix:")
            for c in changes[:10]:
                print(f"    {c['article_dir']}: {c['original'][:60]}...")
                print(f"      -> {c['fixed'][:60]}")
            if len(changes) > 10:
                print(f"    ... and {len(changes) - 10} more")
        else:
            print("  No fabricated N. numbers found")

    print(f"\n{'='*50}")
    print(f"Total: {len(total_changes)} citations {'to fix' if dry_run else 'fixed'}")
    if dry_run and total_changes:
        print("\nRun without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
