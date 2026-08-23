"""Tests for agents/references.py — article text loading and formatting."""
from __future__ import annotations

import json
import warnings
from pathlib import Path
from unittest.mock import patch

import pytest

from agents.references import (
    COMMENTARY_SOURCES,
    _cantonal_sources_cache,
    _commentary_refs_cache,
    _prep_materials_cache,
    commentary_refs_filename,
    format_article_text,
    format_cantonal_sources,
    format_commentary_refs,
    format_preparatory_materials,
    is_cantonal_kv,
    load_article_texts,
    load_cantonal_sources,
    load_commentary_refs,
    load_preparatory_materials,
)


def test_load_article_texts(tmp_path):
    texts = {"OR": {"41": [{"text": "Wer einem andern widerrechtlich Schaden zufügt"}]}}
    texts_path = tmp_path / "article_texts.json"
    texts_path.write_text(json.dumps(texts))
    with patch("agents.references.ARTICLE_TEXTS_PATH", texts_path):
        result = load_article_texts()
        assert "OR" in result
        assert "41" in result["OR"]


def test_load_article_texts_caching(tmp_path):
    texts = {"OR": {"41": [{"text": "Test"}]}}
    texts_path = tmp_path / "article_texts.json"
    texts_path.write_text(json.dumps(texts))
    with patch("agents.references.ARTICLE_TEXTS_PATH", texts_path):
        with patch("agents.references._article_texts_cache", None):
            result1 = load_article_texts()
            result2 = load_article_texts()
            assert result1 is result2


def test_load_article_texts_missing_file():
    with patch("agents.references.ARTICLE_TEXTS_PATH", Path("/nonexistent/path.json")):
        with patch("agents.references._article_texts_cache", None):
            result = load_article_texts()
            assert result == {}


def test_format_article_text_simple(tmp_path):
    texts = {"OR": {"41": [{"text": "Wer einem andern widerrechtlich Schaden zufügt"}]}}
    texts_path = tmp_path / "article_texts.json"
    texts_path.write_text(json.dumps(texts))
    with patch("agents.references.ARTICLE_TEXTS_PATH", texts_path):
        with patch("agents.references._article_texts_cache", None):
            result = format_article_text("OR", 41, "")
            assert "widerrechtlich" in result


def test_format_article_text_with_suffix(tmp_path):
    texts = {"OR": {"6a": [{"text": "Art 6a text"}]}}
    texts_path = tmp_path / "article_texts.json"
    texts_path.write_text(json.dumps(texts))
    with patch("agents.references.ARTICLE_TEXTS_PATH", texts_path):
        with patch("agents.references._article_texts_cache", None):
            result = format_article_text("OR", 6, "a")
            assert "Art 6a text" in result


def test_format_article_text_missing():
    with patch("agents.references.ARTICLE_TEXTS_PATH", Path("/nonexistent/path.json")):
        with patch("agents.references._article_texts_cache", None):
            result = format_article_text("OR", 999, "")
            assert result == ""


def test_format_article_text_list_items(tmp_path):
    texts = {
        "OR": {"41": [{"type": "list", "items": [
            {"letter": "a", "text": "First"},
            {"letter": "b", "text": "Second"},
        ]}]},
    }
    texts_path = tmp_path / "article_texts.json"
    texts_path.write_text(json.dumps(texts))
    with patch("agents.references.ARTICLE_TEXTS_PATH", texts_path):
        with patch("agents.references._article_texts_cache", None):
            result = format_article_text("OR", 41, "")
            assert "a. First" in result
            assert "b. Second" in result


def test_format_article_text_numbered_para(tmp_path):
    texts = {"OR": {"41": [{"num": "1", "text": "Para one"}]}}
    texts_path = tmp_path / "article_texts.json"
    texts_path.write_text(json.dumps(texts))
    with patch("agents.references.ARTICLE_TEXTS_PATH", texts_path):
        with patch("agents.references._article_texts_cache", None):
            result = format_article_text("OR", 41, "")
            assert "1 Para one" in result


# --- Commentary refs tests ---


@pytest.fixture(autouse=True)
def clear_commentary_cache():
    """Clear the module-level commentary refs cache between tests."""
    _commentary_refs_cache.clear()
    yield
    _commentary_refs_cache.clear()


def _make_refs_dir(tmp_path, law, source, data):
    """Helper to write a commentary refs JSON file."""
    refs_dir = tmp_path / "commentary_refs"
    refs_dir.mkdir(exist_ok=True)
    path = refs_dir / commentary_refs_filename(law, source)
    path.write_text(json.dumps({law.upper(): data}))
    return refs_dir


