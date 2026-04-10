"""Tests for the BSK citation verification helpers in scripts.verify_citations.

Focus: the three-state author matching (strict / loose / no match) introduced
in Phase 1a to reduce false positives in the audit tool. Prior to this
change, the audit only checked the top-level ``authors`` list in the
per-law ref data, which falsely flagged citations against any scholar who
was known to the article via ``positions[].author`` but wasn't the primary
BSK author.
"""
from __future__ import annotations

from scripts.citation_patterns import Citation, CitationType
from scripts.verify_citations import (
    _author_matches,
    _collect_known_authors,
    _verify_bsk_citation,
)

# ── _collect_known_authors ──────────────────────────────────────────


def test_collect_known_authors_strict_only():
    primary = {"authors": ["Axel Tschentscher"], "positions": [], "controversies": []}
    strict, loose = _collect_known_authors(primary)
    assert strict == {"Axel Tschentscher"}
    assert loose == {"Axel Tschentscher"}


def test_collect_known_authors_positions_only():
    primary = {
        "authors": [],
        "positions": [
            {"author": "Biaggini", "n": "N 3"},
            {"author": "Aubert/Mahon", "n": "N 8"},
        ],
    }
    strict, loose = _collect_known_authors(primary)
    assert strict == set()
    assert loose == {"Biaggini", "Aubert/Mahon"}


def test_collect_known_authors_strict_plus_positions():
    primary = {
        "authors": ["Axel Tschentscher"],
        "positions": [
            {"author": "Tschentscher"},
            {"author": "Biaggini"},
            {"author": "SG-Komm. BV-Gerber Jenni"},
        ],
    }
    strict, loose = _collect_known_authors(primary)
    assert strict == {"Axel Tschentscher"}
    assert loose == {"Axel Tschentscher", "Tschentscher", "Biaggini", "SG-Komm. BV-Gerber Jenni"}
    # strict is a subset of loose
    assert strict <= loose


def test_collect_known_authors_from_controversies():
    primary = {
        "authors": ["Waldmann"],
        "controversies": [
            {
                "topic": "Interpretation",
                "positions": {
                    "Aubert/Mahon": "supports",
                    "Biaggini": "dissents",
                },
            }
        ],
    }
    strict, loose = _collect_known_authors(primary)
    assert strict == {"Waldmann"}
    assert "Aubert/Mahon" in loose
    assert "Biaggini" in loose


def test_collect_known_authors_handles_missing_fields():
    primary = {}
    strict, loose = _collect_known_authors(primary)
    assert strict == set()
    assert loose == set()


def test_collect_known_authors_skips_empty_entries():
    primary = {
        "authors": ["Waldmann", "", None],
        "positions": [
            {"author": ""},
            {"author": None},
            {"author": "Biaggini"},
        ],
    }
    strict, loose = _collect_known_authors(primary)
    assert strict == {"Waldmann"}
    assert loose == {"Waldmann", "Biaggini"}


# ── _author_matches ─────────────────────────────────────────────────


def test_author_matches_exact():
    assert _author_matches("Tschentscher", {"Tschentscher"})


def test_author_matches_case_insensitive():
    assert _author_matches("tschentscher", {"Tschentscher"})
    assert _author_matches("Tschentscher", {"TSCHENTSCHER"})


def test_author_matches_substring_cited_shorter():
    # Cited "Kessler", ref data has "Martin Kessler"
    assert _author_matches("Kessler", {"Martin Kessler"})


def test_author_matches_substring_cited_longer():
    # Cited "Axel Tschentscher", ref data only has "Tschentscher"
    assert _author_matches("Axel Tschentscher", {"Tschentscher"})


def test_author_matches_no_match():
    assert not _author_matches("Zorro", {"Kessler", "Tschentscher"})


def test_author_matches_empty_cited():
    assert not _author_matches("", {"Kessler"})


def test_author_matches_empty_known():
    assert not _author_matches("Kessler", set())


# ── _verify_bsk_citation ────────────────────────────────────────────


def _bsk_citation(author: str, article: str = "8") -> Citation:
    return Citation(
        type=CitationType.BSK,
        raw=f"{author}, BSK BV, Art. {article}",
        reference=f"{author}, BSK BV, Art. {article}",
        details={"author": author, "law": "BV", "article": article, "randziffer": None},
    )


def test_verify_bsk_strict_match():
    refs = {
        "8": {
            "primary": {
                "authors": ["Waldmann"],
                "positions": [{"author": "Waldmann"}, {"author": "Kiener"}],
            }
        }
    }
    citation = _verify_bsk_citation(_bsk_citation("Waldmann"), refs, "8")
    assert citation.verified is True
    assert "strict" in citation.verification_note.lower()


def test_verify_bsk_loose_match_via_positions():
    """Regression test for the Phase 1a fix: a citation against an author
    who appears in ``positions[].author`` but not in the top-level
    ``authors`` list should now match loose, not fail.
    """
    refs = {
        "67": {
            "primary": {
                "authors": ["Axel Tschentscher"],
                "positions": [
                    {"author": "Tschentscher"},
                    {"author": "Biaggini"},
                ],
            }
        }
    }
    citation = _verify_bsk_citation(_bsk_citation("Biaggini", "67"), refs, "67")
    assert citation.verified is True
    assert "loose" in citation.verification_note.lower()


def test_verify_bsk_loose_match_via_controversies():
    refs = {
        "8": {
            "primary": {
                "authors": ["Waldmann"],
                "controversies": [
                    {
                        "topic": "Anyone's guess",
                        "positions": {"Kälin/Caroni": "yes", "Biaggini": "no"},
                    }
                ],
            }
        }
    }
    citation = _verify_bsk_citation(_bsk_citation("Kälin/Caroni"), refs, "8")
    assert citation.verified is True


def test_verify_bsk_no_match():
    refs = {
        "8": {
            "primary": {
                "authors": ["Waldmann"],
                "positions": [{"author": "Kiener"}],
            }
        }
    }
    citation = _verify_bsk_citation(_bsk_citation("Zorro"), refs, "8")
    assert citation.verified is False
    assert "Zorro" in citation.verification_note


def test_verify_bsk_no_ref_data_for_article():
    refs = {}
    citation = _verify_bsk_citation(_bsk_citation("Waldmann", "999"), refs, "999")
    assert citation.verified is None
    assert "No BSK ref data" in citation.verification_note


def test_verify_bsk_no_author_in_citation():
    refs = {
        "8": {
            "primary": {
                "authors": ["Waldmann"],
                "positions": [{"author": "Kiener"}],
            }
        }
    }
    citation = _verify_bsk_citation(_bsk_citation(""), refs, "8")
    assert citation.verified is None
    assert "No author" in citation.verification_note
