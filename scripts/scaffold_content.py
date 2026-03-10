"""Scaffold content directories for articles."""
from __future__ import annotations
from pathlib import Path
from scripts.fetch_articles import article_dir_name
from scripts.schema import ArticleMeta, SR_NUMBERS, LAW_ELI_PATHS


def scaffold_article(content_root, law, number, suffix, title, absatz_count=1, lexfind_id=None, lexfind_url="", in_force_since=""):
    dir_name = article_dir_name(number, suffix)
    art_dir = content_root / law.lower() / dir_name
    art_dir.mkdir(parents=True, exist_ok=True)
    sr = SR_NUMBERS.get(law, "")
    eli_path = LAW_ELI_PATHS.get(law, "")
    fedlex_url = f"https://www.fedlex.admin.ch/eli/cc/{eli_path}/de#art_{number}{suffix}"
    title = title or f"Art. {number}{suffix} {law}"
    meta_path = art_dir / "meta.yaml"
    if not meta_path.exists():
        meta = ArticleMeta(
            law=law, article=number, article_suffix=suffix, title=title,
            sr_number=sr, absatz_count=absatz_count, fedlex_url=fedlex_url,
            lexfind_id=lexfind_id, lexfind_url=lexfind_url, in_force_since=in_force_since,
            layers={},
        )
        meta_path.write_text(meta.to_yaml())
    placeholders = {
        "summary.md": f"# Uebersicht\n\nArt. {number}{suffix} {law} — {title}\n",
        "doctrine.md": f"# Doktrin\n\nArt. {number}{suffix} {law} — {title}\n",
        "caselaw.md": f"# Rechtsprechung\n\nArt. {number}{suffix} {law} — {title}\n",
    }
    for filename, content in placeholders.items():
        fp = art_dir / filename
        if not fp.exists():
            fp.write_text(content)
    return art_dir


def scaffold_law(content_root, law, articles):
    for article in articles:
        scaffold_article(content_root, law, article["number"], article.get("suffix", ""), article.get("title", ""))


if __name__ == "__main__":
    import asyncio
    import json
    from scripts.fetch_articles import fetch_all_laws
    content_root = Path("content")
    cache_path = Path("scripts/article_lists.json")
    if cache_path.exists():
        print("Using cached article lists...")
        data = json.loads(cache_path.read_text())
        for law, info in data.items():
            print(f"Scaffolding {law} ({info['article_count']} articles)...")
            scaffold_law(content_root, law, info["articles"])
    else:
        print("Fetching article lists from opencaselaw...")
        results = asyncio.run(fetch_all_laws())
        for law, articles in results.items():
            print(f"Scaffolding {law} ({len(articles)} articles)...")
            scaffold_law(content_root, law, articles)
    print("Done.")
