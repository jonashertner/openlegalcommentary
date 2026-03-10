import pytest
from pathlib import Path
from scripts.validate_content import validate_article_dir, validate_content_tree


@pytest.fixture
def valid_article(tmp_path):
    art_dir = tmp_path / "or" / "art-041"
    art_dir.mkdir(parents=True)
    (art_dir / "meta.yaml").write_text(
        "law: OR\narticle: 41\ntitle: Haftung aus unerlaubter Handlung\n"
        "sr_number: '220'\nabsatz_count: 2\n"
        "fedlex_url: https://www.fedlex.admin.ch/eli/cc/27/317_321_377/de#art_41\n"
        "layers:\n  summary:\n    last_generated: '2026-03-10'\n    version: 1\n"
        "  doctrine:\n    last_generated: '2026-03-10'\n    version: 1\n"
        "  caselaw:\n    last_generated: '2026-03-10'\n    version: 1\n"
    )
    (art_dir / "summary.md").write_text("# Uebersicht\n\nPlaceholder.")
    (art_dir / "doctrine.md").write_text("# Doktrin\n\n**N. 1** Placeholder.")
    (art_dir / "caselaw.md").write_text("# Rechtsprechung\n\nPlaceholder.")
    return art_dir


@pytest.fixture
def missing_layer(tmp_path):
    art_dir = tmp_path / "or" / "art-041"
    art_dir.mkdir(parents=True)
    (art_dir / "meta.yaml").write_text(
        "law: OR\narticle: 41\ntitle: Test\nsr_number: '220'\nabsatz_count: 1\n"
        "fedlex_url: https://example.com\nlayers:\n  summary:\n    last_generated: '2026-03-10'\n    version: 1\n"
    )
    (art_dir / "summary.md").write_text("# Uebersicht\n\nTest.")
    (art_dir / "doctrine.md").write_text("# Doktrin\n\nTest.")
    return art_dir


def test_valid_article_passes(valid_article):
    assert validate_article_dir(valid_article) == []


def test_missing_layer_detected(missing_layer):
    errors = validate_article_dir(missing_layer)
    assert any("caselaw.md" in e for e in errors)


def test_missing_meta_detected(tmp_path):
    art_dir = tmp_path / "or" / "art-001"
    art_dir.mkdir(parents=True)
    (art_dir / "summary.md").write_text("Test")
    errors = validate_article_dir(art_dir)
    assert any("meta.yaml" in e for e in errors)


def test_content_tree_validation(valid_article):
    content_root = valid_article.parent.parent
    results = validate_content_tree(content_root)
    assert results["total_articles"] == 1
    assert results["errors"] == []
