"""Fetch cantonal law texts and save as per-law JSON.

Three source strategies:
  1. LexWork JSON API (19 cantons) — structured document tree, clean data
  2. SIL HTML portals (GE, NE) — Word-generated HTML
  3. opencaselaw MCP fallback (ZH, TI, SZ, VD, JU) — PDF-parsed via LexFind

Usage:
    uv run python -m scripts.fetch_cantonal_laws             # fetch all 26 KVs
    uv run python -m scripts.fetch_cantonal_laws --canton BE  # fetch one canton
    uv run python -m scripts.fetch_cantonal_laws --list       # list cantons
    uv run python -m scripts.fetch_cantonal_laws --force      # re-fetch even if exists
"""
from __future__ import annotations

import asyncio
import html as html_lib
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import httpx

CANTONAL_DIR = Path(__file__).parent / "cantonal"

USER_AGENT = (
    "OpenLegalCommentary/1.0 "
    "(https://openlegalcommentary.ch; legal research)"
)

# ── Canton configuration ─────────────────────────────────────────

CANTON_LANG: dict[str, str] = {
    "AG": "de", "AI": "de", "AR": "de", "BE": "de", "BL": "de",
    "BS": "de", "FR": "fr", "GE": "fr", "GL": "de", "GR": "de",
    "JU": "fr", "LU": "de", "NE": "fr", "NW": "de", "OW": "de",
    "SG": "de", "SH": "de", "SO": "de", "SZ": "de", "TG": "de",
    "TI": "it", "UR": "de", "VD": "fr", "VS": "de", "ZG": "de",
    "ZH": "de",
}

# LexWork REST API hosts (19 cantons)
LEXWORK_HOSTS: dict[str, str] = {
    "AG": "gesetzessammlungen.ag.ch",
    "AI": "ai.clex.ch",
    "AR": "ar.clex.ch",
    "BE": "www.belex.sites.be.ch",
    "BL": "bl.clex.ch",
    "BS": "www.gesetzessammlung.bs.ch",
    "FR": "fr.clex.ch",
    "GL": "gl.clex.ch",
    "GR": "www.gr-lex.gr.ch",
    "LU": "srl.lu.ch",
    "NW": "nw.clex.ch",
    "OW": "ow.clex.ch",
    "SG": "www.gesetzessammlung.sg.ch",
    "SH": "sh.clex.ch",
    "SO": "bgs.so.ch",
    "TG": "www.rechtsbuch.tg.ch",
    "UR": "rechtsbuch.ur.ch",
    "VS": "vs.clex.ch",
    "ZG": "zg.clex.ch",
}

# SIL portals (GE, NE) — Word-generated HTML
SIL_CONFIG: dict[str, dict] = {
    "NE": {"host": "rsn.ne.ch", "base_path": "/DATA/program/books/rsne"},
    "GE": {"host": "silgeneve.ch", "base_path": "/legis/program/books/rsg"},
}

# KV SR numbers per canton (for LexWork API lookup)
CANTON_KV_SR: dict[str, str] = {
    "ZH": "101", "BE": "101.1", "LU": "1", "UR": "1.1101",
    "SZ": "100.100", "OW": "101.0", "NW": "111", "GL": "I A/1/1",
    "ZG": "111.1", "FR": "10.1", "SO": "111.1", "BS": "111.100",
    "BL": "100", "SH": "101.000", "AR": "111.1", "AI": "101.000",
    "SG": "111.1", "GR": "110.100", "AG": "110.000", "TG": "101",
    "TI": "101.000", "VD": "101.01", "VS": "101.1", "NE": "101",
    "GE": "A 2 00", "JU": "101",
}

# LexFind IDs (for MCP fallback)
CANTON_LEXFIND_ID: dict[str, int] = {
    "ZH": 21736, "BE": 23149, "LU": 10797, "UR": 17919,
    "SZ": 17525, "OW": 12769, "NW": 13358, "GL": 7326,
    "ZG": 19965, "FR": 5674, "SO": 15261, "BS": 3293,
    "BL": 3696, "SH": 14100, "AR": 2368, "AI": 1209,
    "SG": 14551, "GR": 9576, "AG": 25, "TG": 17412,
    "TI": 20038, "VD": 18476, "VS": 19030, "NE": 9978,
    "GE": 31535, "JU": 8442,
}

