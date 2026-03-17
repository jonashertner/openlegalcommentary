"""Export content to HuggingFace dataset format (JSON Lines)."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

CONTENT_ROOT = Path(__file__).resolve().parent.parent / "content"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

LAWS = ("BV", "ZGB", "OR", "ZPO", "StGB", "StPO", "SchKG", "VwVG")


def read_if_exists(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def export_article(law: str, art_dir: Path) -> dict | None:
    """Export a single article to a dataset record."""
    meta_path = art_dir / "meta.yaml"
    if not meta_path.exists():
        return None

    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
    if not meta:
        return None

    summary = read_if_exists(art_dir / "summary.md")
    doctrine = read_if_exists(art_dir / "doctrine.md")
    caselaw = read_if_exists(art_dir / "caselaw.md")

    # Skip placeholder-only articles (scaffolded placeholders have ~3 short lines)
    def has_real_content(text: str) -> bool:
        lines = [line for line in text.strip().splitlines() if line.strip()]
        # keep in sync with site/src/lib/content.ts:isPlaceholder()
        return len(lines) > 3 or (
            len(lines) > 0 and sum(len(line) for line in lines) > 200
        )

    if not any(has_real_content(t) for t in (summary, doctrine, caselaw)):
        return None

    record = {
        "law": meta.get("law", law),
        "article": meta.get("article"),
        "article_suffix": meta.get("article_suffix", ""),
        "title": meta.get("title", ""),
        "sr_number": meta.get("sr_number", ""),
        "summary_de": summary,
        "doctrine_de": doctrine,
        "caselaw_de": caselaw,
        "summary_fr": read_if_exists(art_dir / "summary.fr.md"),
        "doctrine_fr": read_if_exists(art_dir / "doctrine.fr.md"),
        "caselaw_fr": read_if_exists(art_dir / "caselaw.fr.md"),
        "summary_it": read_if_exists(art_dir / "summary.it.md"),
        "doctrine_it": read_if_exists(art_dir / "doctrine.it.md"),
        "caselaw_it": read_if_exists(art_dir / "caselaw.it.md"),
        "summary_en": read_if_exists(art_dir / "summary.en.md"),
        "doctrine_en": read_if_exists(art_dir / "doctrine.en.md"),
        "caselaw_en": read_if_exists(art_dir / "caselaw.en.md"),
        "fedlex_url": meta.get("fedlex_url", ""),
        "in_force_since": meta.get("in_force_since", ""),
    }

    # Add layer metadata
    layers = meta.get("layers", {})
    for layer_name in ("summary", "doctrine", "caselaw"):
        layer_meta = layers.get(layer_name, {})
        record[f"{layer_name}_version"] = layer_meta.get("version", 0)
        record[f"{layer_name}_last_generated"] = layer_meta.get("last_generated", "")
        record[f"{layer_name}_quality_score"] = layer_meta.get("quality_score")

    return record


def export_all() -> None:
    """Export all articles to JSONL files, one per law."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total = 0

    for law in LAWS:
        law_dir = CONTENT_ROOT / law.lower()
        if not law_dir.exists():
            continue

        records = []
        art_dirs = sorted(
            [d for d in law_dir.iterdir() if d.is_dir() and d.name.startswith("art-")]
        )

        for art_dir in art_dirs:
            record = export_article(law, art_dir)
            if record:
                records.append(record)

        if records:
            output_path = OUTPUT_DIR / f"{law.lower()}.jsonl"
            with open(output_path, "w", encoding="utf-8") as f:
                for record in records:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"  {law}: {len(records)} articles exported to {output_path.name}")
            total += len(records)

    # Write dataset card
    card_path = OUTPUT_DIR / "README.md"
    card_path.write_text(
        f"""---
license: cc-by-sa-4.0
language:
  - de
  - fr
  - it
  - en
tags:
  - legal
  - swiss-law
  - commentary
  - multilingual
size_categories:
  - 1K<n<10K
---

# Swiss Law Commentary Dataset

Open-access, AI-generated legal commentary on 8 Swiss federal laws.

- **Source:** [openlegalcommentary.ch](https://openlegalcommentary.ch)
- **Laws:** BV, ZGB, OR, ZPO, StGB, StPO, SchKG, VwVG
- **Layers:** Summary (B1 level), Doctrine (academic), Case Law (BGE digest)
- **Languages:** DE, FR, IT, EN
- **Articles exported:** {total}
- **License:** CC BY-SA 4.0

Built with ♥ by [Jonas Hertner](https://jonashertner.com)

## Files

One JSONL file per law (e.g., `or.jsonl`, `zgb.jsonl`).

## Schema

| Field | Type | Description |
|-------|------|-------------|
| `law` | string | Law abbreviation (e.g., "OR") |
| `article` | int | Article number |
| `article_suffix` | string | Suffix (e.g., "a", "bis") |
| `title` | string | Article title |
| `sr_number` | string | SR number |
| `summary_de` | string | German summary (Markdown) |
| `doctrine_de` | string | German doctrine (Markdown) |
| `caselaw_de` | string | German case law digest (Markdown) |
| `summary_fr` | string | French summary |
| `doctrine_fr` | string | French doctrine |
| `caselaw_fr` | string | French case law |
| `summary_it` | string | Italian summary |
| `doctrine_it` | string | Italian doctrine |
| `caselaw_it` | string | Italian case law |
| `summary_en` | string | English summary |
| `doctrine_en` | string | English doctrine |
| `caselaw_en` | string | English case law |
| `fedlex_url` | string | Fedlex URL |
| `in_force_since` | string | In force since date |
""",
        encoding="utf-8",
    )

    print(f"\nTotal: {total} articles exported")


if __name__ == "__main__":
    export_all()
