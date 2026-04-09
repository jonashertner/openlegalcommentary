"""Tests for scripts/discover_botschaften.py — parliament API registry builder."""
from __future__ import annotations

from scripts.discover_botschaften import (
    SEED_AFFAIRS,
    extract_affair_data,
    normalize_bbl_ref,
)


def test_seed_affairs_has_all_laws():
    expected_laws = {"BV", "ZGB", "OR", "ZPO", "StGB", "StPO", "SchKG", "VwVG", "BGFA"}
    assert set(SEED_AFFAIRS.keys()) == expected_laws


def test_seed_affairs_values_are_nonempty():
    for law, ids in SEED_AFFAIRS.items():
        assert len(ids) > 0, f"{law} has no seed affair IDs"
        for aid in ids:
            assert aid.isdigit(), f"{law} has non-numeric affair ID: {aid}"


def test_normalize_bbl_ref_modern():
    assert normalize_bbl_ref("BBl 2017 399") == "bbl-2017-399"


def test_normalize_bbl_ref_old_format():
    assert normalize_bbl_ref("BBl 1999 IV 4462") == "bbl-1999-IV-4462"


def test_normalize_bbl_ref_with_extra_spaces():
    assert normalize_bbl_ref("BBl  1999  6013") == "bbl-1999-6013"


def test_extract_affair_data_minimal():
    """Test extraction from a minimal affair JSON structure."""
    affair_json = {
        "id": 19990027,
        "title": "Freizügigkeit der Anwältinnen und Anwälte. Bundesgesetz",
        "shortId": "99.027",
        "affairType": {"abbreviation": "BRG", "id": 1, "name": "Geschäft des Bundesrates"},
        "state": {"id": 229, "name": "Erledigt"},
        "drafts": [
            {
                "references": [
                    {
                        "title": "Botschaft vom 28. April 1999 zum BGFA",
                        "publication": {
                            "source": "BBl 1999 6013",
                            "url": "http://www.admin.ch/opc/de/federal-gazette/1999/6013.pdf",
                            "year": "1999",
                            "page": "6013",
                            "type": {"shortName": "BBl"},
                        },
                        "date": "/Date(925336800000+0200)/",
                        "type": {"id": 1},
                    },
                ],
                "consultation": {
                    "resolutions": [
                        {
                            "council": {"name": "Nationalrat"},
                            "date": "1999-09-01T00:00:00Z",
                            "text": "Beschluss abweichend vom Entwurf",
                        },
                    ],
                },
                "preConsultations": [],
                "links": [],
                "texts": [{"type": {"id": 2}, "value": "Botschaft zum BGFA"}],
            },
        ],
        "relatedAffairs": [],
    }
    result = extract_affair_data(affair_json)
    assert result["id"] == "19990027"
    assert result["short_id"] == "99.027"
    assert len(result["botschaften"]) == 1
    assert result["botschaften"][0]["bbl_ref"] == "BBl 1999 6013"
    assert result["botschaften"][0]["bbl_ref_normalized"] == "bbl-1999-6013"
    assert "6013.pdf" in result["botschaften"][0]["pdf_url"]
    assert len(result["resolutions"]) == 1
    assert result["resolutions"][0]["council"] == "Nationalrat"