def test_load_commentary_primary_refs(tmp_path):
    data = {
        "41": {"authors": ["Kessler"], "edition": "Doctrinal OR I, 7. Aufl. 2019"},
    }
    refs_dir = _make_refs_dir(tmp_path, "or", "primary", data)
    result = load_commentary_refs(refs_dir, "OR")
    assert "41" in result


def test_load_commentary_primary_missing_law(tmp_path):
    refs_dir = tmp_path / "commentary_refs"
    refs_dir.mkdir()
    result = load_commentary_refs(refs_dir, "ZGB")
    assert result == {}


def test_load_commentary_merges_primary_and_cr(tmp_path):
    refs_dir = tmp_path / "commentary_refs"
    refs_dir.mkdir()
    refs = {"OR": {"41": {"authors": ["Kessler"], "edition": "Doctrinal OR I"}}}
    cr = {"OR": {"41": {"authors": ["Thévenoz"], "edition": "CR CO I"}}}
    (refs_dir / "or_primary.json").write_text(json.dumps(refs))
    (refs_dir / "or_cr.json").write_text(json.dumps(cr))
    result = load_commentary_refs(refs_dir, "OR")
    assert "41" in result
    assert "primary" in result["41"]
    assert "cr" in result["41"]


def test_format_commentary_refs_basic(tmp_path):
    data = {
        "41": {
            "authors": ["Kessler"],
            "edition": "Doctrinal OR I, 7. Aufl. 2019",
            "randziffern_map": {"1-3": "Entstehungsgeschichte"},
            "positions": [
                {
                    "author": "Kessler", "n": "N. 12",
                    "topic": "Widerrechtlichkeit",
                    "position": "Erfolgsunrecht genügt",
                },
            ],
            "controversies": [],
            "cross_refs": [],
            "key_literature": [],
        },
    }
    refs_dir = _make_refs_dir(tmp_path, "or", "primary", data)
    result = format_commentary_refs(refs_dir, "OR", 41, "")
    assert "Kessler" in result
    assert "Doctrinal OR I" in result
    assert "N. 12" in result
    assert "Entstehungsgeschichte" in result


def test_format_commentary_refs_empty_for_uncovered_law(tmp_path):
    refs_dir = tmp_path / "commentary_refs"
    refs_dir.mkdir()
    result = format_commentary_refs(refs_dir, "VwVG", 5, "")
    assert result == ""


def test_format_commentary_refs_empty_for_unknown_article(tmp_path):
    data = {
        "41": {"authors": ["Kessler"], "edition": "Doctrinal OR I"},
    }
    refs_dir = _make_refs_dir(tmp_path, "or", "primary", data)
    result = format_commentary_refs(refs_dir, "OR", 999, "")
    assert result == ""


def test_format_commentary_refs_with_suffix(tmp_path):
    data = {"6a": {"authors": ["Author"], "edition": "Doctrinal OR I"}}
    refs_dir = _make_refs_dir(tmp_path, "or", "primary", data)
    result = format_commentary_refs(refs_dir, "OR", 6, "a")
    assert "Author" in result


def test_format_commentary_refs_primary_and_cr(tmp_path):
    refs_dir = tmp_path / "commentary_refs"
    refs_dir.mkdir()
    refs = {"OR": {"41": {
        "authors": ["Kessler"], "edition": "Doctrinal OR I",
        "positions": [
            {"author": "Kessler", "n": "N. 5", "topic": "T", "position": "P"},
        ],
    }}}
    cr = {"OR": {"41": {
        "authors": ["Thévenoz"], "edition": "CR CO I",
        "positions": [
            {"author": "Thévenoz", "n": "N. 3", "topic": "T", "position": "P2"},
        ],
    }}}
    (refs_dir / "or_primary.json").write_text(json.dumps(refs))
    (refs_dir / "or_cr.json").write_text(json.dumps(cr))
    result = format_commentary_refs(refs_dir, "OR", 41, "")
    assert "Doctrinal" in result
    assert "CR" in result
    assert "Kessler" in result
    assert "Thévenoz" in result


# --- Preparatory materials tests ---


@pytest.fixture(autouse=True)
def clear_prep_cache():
    """Clear the module-level preparatory materials cache between tests."""
    _prep_materials_cache.clear()
    yield
    _prep_materials_cache.clear()


