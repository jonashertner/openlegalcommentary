"""Tests for the coordinator — decision mapping and pipeline orchestration."""
from __future__ import annotations

from agents.coordinator import (
    ArticleRef,
    map_decisions_to_articles,
    parse_decision_list,
)


def test_parse_decision_list_legacy_bge_format():
    """Legacy BGE format with Laws: LAW Art. N."""
    text = """1. **BGE 130 III 182** - Haftung aus unerlaubter Handlung
   Court: BGer, Date: 2004-02-10
   Laws: OR Art. 41, OR Art. 42

2. **BGE 133 III 323** - Kausalzusammenhang
   Court: BGer, Date: 2007-05-15
   Laws: OR Art. 41, OR Art. 43"""

    decisions = parse_decision_list(text)
    assert len(decisions) >= 2
    assert decisions[0]["reference"] == "BGE 130 III 182"
    # Articles extracted from "OR Art. 41" pattern
    or_41 = [a for a in decisions[0]["articles"] if a["law"] == "OR" and a["article"] == 41]
    assert len(or_41) >= 1


def test_parse_decision_list_current_bger_format():
    """Current MCP format: **N. DOCKET** followed by metadata + snippet."""
    text = """Found 2 decisions (showing 1-2):

**1. 5A_144/2026** (2026-04-01) [bger] [de]
   ID: bger_5A_144_2026
   Title: avance de frais (action en annulation)
   ...Die Beschwerde stützt sich auf Art. 8 BV und Art. 29 BV...

**2. 8C_222/2026** (2026-04-01) [bger] [de]
   ID: bger_8C_222_2026
   Title: Assurance-accidents
   ...Rügen werden gestützt auf Art. 41 OR vorgebracht..."""

    decisions = parse_decision_list(text)
    assert len(decisions) == 2
    assert decisions[0]["reference"] == "5A_144/2026"
    assert decisions[1]["reference"] == "8C_222/2026"
    # Articles extracted from "Art. N LAW" in snippet
    bv_8 = [a for a in decisions[0]["articles"] if a["law"] == "BV" and a["article"] == 8]
    assert len(bv_8) >= 1


def test_parse_decision_list_ignores_non_statute_art():
    """Art. XYZ (parcel number, redacted) should not create a spurious match."""
    text = """**1. 5A_100/2026** (2026-04-01) [bger] [de]
   ID: bger_5A_100_2026
   Title: Baubewilligung
   ...Grundstück Art. fff.________ des Grundbuchs..."""

    decisions = parse_decision_list(text)
    assert len(decisions) == 1
    # "Art. fff.______" should not match — no digits, no valid law
    assert decisions[0]["articles"] == []


def test_map_decisions_to_articles():
    decisions = [
        {
            "reference": "BGE 130 III 182",
            "articles": [
                {"law": "OR", "article": 41, "suffix": ""},
                {"law": "OR", "article": 42, "suffix": ""},
            ],
        },
        {
            "reference": "BGE 140 III 86",
            "articles": [
                {"law": "OR", "article": 41, "suffix": ""},
            ],
        },
    ]

    mapping = map_decisions_to_articles(decisions)

    or_41 = [r for r in mapping if r.law == "OR" and r.article_number == 41]
    assert len(or_41) == 1
    assert len(or_41[0].decision_refs) == 2

    or_42 = [r for r in mapping if r.law == "OR" and r.article_number == 42]
    assert len(or_42) == 1
    assert len(or_42[0].decision_refs) == 1


def test_article_ref_dataclass():
    ref = ArticleRef(
        law="OR", article_number=41,
        article_suffix="",
        decision_refs=["BGE 130 III 182"],
    )
    assert ref.law == "OR"
    assert ref.article_number == 41