MCP_BASE = "https://mcp.opencaselaw.ch"


# ── Save ─────────────────────────────────────────────────────────


def save_cantonal_law(
    canton: str,
    title: str,
    sr_number: str,
    language: str,
    articles: list[dict],
    article_texts: dict[str, list[dict]],
    *,
    source: str = "unknown",
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
        "lexfind_id": CANTON_LEXFIND_ID.get(canton, 0),
        "fetched_at": date.today().isoformat(),
        "source": source,
        "article_count": len(articles),
        "articles": articles,
        "article_texts": article_texts,
    }
    out_path = CANTONAL_DIR / f"{slug}.json"
    out_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return out_path


# ── LexWork fetcher (19 cantons) ─────────────────────────────────


def fetch_lexwork(canton: str) -> Path:
    """Fetch a law via LexWork structured JSON API."""
    host = LEXWORK_HOSTS[canton]
    lang = CANTON_LANG[canton]
    sr = CANTON_KV_SR[canton]
    base = f"https://{host}"

    print(f"  {canton}: LexWork API at {host}...")
    r = _http_get(
        f"{base}/api/{lang}/texts_of_law/{sr}/show_as_json"
    )
    data = r.json()
    tol = data["text_of_law"]
    sv = tol.get("selected_version") or tol.get("current_version", {})
    jc = sv.get("json_content")
    if not jc:
        raise RuntimeError(f"{canton}: no json_content in LexWork response")

    title = tol.get("title", "")
    actual_sr = tol.get("systematic_number", sr)

    # Walk document tree to extract articles
    doc = jc["document"]
    content_node = doc.get("content", {})
    articles: list[dict] = []
    article_texts: dict[str, list[dict]] = {}
    _walk_lexwork_tree(content_node, lang, articles, article_texts)

    out = save_cantonal_law(
        canton=canton, title=title, sr_number=actual_sr,
        language=lang, articles=articles,
        article_texts=article_texts, source="lexwork",
    )
    print(f"  -> {canton}: {len(articles)} articles (LexWork)")
    return out


def _walk_lexwork_tree(
    node: dict,
    lang: str,
    articles: list[dict],
    article_texts: dict[str, list[dict]],
) -> None:
    """Recursively walk a LexWork document tree, extracting articles."""
    node_type = node.get("type", "")

    if node_type == "article":
        # Extract article number
        number_raw = node.get("number", {}).get(lang, "")
        art_num = _clean_article_number(number_raw)
        if not art_num:
            return

        # Article heading
        heading = node.get("text", {}).get(lang, "")

        # Collect paragraph texts from children
        para_parts: list[str] = []
        for child in node.get("children", []):
            _collect_paragraphs(child, lang, para_parts)

        art_text = "\n".join(para_parts)

        # Parse number/suffix
        m = re.match(r"^(\d+)([a-z]*)$", art_num)
        if m:
            num = int(m.group(1))
            suffix = m.group(2)
        else:
            return

        articles.append({
            "number": num,
            "suffix": suffix,
            "raw": art_num,
            "title": heading,
        })
        article_texts[art_num] = parse_article_text(art_text)
        return

    # Recurse into children for non-article nodes
    for child in node.get("children", []):
        _walk_lexwork_tree(child, lang, articles, article_texts)


def _collect_paragraphs(
    node: dict, lang: str, parts: list[str],
) -> None:
    """Collect text from paragraph/enumeration nodes."""
    node_type = node.get("type", "")
    html_content = node.get("html_content", {}).get(lang, "")

    if node_type in ("footnote_reference", "footnote"):
        return

    if node_type in ("paragraph", "enumeration") and html_content:
        # Extract number and text separately for clean output
        num = _extract_html_number(html_content)
        text = _extract_html_text_content(html_content)
        if num and text:
            parts.append(f"{num} {text}")
        elif text:
            parts.append(text)
        elif num:
            parts.append(num)
    elif html_content:
        text = _html_to_text(html_content)
        if text:
            parts.append(text)

    for child in node.get("children", []):
        _collect_paragraphs(child, lang, parts)


