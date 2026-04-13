"""Fetch cantonal law texts from opencaselaw and save as per-law JSON.

Usage:
    uv run python -m scripts.fetch_cantonal_laws             # fetch all 26 KVs
    uv run python -m scripts.fetch_cantonal_laws --canton ZH  # fetch one canton
    uv run python -m scripts.fetch_cantonal_laws --list       # list cantons
"""
from __future__ import annotations

import asyncio
import json
import re
import sys
from datetime import date
from pathlib import Path

from agents.mcp_client import mcp_call

CANTONAL_DIR = Path(__file__).parent / "cantonal"
MCP_BASE = "https://mcp.opencaselaw.ch"

# Canton → KV config with LexFind IDs from search_legislation results
CANTON_KV_CONFIG: dict[str, dict] = {
    "ZH": {"language": "de", "lexfind_id": 21736, "title": "Verfassung des Kantons Zürich"},
    "BE": {"language": "de", "lexfind_id": 23149, "title": "Verfassung des Kantons Bern"},
    "LU": {"language": "de", "lexfind_id": 10797, "title": "Verfassung des Kantons Luzern"},
    "UR": {"language": "de", "lexfind_id": 17919, "title": "Verfassung des Kantons Uri"},
    "SZ": {"language": "de", "lexfind_id": 17525, "title": "Verfassung des Kantons Schwyz"},
    "OW": {"language": "de", "lexfind_id": 12769, "title": "Verfassung des Kantons Obwalden"},
    "NW": {"language": "de", "lexfind_id": 13358, "title": "Verfassung des Kantons Nidwalden"},
    "GL": {"language": "de", "lexfind_id": 7326, "title": "Verfassung des Kantons Glarus"},
    "ZG": {"language": "de", "lexfind_id": 19965, "title": "Verfassung des Kantons Zug"},
    "FR": {"language": "fr", "lexfind_id": 5674, "title": "Constitution du canton de Fribourg"},
    "SO": {"language": "de", "lexfind_id": 15261, "title": "Verfassung des Kantons Solothurn"},
    "BS": {"language": "de", "lexfind_id": 3293, "title": "Verfassung des Kantons Basel-Stadt"},
    "BL": {"language": "de", "lexfind_id": 3696, "title": "Verfassung des Kantons Basel-Landschaft"},
    "SH": {"language": "de", "lexfind_id": 14100, "title": "Verfassung des Kantons Schaffhausen"},
    "AR": {"language": "de", "lexfind_id": 2368, "title": "Verfassung des Kantons Appenzell A.Rh."},
    "AI": {"language": "de", "lexfind_id": 1209, "title": "Verfassung für den Eidgenössischen Stand Appenzell I. Rh."},
    "SG": {"language": "de", "lexfind_id": 14551, "title": "Verfassung des Kantons St.Gallen"},
    "GR": {"language": "de", "lexfind_id": 9576, "title": "Verfassung des Kantons Graubünden"},
    "AG": {"language": "de", "lexfind_id": 25, "title": "Verfassung des Kantons Aargau"},
    "TG": {"language": "de", "lexfind_id": 17412, "title": "Verfassung des Kantons Thurgau"},
    "TI": {"language": "it", "lexfind_id": 20038, "title": "Costituzione della Repubblica e Cantone Ticino"},
    "VD": {"language": "fr", "lexfind_id": 18476, "title": "Constitution du Canton de Vaud"},
    "VS": {"language": "de", "lexfind_id": 19030, "title": "Verfassung des Kantons Wallis"},
    "NE": {"language": "fr", "lexfind_id": 9978, "title": "Constitution de la République et Canton de Neuchâtel"},
    "GE": {"language": "fr", "lexfind_id": 31535, "title": "Constitution de la République et canton de Genève"},
    "JU": {"language": "fr", "lexfind_id": 8442, "title": "Constitution de la République et Canton du Jura"},
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


def parse_article_list_response(text: str) -> list[dict]:
    """Parse the get_law article list response into structured data.

    The response lists articles as:
    - Art. 1 Heading
    - Art. 2 Heading
    """
    articles: list[dict] = []
    seen: set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("- Art.") and not line.startswith("- §"):
            continue
        # Skip range references like "Art. 1–10"
        if re.match(r"^- (?:Art\.|§)\s+\d+\s*(?:–|—|-)\s*\d+", line):
            continue
        match = re.match(r"^- (?:Art\.|§)\s+(\d+)\s*([a-z]*)\s*(.*)", line)
        if not match:
            continue
        number = int(match.group(1))
        suffix = match.group(2).strip()
        rest = match.group(3).strip()
        raw = f"{number}{suffix}"
        if raw in seen:
            continue
        seen.add(raw)
        # Clean title: strip amendment notes and footnotes
        title = _extract_title(rest)
        articles.append({"number": number, "suffix": suffix, "raw": raw, "title": title})
    articles.sort(key=lambda a: (a["number"], a["suffix"]))
    return articles


def _extract_title(text: str) -> str:
    """Extract article title, skipping amendment notes."""
    if not text:
        return ""
    amendment_starts = (
        "Eingefügt", "Fassung gemäss", "Aufgehoben", "Angenommen",
        "in der Fassung", "In Kraft", "Berichtigt",
        "Introduit", "Adopté", "Abrogé", "Accepté",
        "Introdotto", "Accettato", "Abrogato",
    )
    for prefix in amendment_starts:
        if text.startswith(prefix):
            return ""
    for marker in amendment_starts:
        idx = text.find(marker)
        if idx > 0:
            text = text[:idx].strip()
            break
    text = re.sub(r"\s*\*?\s*Mit Übergangsbestimmung\.?\s*\*?\s*", "", text).strip()
    text = re.sub(r"\d*\*\s*$", "", text).strip()
    return text


def parse_single_article_response(text: str) -> list[dict]:
    """Parse a get_law single-article response into paragraph structures.

    The response looks like:
    ### § N or ### Art. N
    1 Text of paragraph 1.
    2 Text of paragraph 2.
    """
    # Find the article body after the ### header
    lines = text.splitlines()
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("### "):
            body_start = i + 1
            break
    body = "\n".join(lines[body_start:]).strip()
    return parse_article_text(body)


def parse_article_text(text: str) -> list[dict]:
    """Parse article text into paragraph structures.

    Handles numbered paragraphs (1, 2, 3...) and unnumbered text.
    Returns list of ArticleTextParagraph-shaped dicts.
    """
    if not text.strip():
        return []

    # Join lines that were broken by PDF layout (soft hyphens)
    text = re.sub(r"­\s*\n", "", text)  # soft hyphen + newline
    text = re.sub(r"-\s*\n(?=[a-zà-ü])", "", text)  # hard hyphen + newline before lowercase

    lines = text.strip().split("\n")
    paragraphs: list[dict] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for numbered paragraph: starts with digit(s) followed by space
        num_match = re.match(r"^(\d+)\s+(.+)$", line)
        if num_match:
            para_num = num_match.group(1)
            # Only treat as paragraph number if it's a reasonable Absatz number (1-20ish)
            if int(para_num) <= 20:
                paragraphs.append({"num": para_num, "text": num_match.group(2)})
                continue

        # Unnumbered paragraph — append to previous if it looks like continuation
        if paragraphs and not line[0].isupper() and not line.startswith("a.") and not line.startswith("a)"):
            # Continuation of previous paragraph
            prev = paragraphs[-1]
            prev["text"] = prev["text"] + " " + line
        else:
            paragraphs.append({"num": None, "text": line})

    if not paragraphs:
        paragraphs = [{"num": None, "text": text.strip()}]

    return paragraphs


async def fetch_cantonal_kv(canton: str, concurrency: int = 5) -> Path:
    """Fetch a single canton's KV from opencaselaw and save as JSON.

    Two-step approach:
    1. get_law(canton, sr_number) → article list (all articles)
    2. get_law(canton, sr_number, article=N) → text per article (batched)
    """
    cfg = CANTON_KV_CONFIG[canton]
    sr = cfg.get("sr_number", "")
    print(f"  Fetching {canton} KV...")

    # Step 1: Get SR number from get_legislation metadata
    if not sr:
        meta_text = await mcp_call(
            MCP_BASE, "get_legislation",
            {"lexfind_id": cfg["lexfind_id"], "language": cfg["language"]},
            timeout=120.0,
        )
        sr_match = re.search(r"\*\*SR Number:\*\*\s*(.+)", meta_text)
        sr = sr_match.group(1).strip() if sr_match else ""
        cfg["sr_number"] = sr

    # Step 2: Get article list
    list_text = await mcp_call(
        MCP_BASE, "get_law",
        {"canton": canton, "sr_number": sr, "language": cfg["language"]},
        timeout=60.0,
    )
    articles = parse_article_list_response(list_text)
    print(f"    {canton}: {len(articles)} articles found, fetching texts...")

    # Step 3: Fetch article texts with bounded concurrency
    semaphore = asyncio.Semaphore(concurrency)
    article_texts: dict[str, list[dict]] = {}

    async def fetch_one(art: dict) -> None:
        raw = art["raw"]
        async with semaphore:
            for attempt in range(3):
                try:
                    if attempt > 0:
                        await asyncio.sleep(2 ** attempt)  # 2s, 4s backoff
                    art_text = await mcp_call(
                        MCP_BASE, "get_law",
                        {"canton": canton, "sr_number": sr, "article": raw, "language": cfg["language"]},
                        timeout=30.0,
                    )
                    article_texts[raw] = parse_single_article_response(art_text)
                    return
                except Exception as e:
                    if attempt == 2:
                        print(f"    WARNING: {canton} Art. {raw}: {e}")
                        article_texts[raw] = []

    # Fetch sequentially in small batches to avoid rate limits
    batch_size = concurrency
    for i in range(0, len(articles), batch_size):
        batch = articles[i:i + batch_size]
        await asyncio.gather(*(fetch_one(art) for art in batch))
        if i + batch_size < len(articles):
            await asyncio.sleep(0.5)  # Brief pause between batches

    out_path = save_cantonal_law(
        canton=canton,
        title=cfg["title"],
        sr_number=sr,
        lexfind_id=cfg["lexfind_id"],
        language=cfg["language"],
        articles=articles,
        article_texts=article_texts,
    )

    fetched = sum(1 for v in article_texts.values() if v)
    print(f"  -> {canton}: {len(articles)} articles, {fetched} with text, saved to {out_path.name}")
    return out_path


async def fetch_all(cantons: list[str]) -> None:
    """Fetch KVs for all specified cantons sequentially."""
    for canton in cantons:
        try:
            await fetch_cantonal_kv(canton)
        except Exception as e:
            print(f"  ERROR fetching {canton}: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch cantonal KVs from opencaselaw")
    parser.add_argument("--canton", help="Two-letter canton code (e.g., ZH). Omit for all.")
    parser.add_argument("--list", action="store_true", help="List available cantons")
    args = parser.parse_args()

    if args.list:
        for code, cfg in CANTON_KV_CONFIG.items():
            print(f"{code}: {cfg['title']} ({cfg['language']}, LexFind {cfg['lexfind_id']})")
        sys.exit(0)

    cantons = [args.canton.upper()] if args.canton else list(CANTON_KV_CONFIG.keys())
    print(f"Fetching {len(cantons)} cantonal constitutions...")
    asyncio.run(fetch_all(cantons))
    print("Done.")
