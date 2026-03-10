import pytest
from scripts.schema import ArticleMeta, LayerMeta


def test_valid_meta():
    meta = ArticleMeta(
        law="OR",
        article=41,
        title="Haftung aus unerlaubter Handlung",
        sr_number="220",
        absatz_count=2,
        fedlex_url="https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de#art_41",
        layers={
            "summary": LayerMeta(last_generated="2026-03-10", version=1, quality_score=0.94),
            "doctrine": LayerMeta(last_generated="2026-03-10", version=1, quality_score=0.96),
            "caselaw": LayerMeta(last_generated="2026-03-10", version=1, quality_score=0.92),
        },
    )
    assert meta.law == "OR"
    assert meta.article == 41
    assert meta.layers["summary"].quality_score == 0.94


def test_invalid_law_rejected():
    with pytest.raises(ValueError):
        ArticleMeta(law="INVALID", article=1, title="Test", sr_number="999", absatz_count=1, fedlex_url="https://example.com", layers={})


def test_quality_score_bounds():
    with pytest.raises(ValueError):
        LayerMeta(last_generated="2026-03-10", version=1, quality_score=1.5)


def test_article_number_positive():
    with pytest.raises(ValueError):
        ArticleMeta(law="OR", article=0, title="Test", sr_number="220", absatz_count=1, fedlex_url="https://example.com", layers={})


def test_meta_to_yaml_roundtrip():
    meta = ArticleMeta(
        law="BV", article=1, title="Schweizerische Eidgenossenschaft", sr_number="101",
        absatz_count=1, fedlex_url="https://www.fedlex.admin.ch/eli/cc/1999/404/de#art_1",
        layers={"summary": LayerMeta(last_generated="2026-03-10", version=1)},
    )
    yaml_str = meta.to_yaml()
    loaded = ArticleMeta.from_yaml(yaml_str)
    assert loaded == meta
