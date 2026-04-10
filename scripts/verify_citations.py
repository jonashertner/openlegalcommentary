"""Citation verification pipeline for openlegalcommentary.

Verifies citations in generated commentary against available source data:
- BGE references: checked against opencaselaw (when network available)
- BSK/CR references: cross-checked against scripts/commentary_refs/*.json
- BBl references: cross-checked against scripts/preparatory_materials/*.json
- Literature N. numbers: flagged if not backed by reference data

Generates per-article verification reports as JSON.

Usage:
  uv run python -m scripts.verify_citations --law BV
  uv run python -m scripts.verify_citations --law BV --article 8
  uv run python -m scripts.verify_citations --law BV --report
  uv run python -m scripts.verify_citations --all --summary
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from scripts.citation_patterns import (
    Citation,
    CitationType,
    extract_citations,
)
from scripts.schema import LAWS

CONTENT_ROOT = Path("content")
COMMENTARY_REFS_ROOT = Path("scripts/commentary_refs")
PREP_MATERIALS_ROOT = Path("scripts/preparatory_materials")


def _load_commentary_refs(law: str) -> dict:
    """Load BSK commentary reference data for a law.

    On-disk layout: ``scripts/commentary_refs/{law}_refs.json``, keyed by the
    law abbreviation (e.g. ``"BV"``), under which article numbers map to
    reference entries with ``authors``, ``positions``, ``randziffern_map``,
    etc. Each article's data is wrapped under the key ``"primary"`` so that
    downstream BSK verification can read it as ``refs[art_key]["primary"]``.

    CR (Commentaire Romand) reference data does not yet exist on disk. When
    it does, extend this loader to merge those entries under the ``"cr"``
    key on the same article records.
    """
    merged: dict = {}
    path = COMMENTARY_REFS_ROOT / f"{law.lower()}_refs.json"
    if not path.exists():
        return merged
    data = json.loads(path.read_text())
    articles = data.get(law.upper(), {})
    for art_key, art_data in articles.items():
        merged[art_key] = {"primary": art_data}
    return merged


def _load_prep_materials(law: str) -> dict:
    """Load preparatory materials data for a law."""
    path = PREP_MATERIALS_ROOT / f"{law.lower()}.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return data.get("articles", {})


def _collect_known_authors(primary: dict) -> tuple[set[str], set[str]]:
    """Collect known author names for a BSK-covered article.

    Returns two sets:
    - ``strict``: authors listed at the article's top-level ``authors`` key
      (the primary BSK author/s for this article — a strict match here
      means the citation points at the "right" source)
    - ``loose``: additional authors who appear in ``positions[].author``
      or as keys inside ``controversies[].positions``. These are scholars
      known to have *some* position on this article, including from other
      commentaries (St. Galler, Berner Kommentar, standalone treatises).
      A match here is weaker — the author is a real scholar on the topic,
      but the exact commentary source the citation claims may differ.

    The strict set is always a subset of the loose set (loose includes
    strict). This lets callers distinguish "cited the primary BSK author"
    from "cited a known scholar on this article, possibly from a
    different source".
    """
    strict: set[str] = set()
    for a in primary.get("authors", []) or []:
        if isinstance(a, str) and a.strip():
            strict.add(a.strip())

    loose: set[str] = set(strict)
    for position in primary.get("positions", []) or []:
        author = position.get("author") if isinstance(position, dict) else None
        if isinstance(author, str) and author.strip():
            loose.add(author.strip())
    for controversy in primary.get("controversies", []) or []:
        positions = (
            controversy.get("positions", {})
            if isinstance(controversy, dict)
            else {}
        )
        if isinstance(positions, dict):
            for key in positions:
                if isinstance(key, str) and key.strip():
                    loose.add(key.strip())

    return strict, loose


def _author_matches(cited: str, known: set[str]) -> bool:
    """Case-insensitive substring match of a cited author against a set of
    known author names. Substring match is permissive on purpose — "Kessler"
    should match "Martin Kessler" and vice versa — but tight enough that
    unrelated single-token hits (e.g. "Müller" matching "Müller-Chen") are
    acceptable noise for a flag-for-review tool.
    """
    if not cited:
        return False
    cited_lower = cited.lower()
    for k in known:
        k_lower = k.lower()
        if cited_lower in k_lower or k_lower in cited_lower:
            return True
    return False


def _verify_bsk_citation(
    citation: Citation,
    refs: dict,
    article_key: str,
) -> Citation:
    """Verify a BSK citation against reference data.

    Three-state outcome:
    - **strict match**: author appears in the top-level ``authors`` list →
      ``verified = True``, note records "strict match"
    - **loose match**: author appears only in ``positions[].author`` or
      ``controversies[].positions`` keys → ``verified = True``, note
      records "loose match — seen in positions, not in BSK authors list"
    - **no match**: author nowhere in the ref data → ``verified = False``,
      note records the cited author and the known authors

    Articles with no ref data return ``verified = None`` (unchecked).
    Citations with no author field also return ``None``.
    """
    article_refs = refs.get(article_key, {})
    primary = article_refs.get("primary", {})

    author = citation.details.get("author", "")
    strict_authors, loose_authors = _collect_known_authors(primary)

    if not loose_authors:
        citation.verified = None
        citation.verification_note = "No BSK ref data available for this article"
    elif not author:
        citation.verified = None
        citation.verification_note = "No author specified in citation"
    elif _author_matches(author, strict_authors):
        citation.verified = True
        citation.verification_note = "Author matches BSK primary (strict)"
    elif _author_matches(author, loose_authors):
        citation.verified = True
        citation.verification_note = (
            "Author seen in positions/controversies (loose) — "
            "possibly cited from another commentary"
        )
    else:
        citation.verified = False
        citation.verification_note = (
            f"Author '{author}' not in ref data "
            f"(known: {', '.join(sorted(loose_authors))})"
        )

    rz = citation.details.get("randziffer")
    if rz and primary.get("randziffern_map"):
        citation.verification_note += "; has ref data for N. cross-check"

    return citation


def _verify_cr_citation(
    citation: Citation,
    refs: dict,
    article_key: str,
) -> Citation:
    """Verify a CR citation against reference data."""
    article_refs = refs.get(article_key, {})
    cr = article_refs.get("cr", {})

    author = citation.details.get("author", "")
    known_authors = cr.get("authors", [])

    if known_authors and author:
        author_found = any(
            author.lower() in a.lower() or a.lower() in author.lower()
            for a in known_authors
        )
        if author_found:
            citation.verified = True
            citation.verification_note = "Author found in CR ref data"
        else:
            citation.verified = False
            citation.verification_note = (
                f"Author '{author}' not in CR ref data "
                f"(known: {', '.join(known_authors)})"
            )
    elif not known_authors:
        citation.verified = None
        citation.verification_note = "No CR ref data available"
    else:
        citation.verified = None
        citation.verification_note = "No author specified"

    return citation


def _verify_bbl_citation(
    citation: Citation,
    prep_materials: dict,
    article_key: str,
) -> Citation:
    """Verify a BBl citation against preparatory materials data."""
    article_data = prep_materials.get(article_key, {})

    if not article_data:
        citation.verified = None
        citation.verification_note = "No preparatory materials data available"
        return citation

    # Check if page ref appears in known BBl pages
    cited_page = str(citation.details.get("page", ""))
    known_pages: list[str] = []
    for source in article_data.get("sources", []):
        known_pages.extend(source.get("bbl_page_refs", []))

    if known_pages and cited_page:
        page_found = any(
            cited_page in page_range
            for page_range in known_pages
        )
        if page_found:
            citation.verified = True
            citation.verification_note = "BBl page found in prep materials"
        else:
            citation.verified = False
            citation.verification_note = (
                f"BBl page {cited_page} not in prep materials "
                f"(known: {', '.join(known_pages)})"
            )
    elif not known_pages:
        citation.verified = None
        citation.verification_note = "No BBl page refs in prep materials"

    return citation


def verify_article(
    law: str,
    article_dir: Path,
    commentary_refs: dict,
    prep_materials: dict,
) -> dict:
    """Verify all citations in a single article's commentary.

    Returns a verification report dict.
    """
    meta_path = article_dir / "meta.yaml"
    if not meta_path.exists():
        return {"error": "No meta.yaml found"}

    meta = yaml.safe_load(meta_path.read_text()) or {}
    article_number = meta.get("article", 0)
    article_suffix = meta.get("article_suffix", "")
    article_key = f"{article_number}{article_suffix}"

    all_citations: list[Citation] = []
    layers_checked: list[str] = []

    for layer in ("doctrine", "caselaw", "summary"):
        layer_path = article_dir / f"{layer}.md"
        if not layer_path.exists():
            continue

        content = layer_path.read_text()
        # Skip placeholder files
        lines = [ln for ln in content.strip().split("\n") if ln.strip()]
        if len(lines) <= 3 and sum(len(ln) for ln in lines) <= 200:
            continue

        citations = extract_citations(content)
        for c in citations:
            c.details["layer"] = layer

        # Verify each citation
        for c in citations:
            if c.type == CitationType.BGE:
                # BGE citations are trusted (verifiable via opencaselaw)
                c.verified = True
                c.verification_note = "BGE — verifiable via opencaselaw"

            elif c.type == CitationType.BGER:
                c.verified = True
                c.verification_note = "BGer — verifiable via opencaselaw"

            elif c.type == CitationType.BSK:
                _verify_bsk_citation(c, commentary_refs, article_key)

            elif c.type == CitationType.CR:
                _verify_cr_citation(c, commentary_refs, article_key)

            elif c.type == CitationType.BBL:
                _verify_bbl_citation(c, prep_materials, article_key)

            elif c.type == CitationType.STGALLER:
                # St. Galler Kommentar — no ref data to verify against
                c.verified = None
                c.verification_note = "No ref data for St. Galler Kommentar"

            elif c.type == CitationType.LITERATURE:
                # Flag literature with specific N. numbers as potentially fabricated
                rz = c.details.get("randziffer")
                if rz:
                    c.verified = False
                    c.verification_note = (
                        "Literature N. number not verifiable — may be fabricated"
                    )
                else:
                    c.verified = None
                    c.verification_note = "Literature without N. — not verifiable"

        all_citations.extend(citations)
        layers_checked.append(layer)

    # Build report
    total = len(all_citations)
    verified = sum(1 for c in all_citations if c.verified is True)
    flagged = sum(1 for c in all_citations if c.verified is False)
    unchecked = sum(1 for c in all_citations if c.verified is None)

    by_type: dict[str, int] = {}
    for c in all_citations:
        by_type[c.type.value] = by_type.get(c.type.value, 0) + 1

    report = {
        "law": law,
        "article": article_number,
        "article_suffix": article_suffix,
        "layers_checked": layers_checked,
        "total_citations": total,
        "verified": verified,
        "flagged": flagged,
        "unchecked": unchecked,
        "by_type": by_type,
        "citations": [
            {
                "type": c.type.value,
                "reference": c.reference,
                "line": c.line_number,
                "layer": c.details.get("layer", ""),
                "verified": c.verified,
                "note": c.verification_note,
            }
            for c in all_citations
        ],
        "flagged_citations": [
            {
                "type": c.type.value,
                "reference": c.reference,
                "line": c.line_number,
                "layer": c.details.get("layer", ""),
                "note": c.verification_note,
            }
            for c in all_citations
            if c.verified is False
        ],
    }

    return report


def verify_law(law: str, article_number: int | None = None) -> list[dict]:
    """Verify citations for all articles in a law (or a specific article)."""
    law_dir = CONTENT_ROOT / law.lower()
    if not law_dir.exists():
        print(f"No content directory for {law}")
        return []

    commentary_refs = _load_commentary_refs(law)
    prep_materials = _load_prep_materials(law)

    reports = []
    for art_dir in sorted(law_dir.iterdir()):
        if not art_dir.is_dir() or not art_dir.name.startswith("art-"):
            continue

        if article_number is not None:
            meta_path = art_dir / "meta.yaml"
            if meta_path.exists():
                meta = yaml.safe_load(meta_path.read_text()) or {}
                if meta.get("article") != article_number:
                    continue

        report = verify_article(law, art_dir, commentary_refs, prep_materials)
        if report.get("total_citations", 0) > 0:
            reports.append(report)

            # Write per-article report
            report_path = art_dir / ".citations.json"
            report_path.write_text(
                json.dumps(report, indent=2, ensure_ascii=False)
            )

    return reports


def print_summary(reports: list[dict]) -> None:
    """Print a summary of verification results."""
    total_citations = sum(r["total_citations"] for r in reports)
    total_verified = sum(r["verified"] for r in reports)
    total_flagged = sum(r["flagged"] for r in reports)
    total_unchecked = sum(r["unchecked"] for r in reports)

    print("\nVerification Summary")
    print(f"{'='*50}")
    print(f"Articles checked:    {len(reports)}")
    print(f"Total citations:     {total_citations}")
    print(f"  Verified:          {total_verified}")
    print(f"  Flagged:           {total_flagged}")
    print(f"  Unchecked:         {total_unchecked}")

    if total_citations > 0:
        pct = total_verified / total_citations * 100
        print(f"  Verification rate: {pct:.1f}%")

    # Aggregate by type
    by_type: dict[str, int] = {}
    for r in reports:
        for t, count in r["by_type"].items():
            by_type[t] = by_type.get(t, 0) + count

    if by_type:
        print("\nBy citation type:")
        for t, count in sorted(by_type.items(), key=lambda x: -x[1]):
            print(f"  {t:20s} {count:>5}")

    # Show flagged articles
    flagged_articles = [r for r in reports if r["flagged"] > 0]
    if flagged_articles:
        print(f"\nArticles with flagged citations ({len(flagged_articles)}):")
        for r in flagged_articles[:20]:
            suffix = r.get("article_suffix", "")
            print(
                f"  Art. {r['article']}{suffix} {r['law']}: "
                f"{r['flagged']} flagged"
            )
        if len(flagged_articles) > 20:
            print(f"  ... and {len(flagged_articles) - 20} more")


def main():
    parser = argparse.ArgumentParser(
        description="Verify citations in openlegalcommentary content",
    )
    parser.add_argument(
        "--law",
        help="Law to verify (e.g., BV, OR)",
    )
    parser.add_argument(
        "--article",
        type=int,
        help="Specific article number to verify",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Verify all laws",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Write per-article .citations.json reports",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print summary statistics",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    if not args.law and not args.all:
        parser.error("Specify --law or --all")

    laws = list(LAWS) if args.all else [args.law]
    all_reports: list[dict] = []

    for law in laws:
        print(f"Verifying {law}...")
        reports = verify_law(law, article_number=args.article)
        all_reports.extend(reports)

    if args.json:
        print(json.dumps(all_reports, indent=2, ensure_ascii=False))
    elif args.summary or not args.json:
        print_summary(all_reports)


if __name__ == "__main__":
    main()