def _html_to_text(html_str: str) -> str:
    """Convert LexWork HTML snippets to clean text.

    Paragraph structure: <span class='number'>N</span> <p><span
    class='text_content'>Text</span></p> → "N Text"
    """
    if not html_str:
        return ""
    # Replace <br> with newlines
    text = re.sub(r"<br\s*/?>", "\n", html_str)
    # Close block elements with newlines, but NOT <p> inside
    # paragraphs — we want "N Text" on one line
    text = re.sub(r"</(?:div|li|tr)>", "\n", text)
    # Remove <p> and </p> (keep inline with number span)
    text = re.sub(r"</?p>", " ", text)
    # Extract number spans: keep as "N " prefix
    text = re.sub(
        r"<span\s+class=['\"]number['\"]>([^<]*)</span>",
        r"\1 ", text,
    )
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    text = html_lib.unescape(text)
    lines = []
    for line in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines)


def _extract_html_number(html_str: str) -> str:
    """Extract paragraph number from <span class='number'>N</span>."""
    m = re.search(
        r"<span\s+class=['\"]number['\"]>([^<]*)</span>", html_str,
    )
    return html_lib.unescape(m.group(1)).strip() if m else ""


def _extract_html_text_content(html_str: str) -> str:
    """Extract text content, stripping all HTML tags."""
    # Remove number spans first (already extracted separately)
    text = re.sub(
        r"<span\s+class=['\"]number['\"]>[^<]*</span>", "", html_str,
    )
    # Remove article_number/article_title divs (metadata, not content)
    text = re.sub(
        r"<div\s+class=['\"]article_(?:number|title)['\"]>.*?</div>",
        "", text, flags=re.DOTALL,
    )
    # Strip all tags
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _clean_article_number(raw: str) -> str:
    """'Art.&nbsp;5a' → '5a', '§&nbsp;1' → '1', 'Artikel&nbsp;1' → '1'."""
    text = html_lib.unescape(raw)
    text = re.sub(r"^(?:Artikel|Art\.?|§)\s*", "", text).strip()
    return text


# ── SIL fetcher (GE, NE) ────────────────────────────────────────


def fetch_sil(canton: str) -> Path:
    """Fetch a law from a SIL (Word HTML) portal."""
    cfg = SIL_CONFIG[canton]
    lang = CANTON_LANG[canton]
    sr = CANTON_KV_SR[canton]
    base_url = f"https://{cfg['host']}"
    data_base = f"{base_url}{cfg['base_path']}"

    # Find the right filename for this SR number
    print(f"  {canton}: SIL portal at {cfg['host']}...")
    r = _http_get(f"{data_base}/content.htm", accept="text/html")
    r.encoding = "windows-1252"

    # Find PDF/HTML file for this SR
    # SIL uses filenames like "rsg_a2_00.pdf" for GE constitution
    sr_pattern = sr.replace(" ", "_").replace(".", "_").lower()
    pdf_pattern = re.compile(
        rf"href=['\"](?:pdf|htm)/([^'\"]*{re.escape(sr_pattern)}[^'\"]*)['\"]",
        re.IGNORECASE,
    )
    pdf_match = pdf_pattern.search(r.text)

    if not pdf_match:
        # Try matching by title in content listing
        title_pattern = re.compile(
            rf"href=['\"](?:pdf|htm)/([^'\"]+)['\"]>"
            rf"\s*{re.escape(sr)}\s",
            re.IGNORECASE,
        )
        pdf_match = title_pattern.search(r.text)

    if not pdf_match:
        raise RuntimeError(
            f"{canton}: could not find KV file in SIL content.htm"
        )

    filename = pdf_match.group(1)
    is_pdf = filename.endswith(".pdf")

    if is_pdf:
        # Fall back to MCP for PDF-based SIL cantons
        print(f"    {canton}: SIL serves PDF, falling back to MCP")
        return asyncio.run(_fetch_mcp(canton))

    # Fetch HTML law page
    law_url = f"{data_base}/htm/{filename}"
    r = _http_get(law_url, accept="text/html")
    r.encoding = "windows-1252"

    # Parse HTML into articles
    articles, article_texts, title = _parse_sil_html(
        r.text, lang, sr
    )

    out = save_cantonal_law(
        canton=canton, title=title, sr_number=sr,
        language=lang, articles=articles,
        article_texts=article_texts, source="sil",
    )
    print(f"  -> {canton}: {len(articles)} articles (SIL)")
    return out


