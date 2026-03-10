
import pytest

from scripts.scaffold_content import scaffold_article, scaffold_law
from scripts.schema import ArticleMeta


@pytest.fixture
def content_root(tmp_path):
    return tmp_path / "content"


def test_scaffold_article_creates_files(content_root):
    scaffold_article(content_root, "OR", 41, "", "Haftung aus unerlaubter Handlung", 2)
    art_dir = content_root / "or" / "art-041"
    assert art_dir.exists()
    assert (art_dir / "meta.yaml").exists()
    assert (art_dir / "summary.md").exists()
    assert (art_dir / "doctrine.md").exists()
    assert (art_dir / "caselaw.md").exists()
    meta = ArticleMeta.from_yaml((art_dir / "meta.yaml").read_text())
    assert meta.law == "OR"
    assert meta.article == 41


def test_scaffold_article_does_not_overwrite(content_root):
    scaffold_article(content_root, "OR", 41, "", "Title", 1)
    (content_root / "or" / "art-041" / "doctrine.md").write_text("Custom content")
    scaffold_article(content_root, "OR", 41, "", "Title", 1)
    assert (content_root / "or" / "art-041" / "doctrine.md").read_text() == "Custom content"


def test_scaffold_law(content_root):
    articles = [
        {"number": 1, "suffix": "", "title": "Entstehung"},
        {"number": 2, "suffix": "", "title": "Vertrag"},
    ]
    scaffold_law(content_root, "OR", articles)
    assert (content_root / "or" / "art-001" / "meta.yaml").exists()
    assert (content_root / "or" / "art-002" / "meta.yaml").exists()
