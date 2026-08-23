"""Shared reference loading and formatting for the agent pipeline.

Consolidates article text and commentary reference loading, used by both
the law agent and evaluator.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

ARTICLE_TEXTS_PATH = Path("scripts/article_texts.json")

_article_texts_cache: dict | None = None


def load_article_texts() -> dict:
    """Load article texts from JSON, with module-level caching."""
    global _article_texts_cache
    if _article_texts_cache is not None:
        return _article_texts_cache
    if ARTICLE_TEXTS_PATH.exists():
        _article_texts_cache = json.loads(ARTICLE_TEXTS_PATH.read_text())
        return _article_texts_cache
    _article_texts_cache = {}
    return _article_texts_cache


def format_article_text(law: str, article_number: int, suffix: str) -> str:
    """Format article text from article_texts.json for prompt injection."""
    texts = load_article_texts()
    key = f"{article_number}{suffix}"
    paragraphs = texts.get(law.upper(), {}).get(key, [])
    if not paragraphs:
        return ""
    lines = []
    for p in paragraphs:
        if p.get("type") == "list":
            for item in p.get("items", []):
                lines.append(f"  {item['letter']}. {item['text']}")
        elif p.get("num"):
            lines.append(f"  {p['num']} {p.get('text', '')}")
        else:
            lines.append(p.get("text", ""))
    return "\n".join(lines)


# --- Commentary references (Doctrinal Sources) ---

# The on-disk naming convention, defined once. scripts/verify_citations.py
# imports these rather than repeating the pattern: in March 2026 a rename
# changed this tuple and the data file separately, they stopped agreeing, and
# the doctrine prompt silently lost its commentary block for five months.
COMMENTARY_SOURCES = ("primary", "cr")


def commentary_refs_filename(law: str, source: str) -> str:
    """Return the expected filename for a law's commentary reference data."""
    return f"{law.lower()}_{source}.json"


_commentary_refs_cache: dict[tuple, dict] = {}


def load_commentary_refs(refs_root: Path, law: str) -> dict:
    """Load and merge Primary + CR commentary references for a law.

    Returns a dict keyed by article number string. When both Primary and CR
    exist for the same article, the value is {"primary": {...}, "cr": {...}}.
    When only one source exists, it's {"primary": {...}} or {"cr": {...}}.
    Returns empty dict if no files exist.
    """
    cache_key = (str(refs_root), law)
    if cache_key in _commentary_refs_cache:
        return _commentary_refs_cache[cache_key]

    merged: dict = {}
    for source in COMMENTARY_SOURCES:
        path = refs_root / commentary_refs_filename(law, source)
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        articles = data.get(law.upper(), {})
        for art_key, art_data in articles.items():
            if art_key not in merged:
                merged[art_key] = {}
            merged[art_key][source] = art_data

    if not merged:
        _warn_unrecognised_refs(refs_root, law)

    _commentary_refs_cache[cache_key] = merged
    return merged


def _warn_unrecognised_refs(refs_root: Path, law: str) -> None:
    """Warn when refs_root holds files for `law` that the loader ignores.

    An empty result is legitimate for a law with no reference data. It is not
    legitimate when files for that law are sitting right there under a name the
    loader does not read. That is the failure mode this guard exists for.
    """
    if not refs_root.is_dir():
        return
    prefix = f"{law.lower()}_"
    expected = {commentary_refs_filename(law, s) for s in COMMENTARY_SOURCES}
    stray = sorted(
        p.name for p in refs_root.glob("*.json")
        if p.name.startswith(prefix) and p.name not in expected
    )
    if stray:
        warnings.warn(
            f"commentary reference data for {law.upper()} was not loaded: "
            f"{refs_root} contains {', '.join(stray)}, but the loader reads "
            f"{' or '.join(sorted(expected))}. The doctrine prompt will have "
            f"no commentary block for {law.upper()}.",
            RuntimeWarning,
            stacklevel=3,
        )