def _make_prep_materials(tmp_path, law, articles_data):
    """Helper to write a preparatory materials JSON file."""
    prep_dir = tmp_path / "preparatory_materials"
    prep_dir.mkdir(exist_ok=True)
    path = prep_dir / f"{law.lower()}.json"
    path.write_text(json.dumps({
        "law": law.upper(),
        "sr_number": "935.61",
        "generated": "2026-04-06T14:00:00Z",
        "articles": articles_data,
    }))
    return prep_dir


def test_load_preparatory_materials_basic(tmp_path):
    articles = {
        "12": {
            "sources": [{
                "bbl_ref": "BBl 1999 6013",
                "bbl_page_refs": ["6045-6048"],
                "legislative_intent": "Art. 12 enthält einen Katalog.",
                "key_arguments": ["Numerus clausus"],
                "design_choices": [],
                "rejected_alternatives": [],
                "general_context": None,
            }],
            "parliamentary_modifications": [],
        },
    }
    prep_dir = _make_prep_materials(tmp_path, "BGFA", articles)
    with patch("agents.references.PREPARATORY_MATERIALS_ROOT", prep_dir):
        result = load_preparatory_materials("BGFA")
        assert "12" in result
        assert result["12"]["sources"][0]["bbl_ref"] == "BBl 1999 6013"


def test_load_preparatory_materials_missing_law(tmp_path):
    prep_dir = tmp_path / "preparatory_materials"
    prep_dir.mkdir()
    with patch("agents.references.PREPARATORY_MATERIALS_ROOT", prep_dir):
        result = load_preparatory_materials("ZGB")
        assert result == {}


def test_load_preparatory_materials_caching(tmp_path):
    articles = {"1": {"sources": [], "parliamentary_modifications": []}}
    prep_dir = _make_prep_materials(tmp_path, "BGFA", articles)
    with patch("agents.references.PREPARATORY_MATERIALS_ROOT", prep_dir):
        result1 = load_preparatory_materials("BGFA")
        result2 = load_preparatory_materials("BGFA")
        assert result1 is result2


def test_format_preparatory_materials_basic(tmp_path):
    articles = {
        "12": {
            "sources": [{
                "bbl_ref": "BBl 1999 6013",
                "bbl_page_refs": ["6045-6048"],
                "legislative_intent": "Art. 12 enthält einen abschliessenden Katalog.",
                "key_arguments": ["Numerus clausus", "Bundesrechtlich abschliessend"],
                "design_choices": ["Abschliessender Katalog statt Mindeststandards"],
                "rejected_alternatives": ["Selbstregulierung abgelehnt"],
                "general_context": None,
            }],
            "parliamentary_modifications": [
                {
                    "council": "Nationalrat",
                    "date": "1999-09-01",
                    "change": "Beschluss abweichend vom Entwurf",
                },
            ],
        },
    }
    prep_dir = _make_prep_materials(tmp_path, "BGFA", articles)
    with patch("agents.references.PREPARATORY_MATERIALS_ROOT", prep_dir):
        result = format_preparatory_materials("BGFA", 12, "")
        assert "BBl 1999 6013" in result
        assert "abschliessenden Katalog" in result
        assert "Numerus clausus" in result
        assert "Abschliessender Katalog" in result
        assert "Selbstregulierung" in result
        assert "Nationalrat" in result
        assert "Materialien" in result


def test_format_preparatory_materials_empty_for_unknown(tmp_path):
    prep_dir = tmp_path / "preparatory_materials"
    prep_dir.mkdir()
    with patch("agents.references.PREPARATORY_MATERIALS_ROOT", prep_dir):
        result = format_preparatory_materials("BGFA", 999, "")
        assert result == ""


def test_format_preparatory_materials_multiple_sources(tmp_path):
    articles = {
        "12": {
            "sources": [
                {
                    "bbl_ref": "BBl 1999 6013",
                    "bbl_page_refs": ["6045"],
                    "legislative_intent": "Original intent.",
                    "key_arguments": [],
                    "design_choices": [],
                    "rejected_alternatives": [],
                    "general_context": None,
                },
                {
                    "bbl_ref": "BBl 2020 1234",
                    "bbl_page_refs": ["15-16"],
                    "legislative_intent": "Amendment intent.",
                    "key_arguments": [],
                    "design_choices": [],
                    "rejected_alternatives": [],
                    "general_context": None,
                },
            ],
            "parliamentary_modifications": [],
        },
    }
    prep_dir = _make_prep_materials(tmp_path, "BGFA", articles)
    with patch("agents.references.PREPARATORY_MATERIALS_ROOT", prep_dir):
        result = format_preparatory_materials("BGFA", 12, "")
        assert "BBl 1999 6013" in result
        assert "BBl 2020 1234" in result
        assert "Original intent" in result
        assert "Amendment intent" in result


