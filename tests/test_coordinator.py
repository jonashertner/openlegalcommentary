"""Tests for the coordinator — decision mapping and pipeline orchestration."""
from __future__ import annotations

from agents.coordinator import (
    ArticleRef,
    map_decisions_to_articles,
    parse_decision_list,
)


def test_parse_decision_list():
    text = """1. **BGE 130 III 182** - Haftung aus unerlaubter Handlung
   Court: BGer, Date: 2004-02-10
   Laws: OR Art. 41, OR Art. 42

2. **BGE 133 III 323** - Kausalzusammenhang
   Court: BGer, Date: 2007-05-15
   Laws: OR Art. 41, OR Art. 43"""

    decisions = parse_decision_list(text)
    assert len(decisions) >= 2
    assert decisions[0]["reference"] == "BGE 130 III 182"


def test_map_decisions_to_articles():
    decisions = [
        {
            "reference": "BGE 130 III 182",
            "articles": [
                {"law": "OR", "article": 41},
                {"law": "OR", "article": 42},
            ],
        },
        {
            "reference": "BGE 140 III 86",
            "articles": [
                {"law": "OR", "article": 41},
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