def _format_single_source(source_label: str, data: dict) -> str:
    """Format a single Primary or CR source block."""
    lines = []
    lines.append(f"### {source_label}")
    lines.append(f"Authors: {', '.join(data.get('authors', []))}")
    lines.append(f"Edition: {data.get('edition', '')}")

    rz_map = data.get("randziffern_map", {})
    if rz_map:
        lines.append("")
        lines.append("Randziffern overview:")
        for rz_range, topic in rz_map.items():
            lines.append(f"- N. {rz_range}: {topic}")

    positions = data.get("positions", [])
    if positions:
        lines.append("")
        lines.append("Key positions:")
        for p in positions:
            lines.append(f"- {p['author']}, {p['n']}: {p['position']}")

    controversies = data.get("controversies", [])
    if controversies:
        lines.append("")
        lines.append("Doctrinal controversies:")
        for c in controversies:
            parts = [
                f"{author}: {pos}"
                for author, pos in c["positions"].items()
            ]
            lines.append(f"- {c['topic']}: {'; '.join(parts)}")

    cross_refs = data.get("cross_refs", [])
    if cross_refs:
        lines.append("")
        lines.append(f"Cross-references: {', '.join(cross_refs)}")

    key_lit = data.get("key_literature", [])
    if key_lit:
        lines.append("")
        lines.append("Key literature:")
        for lit in key_lit:
            lines.append(f"- {lit}")

    return "\n".join(lines)


def format_commentary_refs(
    refs_root: Path, law: str, article_number: int, suffix: str,
) -> str:
    """Format commentary references for prompt injection.

    Returns empty string if no data available.
    """
    refs = load_commentary_refs(refs_root, law)
    key = f"{article_number}{suffix}"
    article_refs = refs.get(key)
    if not article_refs:
        return ""

    blocks = []
    blocks.append("## Doctrinal Reference Data (Doctrinal Sources)")
    blocks.append("")

    for source in ("primary", "cr"):
        if source in article_refs:
            label = "Primary" if source == "primary" else "CR"
            blocks.append(_format_single_source(label, article_refs[source]))
            blocks.append("")

    blocks.append(
        "Use these references to ground your doctrinal analysis. "
        "Cite authors with proper Primary/CR Randziffern."
    )
    blocks.append(
        "Do NOT reproduce commentary text — synthesize original "
        "analysis that cites specific positions."
    )

    return "\n".join(blocks)


# --- Preparatory materials (Botschaften, parliamentary data) ---

PREPARATORY_MATERIALS_ROOT = Path("scripts/preparatory_materials")
CANTONAL_MATERIALS_ROOT = Path("scripts/cantonal_materials")

_prep_materials_cache: dict[str, dict] = {}
_cantonal_sources_cache: dict[str, dict | None] = {}


def is_cantonal_kv(law: str) -> bool:
    """True if the law key denotes a cantonal constitution (e.g., 'sg-kv')."""
    return law.lower().endswith("-kv") and len(law) == 5


def load_cantonal_sources(law: str) -> dict | None:
    """Load the cantonal source catalog for a cantonal KV, or None.

    Looks up ``scripts/cantonal_materials/{xx}.json`` where ``xx`` is the
    canton code derived from a law key like ``sg-kv``.
    """
    if law in _cantonal_sources_cache:
        return _cantonal_sources_cache[law]
    if not is_cantonal_kv(law):
        _cantonal_sources_cache[law] = None
        return None
    canton = law.lower().split("-")[0]
    path = CANTONAL_MATERIALS_ROOT / f"{canton}.json"
    if not path.exists():
        _cantonal_sources_cache[law] = None
        return None
    _cantonal_sources_cache[law] = json.loads(path.read_text())
    return _cantonal_sources_cache[law]