# --- Cantonal sources tests -------------------------------------------------


def test_is_cantonal_kv_recognises_canton_keys():
    assert is_cantonal_kv("sg-kv") is True
    assert is_cantonal_kv("BS-KV") is True
    assert is_cantonal_kv("zh-kv") is True


def test_is_cantonal_kv_rejects_non_kv_keys():
    assert is_cantonal_kv("BV") is False
    assert is_cantonal_kv("OR") is False
    assert is_cantonal_kv("foo-kv") is False  # length guard
    assert is_cantonal_kv("") is False


def _make_cantonal_dir(tmp_path):
    d = tmp_path / "cantonal_materials"
    d.mkdir()
    return d


def test_load_cantonal_sources_returns_none_for_federal(tmp_path):
    _cantonal_sources_cache.clear()
    with patch("agents.references.CANTONAL_MATERIALS_ROOT", _make_cantonal_dir(tmp_path)):
        assert load_cantonal_sources("BV") is None


def test_load_cantonal_sources_missing_file(tmp_path):
    _cantonal_sources_cache.clear()
    with patch("agents.references.CANTONAL_MATERIALS_ROOT", _make_cantonal_dir(tmp_path)):
        assert load_cantonal_sources("zz-kv") is None


def test_load_cantonal_sources_reads_canton_json(tmp_path):
    _cantonal_sources_cache.clear()
    d = _make_cantonal_dir(tmp_path)
    payload = {"canton": "ZH", "name": "Zürich", "kategorien": {}}
    (d / "zh.json").write_text(json.dumps(payload))
    with patch("agents.references.CANTONAL_MATERIALS_ROOT", d):
        data = load_cantonal_sources("zh-kv")
        assert data is not None
        assert data["canton"] == "ZH"


def test_format_cantonal_sources_renders_metadata_and_caveats(tmp_path):
    _cantonal_sources_cache.clear()
    d = _make_cantonal_dir(tmp_path)
    payload = {
        "canton": "ZH",
        "name": "Zürich",
        "historical_sources": {
            "kv_metadata": {
                "short_title": "KV ZH",
                "sr_number": "LS 101",
                "adoption_date": "2005-02-27",
                "in_force": "2006-01-01",
                "revision_type": "Totalrevision",
                "predecessor": "KV ZH 1869",
            },
            "verfassungsrat": {
                "body": "Verfassungsrat ZH",
                "period": "1999-2003",
                "key_publications": [
                    {"title": "Bericht des Verfassungsrats", "note": "Hauptmaterialie"},
                ],
            },
            "archives": [
                {
                    "name": "Staatsarchiv ZH",
                    "url": "https://staatsarchiv.zh.ch",
                    "note": "Bestand.",
                },
            ],
            "caveats": ["Materialien teilweise nur vor Ort einsehbar."],
        },
        "kategorien": {
            "rs": {
                "label": "Rechtsprechung",
                "sources": {
                    "rs": {"link": "https://example.zh", "bemerkung": "DB", "ab": "2010"},
                },
            },
        },
    }
    (d / "zh.json").write_text(json.dumps(payload))
    with patch("agents.references.CANTONAL_MATERIALS_ROOT", d):
        block = format_cantonal_sources("zh-kv")
    assert "KV-Metadaten" in block
    assert "Verfassungsrat ZH" in block
    assert "Staatsarchiv ZH" in block
    assert "https://example.zh" in block
    assert "Materialien teilweise nur vor Ort einsehbar." in block
    assert "Anti-Fabrikations-Regel" in block


def test_format_cantonal_sources_renders_verfassungserarbeitung_variant(tmp_path):
    """BL-style catalogs use 'verfassungserarbeitung'+'organ' instead of
    'verfassungsrat'+'body'; the drafting history must still render."""
    _cantonal_sources_cache.clear()
    d = _make_cantonal_dir(tmp_path)
    payload = {
        "canton": "BL",
        "name": "Basel-Landschaft",
        "historical_sources": {
            "verfassungserarbeitung": {
                "organ": "Verfassungskommission des Landrats",
                "period": "1976-1984",
                "key_publications": [
                    {
                        "title": "Bericht und Antrag der Verfassungskommission",
                        "note": "Hauptmaterialie",
                    },
                ],
            },
        },
    }
    (d / "bl.json").write_text(json.dumps(payload))
    with patch("agents.references.CANTONAL_MATERIALS_ROOT", d):
        block = format_cantonal_sources("bl-kv")
    assert "Verfassungserarbeitung" in block
    assert "Verfassungskommission des Landrats" in block
    assert "Bericht und Antrag der Verfassungskommission" in block


