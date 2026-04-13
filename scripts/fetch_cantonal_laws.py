"""Fetch cantonal law texts from opencaselaw and save as per-law JSON."""

import json
import re
import sys
from datetime import date
from pathlib import Path

CANTONAL_DIR = Path(__file__).parent / "cantonal"

# Canton → constitution search config
CANTON_KV_CONFIG = {
    "ZH": {"language": "de", "query": "Verfassung des Kantons Zürich"},
    "BE": {"language": "de", "query": "Verfassung des Kantons Bern"},
    "LU": {"language": "de", "query": "Verfassung des Kantons Luzern"},
    "UR": {"language": "de", "query": "Verfassung des Kantons Uri"},
    "SZ": {"language": "de", "query": "Verfassung des Kantons Schwyz"},
    "OW": {"language": "de", "query": "Verfassung des Kantons Obwalden"},
    "NW": {"language": "de", "query": "Verfassung des Kantons Nidwalden"},
    "GL": {"language": "de", "query": "Verfassung des Kantons Glarus"},
    "ZG": {"language": "de", "query": "Verfassung des Kantons Zug"},
    "FR": {"language": "fr", "query": "Constitution du canton de Fribourg"},
    "SO": {"language": "de", "query": "Verfassung des Kantons Solothurn"},
    "BS": {"language": "de", "query": "Verfassung des Kantons Basel-Stadt"},
    "BL": {"language": "de", "query": "Verfassung des Kantons Basel-Landschaft"},
    "SH": {"language": "de", "query": "Verfassung des Kantons Schaffhausen"},
    "AR": {"language": "de", "query": "Verfassung des Kantons Appenzell Ausserrhoden"},
    "AI": {"language": "de", "query": "Verfassung des Kantons Appenzell Innerrhoden"},
    "SG": {"language": "de", "query": "Verfassung des Kantons St. Gallen"},
    "GR": {"language": "de", "query": "Verfassung des Kantons Graubünden"},
    "AG": {"language": "de", "query": "Verfassung des Kantons Aargau"},
    "TG": {"language": "de", "query": "Verfassung des Kantons Thurgau"},
    "TI": {"language": "it", "query": "Costituzione della Repubblica e Cantone Ticino"},
    "VD": {"language": "fr", "query": "Constitution du Canton de Vaud"},
    "VS": {"language": "de", "query": "Verfassung des Kantons Wallis"},
    "NE": {"language": "fr", "query": "Constitution de la République et Canton de Neuchâtel"},
    "GE": {"language": "fr", "query": "Constitution de la République et canton de Genève"},
    "JU": {"language": "fr", "query": "Constitution de la République et Canton du Jura"},
}


def save_cantonal_law(
    canton: str,
    title: str,
    sr_number: str,
    lexfind_id: int,
    language: str,
    articles: list[dict],
    article_texts: dict[str, list[dict]],
) -> Path:
    """Save a cantonal law to its JSON file."""
    CANTONAL_DIR.mkdir(parents=True, exist_ok=True)
    slug = f"{canton.lower()}-kv"
    data = {
        "canton": canton,
        "law_key": slug,
        "sr_number": sr_number,
        "language": language,
        "title": title,
        "lexfind_id": lexfind_id,
        "fetched_at": date.today().isoformat(),
        "article_count": len(articles),
        "articles": articles,
        "article_texts": article_texts,
    }
    out_path = CANTONAL_DIR / f"{slug}.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_path


def parse_legislation_response(
    canton: str, response: dict
) -> tuple[list[dict], dict[str, list[dict]]]:
    """Parse a get_legislation API response into articles list and article_texts dict.

    The response contains an 'articles' list where each entry has:
    - article_num: str (e.g. "1", "2a", "10bis")
    - heading: str (article title/marginal note)
    - text: str (full article text)
    """
    articles_list = []
    article_texts = {}

    for art in response.get("articles", []):
        art_num_raw = art.get("article_num", "")
        heading = art.get("heading", "")
        text = art.get("text", "")

        match = re.match(r"^(\d+)([a-z]*)$", art_num_raw)
        if not match:
            continue
        num = int(match.group(1))
        suffix = match.group(2)

        articles_list.append({
            "number": num,
            "suffix": suffix,
            "raw": art_num_raw,
            "title": heading,
        })

        paragraphs = parse_article_text(text)
        article_texts[art_num_raw] = paragraphs

    return articles_list, article_texts


def parse_article_text(text: str) -> list[dict]:
    """Parse article text into paragraph structures.

    Handles numbered paragraphs (1, 2, 3...).
    Returns list of ArticleTextParagraph-shaped dicts.
    """
    if not text.strip():
        return []

    lines = text.strip().split("\n")
    paragraphs = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for numbered paragraph: starts with digit(s) followed by space
        num_match = re.match(r"^(\d+)\s+(.+)$", line)
        if num_match:
            paragraphs.append({"num": num_match.group(1), "text": num_match.group(2)})
            continue

        # Unnumbered paragraph
        paragraphs.append({"num": None, "text": line})

    if not paragraphs:
        paragraphs = [{"num": None, "text": text.strip()}]

    return paragraphs


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch cantonal laws from opencaselaw")
    parser.add_argument("--canton", help="Two-letter canton code (e.g., ZH). Omit for all.")
    parser.add_argument("--list", action="store_true", help="List available cantons")
    args = parser.parse_args()

    if args.list:
        for code, cfg in CANTON_KV_CONFIG.items():
            print(f"{code}: {cfg['query']} ({cfg['language']})")
        sys.exit(0)

    cantons = [args.canton.upper()] if args.canton else list(CANTON_KV_CONFIG.keys())
    print(f"Cantons to fetch: {', '.join(cantons)}")
    print("Use the MCP tools (search_legislation + get_legislation) to fetch each canton's KV,")
    print("then call save_cantonal_law() with the results.")