def format_cantonal_sources(law: str) -> str:
    """Format the cantonal source catalog for prompt injection.

    Unlike federal Materialien, cantonal KVs do not (yet) have per-article
    digests. This block is therefore identical for every article of a given
    canton: it points the agent at the official source landscape
    (Verfassungsrat-Bericht, Staatsarchiv, Amtsblatt, kantonale
    Rechtsprechungs-Plattformen) so doctrinal analysis can be grounded
    without fabricating specific page references.
    """
    data = load_cantonal_sources(law)
    if not data:
        return ""

    blocks: list[str] = []
    blocks.append("## Kantonale Quellen (Source Catalog)")
    blocks.append("")

    meta = data.get("historical_sources", {}).get("kv_metadata") or {}
    if meta:
        blocks.append("### KV-Metadaten")
        if meta.get("short_title"):
            blocks.append(f"- **Erlass:** {meta['short_title']} ({meta.get('sr_number', '')})")
        if meta.get("adoption_date"):
            blocks.append(
                f"- **Annahme:** {meta['adoption_date']} "
                f"({meta.get('adoption_method', '')})"
            )
        if meta.get("in_force"):
            blocks.append(f"- **In Kraft:** {meta['in_force']}")
        if meta.get("revision_type"):
            blocks.append(f"- **Revisionstyp:** {meta['revision_type']}")
        if meta.get("predecessor"):
            blocks.append(f"- **Vorgängererlass:** {meta['predecessor']}")
        blocks.append("")

    hist = data.get("historical_sources", {})
    # BS/SG record an elected "verfassungsrat" (field: body); cantons whose KV
    # was drafted by a parliamentary commission instead — e.g. BL — record a
    # "verfassungserarbeitung" (field: organ). Render either.
    vr = hist.get("verfassungsrat")
    vr_heading = "Verfassungsrat (Entstehungsgeschichte)"
    if not vr:
        vr = hist.get("verfassungserarbeitung")
        vr_heading = "Verfassungserarbeitung (Entstehungsgeschichte)"
    vr = vr or {}
    if vr:
        blocks.append(f"### {vr_heading}")
        gremium = vr.get("body") or vr.get("organ")
        if gremium:
            blocks.append(f"**Gremium:** {gremium}")
        if vr.get("period"):
            blocks.append(f"**Wirkungszeit:** {vr['period']}")
        pubs = vr.get("key_publications") or []
        if pubs:
            blocks.append("**Schlüsselpublikationen:**")
            for p in pubs:
                line = f"- *{p['title']}*"
                if p.get("date"):
                    line += f" ({p['date']})"
                if p.get("note"):
                    line += f" — {p['note']}"
                blocks.append(line)
        blocks.append("")

    archives = data.get("historical_sources", {}).get("archives") or []
    if archives:
        blocks.append("### Archive & amtliche Publikationsorgane")
        for a in archives:
            line = f"- **{a['name']}** ({a.get('url', '')})"
            if a.get("note"):
                line += f" — {a['note']}"
            blocks.append(line)
        blocks.append("")

    cats = data.get("kategorien") or {}
    if cats:
        blocks.append("### Kantonale Plattformen (laufende Rechtsetzung & Rechtsprechung)")
        for _, group in cats.items():
            for _, src in (group.get("sources") or {}).items():
                if not (src.get("link") or src.get("bemerkung")):
                    continue
                line = "- "
                if src.get("link"):
                    line += f"{src['link']}"
                if src.get("bemerkung"):
                    line += f" — {src['bemerkung']}"
                if src.get("ab"):
                    line += f" (ab {src['ab']})"
                blocks.append(line)
        blocks.append("")

    caveats = data.get("historical_sources", {}).get("caveats") or []
    if caveats:
        blocks.append("### Hinweise zur Quellenlage")
        for c in caveats:
            blocks.append(f"- {c}")
        blocks.append("")

    blocks.append(
        "**Anti-Fabrikations-Regel (kantonal):** Diese Quellen sind in dieser "
        "Pipeline NICHT digestiert. Nenne den *Bericht des Verfassungsrats* "
        "(bzw. der Verfassungskommission) und vergleichbare Materialien beim "
        "Namen, ohne erfundene Seiten- oder "
        "Randziffern. Konkrete Zitate nur, wenn sie über opencaselaw "
        "(`get_decision`, `search_decisions`, `get_law`) oder eine andere "
        "verifizierbare Quelle abrufbar sind."
    )

    return "\n".join(blocks)


