"""Tests for commentary reference schema."""
from __future__ import annotations

import pytest

from scripts.commentary_schema import ArticleRef, Position, Controversy


def test_article_ref_required_fields():
    ref = ArticleRef(authors=["Kessler"], edition="BSK OR I, 7. Aufl. 2019")
    assert ref.authors == ["Kessler"]
    assert ref.edition == "BSK OR I, 7. Aufl. 2019"
    assert ref.positions == []
    assert ref.controversies == []
    assert ref.randziffern_map == {}
    assert ref.cross_refs == []
    assert ref.key_literature == []


def test_article_ref_authors_required_nonempty():
    with pytest.raises(ValueError):
        ArticleRef(authors=[], edition="BSK OR I")


def test_article_ref_edition_required():
    with pytest.raises(ValueError):
        ArticleRef(authors=["Kessler"], edition="")


def test_position_model():
    p = Position(author="Kessler", n="N. 12", topic="Widerrechtlichkeit", position="Erfolgsunrecht genügt")
    assert p.author == "Kessler"
    assert p.n == "N. 12"


def test_controversy_model():
    c = Controversy(
        topic="Organhaftung",
        positions={"Kessler (N. 30)": "lex specialis", "Huguenin": "Parallelanwendung"},
    )
    assert len(c.positions) == 2


def test_article_ref_full():
    ref = ArticleRef(
        authors=["Kessler", "Widmer Lüchinger"],
        edition="BSK OR I, 7. Aufl. 2019",
        randziffern_map={"1-3": "Entstehungsgeschichte", "4-8": "Systematik"},
        positions=[Position(author="Kessler", n="N. 12", topic="Widerrechtlichkeit", position="Erfolgsunrecht genügt")],
        controversies=[Controversy(topic="Organhaftung", positions={"A": "yes", "B": "no"})],
        cross_refs=["Art. 97 OR"],
        key_literature=["Gauch/Schluep/Schmid, OR AT, 11. Aufl. 2020"],
    )
    assert len(ref.positions) == 1
    assert len(ref.controversies) == 1
