#!/usr/bin/env python3
"""Generate a compact search index from article_lists.json"""

import json
from pathlib import Path


def slugify(law: str, number: int, suffix: str) -> str:
    """Generate a slug for an article."""
    display = f"{number}{suffix}" if suffix else str(number)
    return f"art-{display}".lower()


def generate_search_index():
    """Read article_lists.json and generate a compact search index."""
    script_dir = Path(__file__).parent
    input_file = script_dir / "article_lists.json"
    output_file = script_dir.parent / "site" / "public" / "search-index.json"

    print(f"Reading {input_file}...")
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    index = []

    for law, law_data in data.items():
        articles = law_data.get("articles", [])
        print(f"Processing {law} ({len(articles)} articles)...")

        for article in articles:
            number = article.get("number")
            suffix = article.get("suffix", "")
            title = article.get("title", "")

            display_number = f"{number}{suffix}" if suffix else str(number)
            slug = slugify(law, number, suffix)

            index.append({
                "l": law,
                "n": display_number,
                "t": title,
                "u": slug
            })

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write minified JSON (no extra whitespace)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(index, f, separators=(",", ":"), ensure_ascii=False)

    print(f"\nSearch index generated: {output_file}")
    print(f"Total entries: {len(index)}")
    print(f"File size: {output_file.stat().st_size:,} bytes")


if __name__ == "__main__":
    generate_search_index()
