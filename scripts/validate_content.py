"""Validate the content/ directory structure and metadata."""
from __future__ import annotations
from pathlib import Path
from scripts.schema import ArticleMeta, LAWS

REQUIRED_LAYERS = ("summary.md", "doctrine.md", "caselaw.md")
LAW_DIRS = {law.lower(): law for law in LAWS}


def validate_article_dir(article_dir: Path) -> list[str]:
    errors: list[str] = []
    prefix = f"{article_dir.parent.name}/{article_dir.name}"
    meta_path = article_dir / "meta.yaml"
    if not meta_path.exists():
        errors.append(f"{prefix}: missing meta.yaml")
        return errors
    try:
        meta = ArticleMeta.from_yaml(meta_path.read_text())
    except Exception as e:
        errors.append(f"{prefix}: invalid meta.yaml — {e}")
        return errors
    for layer_file in REQUIRED_LAYERS:
        if not (article_dir / layer_file).exists():
            errors.append(f"{prefix}: missing {layer_file}")
    for layer_name in meta.layers:
        if not (article_dir / f"{layer_name}.md").exists():
            errors.append(f"{prefix}: meta declares '{layer_name}' but {layer_name}.md missing")
    law_dir = article_dir.parent.name
    if law_dir in LAW_DIRS and LAW_DIRS[law_dir] != meta.law:
        errors.append(f"{prefix}: directory under '{law_dir}/' but meta says law='{meta.law}'")
    return errors


def validate_content_tree(content_root: Path) -> dict:
    all_errors: list[str] = []
    total = 0
    for law_dir in sorted(content_root.iterdir()):
        if not law_dir.is_dir() or law_dir.name.startswith("."):
            continue
        for art_dir in sorted(law_dir.iterdir()):
            if not art_dir.is_dir() or not art_dir.name.startswith("art-"):
                continue
            total += 1
            all_errors.extend(validate_article_dir(art_dir))
    return {"total_articles": total, "errors": all_errors, "valid": len(all_errors) == 0}


if __name__ == "__main__":
    import sys
    content_path = Path("content")
    if not content_path.exists():
        print("No content/ directory found.")
        sys.exit(1)
    results = validate_content_tree(content_path)
    print(f"Validated {results['total_articles']} articles.")
    if results["errors"]:
        print(f"\n{len(results['errors'])} errors found:\n")
        for e in results["errors"]:
            print(f"  x {e}")
        sys.exit(1)
    else:
        print("All valid.")