def _parse_sil_html(
    html_text: str, lang: str, sr: str,
) -> tuple[list[dict], dict[str, list[dict]], str]:
    """Parse SIL Word-generated HTML into articles."""
    # Extract title
    title_match = re.search(r"<title>([^<]+)</title>", html_text)
    title = html_lib.unescape(
        title_match.group(1).strip()
    ) if title_match else ""

    # Extract body
    body_match = re.search(
        r"<body[^>]*>(.*)</body>",
        html_text, re.DOTALL | re.IGNORECASE,
    )
    if not body_match:
        return [], {}, title

    body = body_match.group(1)
    body = re.sub(
        r"<(?:script|style)[^>]*>.*?</(?:script|style)>",
        "", body, flags=re.DOTALL | re.IGNORECASE,
    )
    body = re.sub(r"<br\s*/?>", "\n", body)
    body = re.sub(
        r"</(?:p|div|h[1-6]|li|tr)>", "\n",
        body, flags=re.IGNORECASE,
    )
    text = re.sub(r"<[^>]+>", "", body)
    text = html_lib.unescape(text)
    lines = [
        re.sub(r"[ \t]+", " ", ln).strip()
        for ln in text.split("\n") if ln.strip()
    ]
    full_text = "\n".join(lines)

    # Segment into articles
    pattern = re.compile(
        r"^Art\.\s*(\d+[a-z]?(?:bis|ter|quater|quinquies)?)\s*(.*)",
        re.MULTILINE,
    )
    articles: list[dict] = []
    article_texts: dict[str, list[dict]] = {}
    matches = list(pattern.finditer(full_text))

    for i, match in enumerate(matches):
        art_num = match.group(1)
        heading = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        art_text = full_text[start:end].strip()

        m = re.match(r"^(\d+)([a-z]*)$", art_num)
        if not m:
            continue

        articles.append({
            "number": int(m.group(1)),
            "suffix": m.group(2),
            "raw": art_num,
            "title": heading,
        })
        article_texts[art_num] = parse_article_text(art_text)

    return articles, article_texts, title


# ── MCP fallback (ZH, TI, SZ, VD, JU) ───────────────────────────


async def _fetch_mcp(canton: str) -> Path:
    """Fetch via opencaselaw MCP API (PDF-parsed, used as fallback)."""
    from agents.mcp_client import mcp_call

    lang = CANTON_LANG[canton]
    sr = CANTON_KV_SR[canton]
    lexfind_id = CANTON_LEXFIND_ID[canton]

    print(f"  {canton}: MCP fallback (LexFind PDF)...")

    # Try get_law first (uses cantonal_laws.db if populated)
    list_text = await mcp_call(
        MCP_BASE, "get_law",
        {"canton": canton, "sr_number": sr, "language": lang},
        timeout=60.0,
    )
    articles = _parse_mcp_article_list(list_text)

    # If get_law returned nothing, fall back to get_legislation
    # which downloads + parses the PDF on the fly
    if not articles:
        print(f"    {canton}: get_law empty, trying get_legislation...")
        leg_text = await mcp_call(
            MCP_BASE, "get_legislation",
            {"lexfind_id": lexfind_id, "language": lang},
            timeout=180.0,
        )
        articles, article_texts = _parse_legislation_response(leg_text)
        title = _mcp_extract_title(leg_text)
        out = save_cantonal_law(
            canton=canton, title=title, sr_number=sr,
            language=lang, articles=articles,
            article_texts=article_texts, source="mcp_lexfind_pdf",
        )
        fetched = sum(1 for v in article_texts.values() if v)
        print(
            f"  -> {canton}: {len(articles)} articles, "
            f"{fetched} with text (get_legislation)"
        )
        return out

    print(f"    {canton}: {len(articles)} articles, fetching texts...")

    # Fetch texts one by one (rate-limited)
    article_texts: dict[str, list[dict]] = {}
    for art in articles:
        raw = art["raw"]
        for attempt in range(3):
            try:
                if attempt > 0:
                    await asyncio.sleep(2 ** attempt)
                art_text = await mcp_call(
                    MCP_BASE, "get_law",
                    {"canton": canton, "sr_number": sr,
                     "article": raw, "language": lang},
                    timeout=30.0,
                )
                article_texts[raw] = _parse_mcp_article(art_text)
                break
            except Exception as e:
                if attempt == 2:
                    print(f"    WARN: {canton} Art. {raw}: {e}")
                    article_texts[raw] = []
        await asyncio.sleep(0.3)

    # Get title from config or response
    title = _mcp_extract_title(list_text)

    out = save_cantonal_law(
        canton=canton, title=title, sr_number=sr,
        language=lang, articles=articles,
        article_texts=article_texts, source="mcp_lexfind",
    )
    fetched = sum(1 for v in article_texts.values() if v)
    print(f"  -> {canton}: {len(articles)} articles, {fetched} with text (MCP)")
    return out