def _load_json_articles(path: Path) -> dict:
    """Load a JSON file and return its 'articles' dict, or empty dict."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return data.get("articles", {})


def load_preparatory_materials(law: str) -> dict:
    """Load per-article preparatory materials for a law.

    Returns dict keyed by article number string, or empty dict if no file.
    """
    if law in _prep_materials_cache:
        return _prep_materials_cache[law]

    path = PREPARATORY_MATERIALS_ROOT / f"{law.lower()}.json"
    if not path.exists():
        _prep_materials_cache[law] = {}
        return {}

    data = json.loads(path.read_text())
    _prep_materials_cache[law] = data.get("articles", {})
    return _prep_materials_cache[law]


def load_all_materialien(law: str) -> dict:
    """Load all Materialien sources for a law into a unified per-article dict.

    Returns ``{article_key: {botschaft: {...}, erlaeuterungsbericht: {...},
    ab_staenderat: {...}, ab_nationalrat: {...}}}``.  Each sub-key is present
    only when the corresponding JSON file exists and contains data for that
    article.
    """
    law_lower = law.lower()
    sources = {
        "botschaft": _load_json_articles(
            PREPARATORY_MATERIALS_ROOT / f"{law_lower}.json",
        ),
        "erlaeuterungsbericht": _load_json_articles(
            PREPARATORY_MATERIALS_ROOT / f"{law_lower}_erlaeuterungsbericht.json",
        ),
        "ab_staenderat": _load_json_articles(
            PREPARATORY_MATERIALS_ROOT / f"{law_lower}_ab_staenderat.json",
        ),
        "ab_nationalrat": _load_json_articles(
            PREPARATORY_MATERIALS_ROOT / f"{law_lower}_ab_nationalrat.json",
        ),
    }

    # Merge into per-article dict
    all_keys: set[str] = set()
    for src_data in sources.values():
        all_keys.update(src_data.keys())

    merged: dict[str, dict] = {}
    for key in all_keys:
        entry: dict = {}
        for src_name, src_data in sources.items():
            if key in src_data:
                entry[src_name] = src_data[key]
        merged[key] = entry

    return merged


def _format_botschaft_source(source: dict) -> list[str]:
    """Format a single Botschaft source entry."""
    lines: list[str] = []
    bbl = source.get("bbl_ref", "?")
    pages = ", ".join(source.get("bbl_page_refs", []))
    lines.append(f"**Reference:** {bbl}, pp. {pages}")

    intent = source.get("legislative_intent")
    if intent:
        lines.append(f"**Legislative intent:** {intent}")

    for arg in source.get("key_arguments", []):
        lines.append(f"- {arg}")

    choices = source.get("design_choices", [])
    if choices:
        lines.append("**Design choices:**")
        for c in choices:
            lines.append(f"- {c}")

    rejected = source.get("rejected_alternatives", [])
    if rejected:
        lines.append("**Rejected alternatives:**")
        for r in rejected:
            lines.append(f"- {r}")

    return lines


def _format_debate_source(source_entry: dict) -> list[str]:
    """Format a single AB (parliamentary debate) source entry."""
    lines: list[str] = []
    for src in source_entry.get("sources", [source_entry]):
        ref = src.get("reference", "")
        if ref:
            lines.append(f"**Reference:** {ref}")

        speakers = src.get("speakers", [])
        if speakers:
            for sp in speakers[:8]:
                name = sp.get("name", "?")
                stmt = sp.get("statement", "")[:200]
                role = sp.get("role", "")
                prefix = f"{name} ({role})" if role else name
                lines.append(f"- **{prefix}:** {stmt}")

        contested = src.get("contested_points", [])
        if contested:
            lines.append("**Contested points:**")
            for c in contested[:5]:
                lines.append(f"- {c}")

        quotes = src.get("key_quotes", [])
        if quotes:
            lines.append("**Key quotes:**")
            for q in quotes[:3]:
                speaker = q.get("speaker", "?")
                quote = q.get("quote", "")[:250]
                lines.append(f"- «{quote}» ({speaker})")

        # Vote counts deliberately omitted — not legally relevant and
        # their inclusion led to fabricated numbers in the generated text.

    return lines


def format_preparatory_materials(
    law: str, article_number: int, suffix: str,
) -> str:
    """Format all available Materialien for prompt injection.

    Loads Botschaft, Erläuterungsbericht, and parliamentary debate data
    (AB Ständerat + AB Nationalrat) and formats them as a unified block.
    For cantonal constitutions (``xx-kv``), dispatches to
    :func:`format_cantonal_sources` instead, which returns a static source
    catalog (Verfassungsrat-Bericht, Staatsarchiv, kantonale Plattformen).
    Returns empty string if no data available.
    """
    if is_cantonal_kv(law):
        return format_cantonal_sources(law)

    all_mat = load_all_materialien(law)
    key = f"{article_number}{suffix}"
    article_mat = all_mat.get(key)
    if not article_mat:
        # Fallback to legacy single-file format
        materials = load_preparatory_materials(law)
        article_data = materials.get(key)
        if not article_data:
            return ""
        # Legacy format: just Botschaft sources
        blocks = ["## Materialien (Legislative History)", ""]
        blocks.append("### Botschaft")
        for source in article_data.get("sources", []):
            blocks.extend(_format_botschaft_source(source))
            blocks.append("")
        return "\n".join(blocks)

    blocks: list[str] = []
    blocks.append("## Materialien (Legislative History)")
    blocks.append("")

    # 1. Botschaft
    bot = article_mat.get("botschaft")
    if bot:
        blocks.append("### Botschaft (Federal Council Message)")
        for source in bot.get("sources", [bot]):
            blocks.extend(_format_botschaft_source(source))
        blocks.append("")

    # 2. Erläuterungsbericht
    erl = article_mat.get("erlaeuterungsbericht")
    if erl:
        blocks.append("### Erläuterungsbericht (Explanatory Report, VE 1995)")
        for source in erl.get("sources", [erl]):
            blocks.extend(_format_botschaft_source(source))
        blocks.append("")

    # 3. AB Ständerat
    ab_sr = article_mat.get("ab_staenderat")
    if ab_sr:
        blocks.append("### Parlamentarische Beratungen — Ständerat")
        blocks.extend(_format_debate_source(ab_sr))
        blocks.append("")

    # 4. AB Nationalrat
    ab_nr = article_mat.get("ab_nationalrat")
    if ab_nr:
        blocks.append("### Parlamentarische Beratungen — Nationalrat")
        blocks.extend(_format_debate_source(ab_nr))
        blocks.append("")

    # Parliamentary modifications from the Botschaft data structure
    bot_data = article_mat.get("botschaft", {})
    mods = bot_data.get("parliamentary_modifications", [])
    if mods:
        blocks.append("### Parlamentarische Änderungen (from Botschaft record)")
        for m in mods:
            council = m.get("council", "")
            date = m.get("date", "")
            change = m.get("change", m.get("text", ""))
            blocks.append(f"- {council}, {date}: {change}")
        blocks.append("")

    if len(blocks) <= 2:
        return ""

    blocks.append(
        "Ground the Entstehungsgeschichte in these actual sources. "
        "Cite BBl page references for the Botschaft. "
        "Attribute parliamentary statements to named speakers. "
        "Trace where courts have confirmed or departed from legislative intent."
    )

    return "\n".join(blocks)