def test_format_preparatory_materials_dispatches_for_cantonal(tmp_path):
    """For cantonal KVs, dispatcher must return the source-catalog block."""
    _cantonal_sources_cache.clear()
    d = _make_cantonal_dir(tmp_path)
    (d / "zh.json").write_text(json.dumps({
        "canton": "ZH",
        "historical_sources": {"kv_metadata": {"short_title": "KV ZH"}},
    }))
    with patch("agents.references.CANTONAL_MATERIALS_ROOT", d):
        # Article-agnostic: same block for any article
        a = format_preparatory_materials("zh-kv", 1, "")
        b = format_preparatory_materials("zh-kv", 99, "a")
        assert a == b
        assert "Kantonale Quellen" in a


def test_format_cantonal_sources_returns_empty_when_missing(tmp_path):
    _cantonal_sources_cache.clear()
    with patch("agents.references.CANTONAL_MATERIALS_ROOT", _make_cantonal_dir(tmp_path)):
        assert format_cantonal_sources("zz-kv") == ""
        assert format_cantonal_sources("BV") == ""


def test_real_sg_bs_bl_catalogs_load_and_format():
    """Smoke test: the actually-shipped SG/BS/BL catalogs format without error."""
    _cantonal_sources_cache.clear()
    sg = load_cantonal_sources("sg-kv")
    bs = load_cantonal_sources("bs-kv")
    bl = load_cantonal_sources("bl-kv")
    assert sg is not None and sg["canton"] == "SG"
    assert bs is not None and bs["canton"] == "BS"
    assert bl is not None and bl["canton"] == "BL"
    sg_block = format_cantonal_sources("sg-kv")
    bs_block = format_cantonal_sources("bs-kv")
    bl_block = format_cantonal_sources("bl-kv")
    assert "Verfassungsrat des Kantons St. Gallen" in sg_block
    assert "Verfassungsrat des Kantons Basel-Stadt" in bs_block
    # BL's KV was drafted by a Verfassungskommission, not an elected Verfassungsrat
    assert "Verfassungserarbeitung" in bl_block
    assert "Verfassungskommission des Landrats" in bl_block
    assert "ratsinfo.sg.ch" in sg_block
    assert "grosserrat.bs.ch" in bs_block


# --- Regression guards for the 2026-03-22 filename divergence ---
#
# Commit 485abae9 renamed the data file and the loader's source tuple in the
# same commit, without them agreeing. load_commentary_refs() returned {} for
# five months and nothing failed, because {} is also the correct answer for a
# law that genuinely has no reference data. These tests separate the two cases.


@pytest.mark.parametrize("source", COMMENTARY_SOURCES)
def test_loader_reads_every_name_the_filename_helper_produces(tmp_path, source):
    """The naming helper and the loader must not drift apart."""
    refs_dir = _make_refs_dir(tmp_path, "bv", source, {"8": {"authors": ["Waldmann"]}})
    result = load_commentary_refs(refs_dir, "BV")
    assert "8" in result, (
        f"loader did not read {commentary_refs_filename('bv', source)}"
    )
    assert source in result["8"]


def test_loader_warns_when_data_sits_under_a_name_it_does_not_read(tmp_path):
    """The exact March 2026 failure: data present, loader blind to it."""
    refs_dir = tmp_path / "commentary_refs"
    refs_dir.mkdir()
    (refs_dir / "bv_refs.json").write_text(
        json.dumps({"BV": {"8": {"authors": ["Waldmann"]}}})
    )

    with pytest.warns(RuntimeWarning, match="bv_refs.json"):
        result = load_commentary_refs(refs_dir, "BV")

    assert result == {}


def test_loader_is_silent_when_the_law_genuinely_has_no_refs(tmp_path):
    """An empty result is legitimate for an uncovered law and must not warn."""
    refs_dir = _make_refs_dir(tmp_path, "bv", "primary", {"8": {"authors": ["W"]}})

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert load_commentary_refs(refs_dir, "ZGB") == {}


def test_doctrine_prompt_block_is_non_empty_when_refs_are_present(tmp_path):
    """End of the chain: refs on disk must reach the prompt as real text."""
    refs_dir = _make_refs_dir(
        tmp_path, "bv", "primary",
        {"8": {"authors": ["Waldmann"], "edition": "BSK BV, 1. Aufl. 2015"}},
    )
    block = format_commentary_refs(refs_dir, "BV", 8, "")
    assert block, "commentary refs on disk produced an empty prompt block"
    assert "Waldmann" in block