def _parse_mcp_article_list(text: str) -> list[dict]:
    """Parse get_law article list markdown."""
    articles: list[dict] = []
    seen: set[str] = set()
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("- Art.") and not line.startswith("- §"):
            continue
        if re.match(r"^- (?:Art\.|§)\s+\d+\s*[–—-]\s*\d+", line):
            continue
        match = re.match(
            r"^- (?:Art\.|§)\s+(\d+)\s*([a-z]*)\s*(.*)", line
        )
        if not match:
            continue
        number = int(match.group(1))
        suffix = match.group(2).strip()
        rest = match.group(3).strip()
        raw = f"{number}{suffix}"
        if raw in seen:
            continue
        seen.add(raw)
        title = _clean_mcp_title(rest)
        articles.append({
            "number": number, "suffix": suffix,
            "raw": raw, "title": title,
        })
    articles.sort(key=lambda a: (a["number"], a["suffix"]))
    return articles


def _clean_mcp_title(text: str) -> str:
    """Clean MCP article title, strip amendment notes."""
    if not text:
        return ""
    skip_starts = (
        "Eingefügt", "Fassung gemäss", "Aufgehoben", "Angenommen",
        "in der Fassung", "In Kraft", "Berichtigt",
        "Introduit", "Adopté", "Abrogé", "Accepté",
        "Introdotto", "Accettato", "Abrogato",
    )
    for prefix in skip_starts:
        if text.startswith(prefix):
            return ""
    for marker in skip_starts:
        idx = text.find(marker)
        if idx > 0:
            text = text[:idx].strip()
            break
    text = re.sub(r"\s*\*?\s*Mit Übergangsbestimmung\.?\s*\*?", "", text)
    return text.strip()


def _parse_mcp_article(text: str) -> list[dict]:
    """Parse single article from MCP get_law response."""
    # Strip the attribution note
    text = re.sub(
        r"---\s*ℹ️.*$", "", text, flags=re.DOTALL
    )
    lines = text.splitlines()
    body_start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("### "):
            body_start = i + 1
            break
    body = "\n".join(lines[body_start:]).strip()
    return parse_article_text(body)


def _parse_legislation_response(
    text: str,
) -> tuple[list[dict], dict[str, list[dict]]]:
    """Parse get_legislation markdown into articles + texts."""
    articles: list[dict] = []
    article_texts: dict[str, list[dict]] = {}

    # Strip attribution note
    text = re.sub(r"---\s*ℹ️.*$", "", text, flags=re.DOTALL)

    # Split at article headers
    sections = re.split(
        r"(?=^### (?:Art\.|§)\s+)", text, flags=re.MULTILINE,
    )

    for section in sections:
        section = section.strip()
        if not section.startswith("### "):
            continue
        header_match = re.match(
            r"^### (?:Art\.|§)\s+(\d+)([a-z]*)\s*(?:—\s*(.+?))?$",
            section.split("\n")[0],
        )
        if not header_match:
            continue

        num = int(header_match.group(1))
        suffix = header_match.group(2) or ""
        heading = (header_match.group(3) or "").strip()
        raw = f"{num}{suffix}"

        if any(a["raw"] == raw for a in articles):
            continue

        body = "\n".join(section.split("\n")[1:]).strip()

        articles.append({
            "number": num, "suffix": suffix,
            "raw": raw, "title": heading,
        })
        article_texts[raw] = parse_article_text(body)

    return articles, article_texts


def _mcp_extract_title(text: str) -> str:
    """Extract law title from MCP response header."""
    for line in text.splitlines():
        if line.startswith("**") and "**" in line[2:]:
            return line.strip("* \n")
    return ""


# ── Shared text parser ───────────────────────────────────────────


def parse_article_text(text: str) -> list[dict]:
    """Parse article text into paragraph structures.

    Handles numbered paragraphs (1, 2, 3...) and unnumbered text.
    Returns list of ArticleTextParagraph-shaped dicts.
    """
    if not text.strip():
        return []

    # Join PDF-broken lines
    text = re.sub(r"\u00ad\s*\n", "", text)  # soft hyphen
    text = re.sub(r"-\s*\n(?=[a-zà-ü])", "", text)  # hard hyphen

    lines = text.strip().split("\n")
    paragraphs: list[dict] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        num_match = re.match(r"^(\d+)\s+(.+)$", line)
        if num_match:
            para_num = num_match.group(1)
            if int(para_num) <= 20:
                paragraphs.append({
                    "num": para_num,
                    "text": num_match.group(2),
                })
                continue

        is_continuation = (
            paragraphs
            and not line[0].isupper()
            and not line.startswith("a.")
            and not line.startswith("a)")
        )
        if is_continuation:
            paragraphs[-1]["text"] += " " + line
        else:
            paragraphs.append({"num": None, "text": line})

    if not paragraphs:
        paragraphs = [{"num": None, "text": text.strip()}]

    return paragraphs


# ── HTTP helper ──────────────────────────────────────────────────

_last_request_time: float = 0


def _http_get(
    url: str, delay: float = 0.5, accept: str = "*/*",
) -> httpx.Response:
    """Rate-limited HTTP GET."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < delay:
        time.sleep(delay - elapsed)
    r = httpx.get(
        url, timeout=30,
        headers={"User-Agent": USER_AGENT, "Accept": accept},
        follow_redirects=True,
    )
    _last_request_time = time.time()
    r.raise_for_status()
    return r


# ── Orchestrator ─────────────────────────────────────────────────


def fetch_canton(canton: str) -> Path:
    """Fetch a canton's KV using the best available source."""
    canton = canton.upper()
    if canton in LEXWORK_HOSTS:
        return fetch_lexwork(canton)
    elif canton in SIL_CONFIG:
        return fetch_sil(canton)
    else:
        # MCP fallback for ZH, TI, SZ, VD, JU
        return asyncio.run(_fetch_mcp(canton))


def fetch_all(
    cantons: list[str], *, force: bool = False,
) -> None:
    """Fetch KVs for all cantons."""
    for canton in cantons:
        slug = f"{canton.lower()}-kv"
        existing = CANTONAL_DIR / f"{slug}.json"
        if not force and existing.exists():
            data = json.loads(existing.read_text())
            count = data.get("article_count", 0)
            if count > 0:
                print(f"  SKIP {canton}: {count} articles (use --force)")
                continue
        try:
            fetch_canton(canton)
        except Exception as e:
            print(f"  ERROR {canton}: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch cantonal KVs"
    )
    parser.add_argument(
        "--canton",
        help="Two-letter canton code (e.g., ZH). Omit for all.",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List available cantons and their source type",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-fetch even if data already exists",
    )
    args = parser.parse_args()

    if args.list:
        for code in sorted(CANTON_LANG.keys()):
            if code in LEXWORK_HOSTS:
                src = f"LexWork ({LEXWORK_HOSTS[code]})"
            elif code in SIL_CONFIG:
                src = f"SIL ({SIL_CONFIG[code]['host']})"
            else:
                src = "MCP fallback (LexFind PDF)"
            print(f"  {code} ({CANTON_LANG[code]}): {src}")
        sys.exit(0)

    cantons = (
        [args.canton.upper()]
        if args.canton
        else sorted(CANTON_LANG.keys())
    )
    print(f"Fetching {len(cantons)} cantonal constitutions...")
    fetch_all(cantons, force=args.force)
    print("Done.")
