"""Discover Botschaften (Federal Council messages) for all covered laws.

Queries the Swiss Parliament API to find Federal Council messages per law.

Queries ws-old.parlament.ch, performs BFS over relatedAffairs, and writes a
registry of found Botschaften to scripts/preparatory_materials/registry.json.

Usage:
    uv run python -m scripts.discover_botschaften
"""
from __future__ import annotations

import asyncio
import json
import re
from datetime import UTC, datetime
from pathlib import Path

import httpx

PARLIAMENT_API_BASE = "https://ws-old.parlament.ch"

# Seed affair IDs for each covered law (parliament affair numbers, no leading zeros)
SEED_AFFAIRS: dict[str, list[str]] = {
    "BV": ["19960091"],
    "ZGB": ["19940083", "20150046", "20180069"],
    "OR": ["20160077", "20080064"],
    "ZPO": ["20060062"],
    "StGB": ["19990063", "20100050"],
    "StPO": ["20060013"],
    "SchKG": ["19910089"],
    "VwVG": ["19650079"],
    "BGFA": ["19990027"],
}

SR_NUMBERS: dict[str, str] = {
    "BV": "101",
    "ZGB": "210",
    "OR": "220",
    "ZPO": "272",
    "StGB": "311.0",
    "StPO": "312.0",
    "SchKG": "281.1",
    "VwVG": "172.021",
    "BGFA": "935.61",
}


def normalize_bbl_ref(ref: str) -> str:
    """Normalize a BBl reference string to a slug.

    Examples:
        "BBl 2017 399"     -> "bbl-2017-399"
        "BBl 1999 IV 4462" -> "bbl-1999-IV-4462"
        "BBl  1999  6013"  -> "bbl-1999-6013"
    """
    # Strip leading "BBl" prefix (case-insensitive) and collapse whitespace
    stripped = re.sub(r"^BBl\s+", "", ref, flags=re.IGNORECASE)
    parts = stripped.split()
    return "bbl-" + "-".join(parts)


def _parse_dotnet_date(date_str: str) -> str | None:
    """Parse a .NET /Date(milliseconds+offset)/ or ISO 8601 date string.

    Returns an ISO 8601 date string (YYYY-MM-DD) or None if unparseable.
    """
    if not date_str:
        return None
    # .NET JSON date: /Date(1234567890000+0200)/
    m = re.match(r"^/Date\((-?\d+)([+-]\d{4})?\)/$", date_str)
    if m:
        ms = int(m.group(1))
        dt = datetime.fromtimestamp(ms / 1000, tz=UTC)
        return dt.date().isoformat()
    # ISO 8601 (e.g. "1999-09-01T00:00:00Z")
    iso_m = re.match(r"^(\d{4}-\d{2}-\d{2})", date_str)
    if iso_m:
        return iso_m.group(1)
    return None


def extract_affair_data(affair: dict) -> dict:
    """Extract structured data from a parliament API affair response.

    Returns a dict with keys:
        id, short_id, title, affair_type, state,
        botschaften, resolutions, committees, debate_documents, related_affair_ids
    """
    affair_id = str(affair.get("id", ""))
    short_id = affair.get("shortId", "")
    title = affair.get("title", "")
    affair_type_info = affair.get("affairType") or {}
    affair_type = affair_type_info.get("abbreviation", "")
    state_info = affair.get("state") or {}
    state = state_info.get("name", "")

    botschaften: list[dict] = []
    resolutions: list[dict] = []
    committees: list[dict] = []
    debate_documents: list[dict] = []

    seen_committees: set[str] = set()

    for draft in affair.get("drafts") or []:
        # --- References (Botschaften / BBl entries) ---
        for ref in draft.get("references") or []:
            ref_type = (ref.get("type") or {}).get("id")
            pub = ref.get("publication") or {}
            source = pub.get("source", "")
            # Skip null sources or non-BBl references
            if not source or "null" in source:
                continue
            pub_type = (pub.get("type") or {}).get("shortName", "")
            if pub_type != "BBl":
                continue
            pdf_url = pub.get("url", "")
            date_raw = ref.get("date", "")
            date_parsed = _parse_dotnet_date(date_raw)
            botschaften.append(
                {
                    "title": ref.get("title", ""),
                    "bbl_ref": source,
                    "bbl_ref_normalized": normalize_bbl_ref(source),
                    "pdf_url": pdf_url,
                    "year": pub.get("year", ""),
                    "page": pub.get("page", ""),
                    "date": date_parsed,
                    "reference_type_id": ref_type,
                }
            )

        # --- Resolutions ---
        consultation = draft.get("consultation") or {}
        for resolution in consultation.get("resolutions") or []:
            council_info = resolution.get("council") or {}
            council_name = council_info.get("name", "")
            date_raw = resolution.get("date", "")
            date_parsed = _parse_dotnet_date(date_raw)
            resolutions.append(
                {
                    "council": council_name,
                    "date": date_parsed,
                    "text": resolution.get("text", ""),
                }
            )

        # --- Pre-consultations (committees) ---
        for pre in draft.get("preConsultations") or []:
            committee_info = pre.get("committee") or {}
            abbreviation = committee_info.get("abbreviation", "")
            if abbreviation and abbreviation not in seen_committees:
                seen_committees.add(abbreviation)
                committees.append(
                    {
                        "abbreviation": abbreviation,
                        "name": committee_info.get("name", ""),
                        "council": (committee_info.get("council") or {}).get("name", ""),
                    }
                )

        # --- Debate documents (links) ---
        for link in draft.get("links") or []:
            link_type = (link.get("type") or {}).get("id")
            url = link.get("url", "")
            if url:
                debate_documents.append(
                    {
                        "type_id": link_type,
                        "title": link.get("title", ""),
                        "url": url,
                    }
                )

    # --- Related affair IDs ---
    related_affair_ids: list[str] = []
    for rel in affair.get("relatedAffairs") or []:
        rel_type = (rel.get("affairType") or {}).get("abbreviation", "")
        rel_id = rel.get("id")
        if rel_id and rel_type == "BRG":
            related_affair_ids.append(str(rel_id))

    return {
        "id": affair_id,
        "short_id": short_id,
        "title": title,
        "affair_type": affair_type,
        "state": state,
        "botschaften": botschaften,
        "resolutions": resolutions,
        "committees": committees,
        "debate_documents": debate_documents,
        "related_affair_ids": related_affair_ids,
    }


async def fetch_affair(client: httpx.AsyncClient, affair_id: str) -> dict | None:
    """Fetch a single affair from the parliament API by ID."""
    url = f"{PARLIAMENT_API_BASE}/affairs/{affair_id}"
    params = {"format": "json", "lang": "de"}
    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        print(f"  Warning: failed to fetch affair {affair_id}: {exc}")
        return None


async def discover_affairs_for_law(
    client: httpx.AsyncClient,
    law: str,
    seed_ids: list[str],
    max_depth: int = 2,
) -> list[dict]:
    """BFS discovery of affairs for a given law, starting from seed IDs.

    Follows relatedAffairs of type BRG up to max_depth levels.
    Filters to only affairs that have at least one Botschaft (BBl reference).
    Rate-limits to 1 request per second.
    """
    visited: set[str] = set()
    queue: list[tuple[str, int]] = [(aid, 0) for aid in seed_ids]
    results: list[dict] = []

    while queue:
        affair_id, depth = queue.pop(0)
        if affair_id in visited:
            continue
        visited.add(affair_id)

        print(f"  [{law}] Fetching affair {affair_id} (depth={depth})")
        raw = await fetch_affair(client, affair_id)
        await asyncio.sleep(1.0)  # rate-limit: 1 req/sec

        if raw is None:
            continue

        affair_type = (raw.get("affairType") or {}).get("abbreviation", "")
        if affair_type != "BRG":
            print(f"  [{law}] Skipping affair {affair_id}: type={affair_type!r} (not BRG)")
            continue

        data = extract_affair_data(raw)

        if data["botschaften"]:
            results.append(data)
        else:
            print(f"  [{law}] Affair {affair_id} has no Botschaften, skipping")

        if depth < max_depth:
            for related_id in data["related_affair_ids"]:
                if related_id not in visited:
                    queue.append((related_id, depth + 1))

    return results


async def build_registry() -> dict:
    """Discover all Botschaften for all covered laws and return a registry dict."""
    registry: dict[str, list[dict]] = {}
    headers = {"Accept": "application/json"}

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        for law, seed_ids in SEED_AFFAIRS.items():
            print(f"Discovering affairs for {law} (SR {SR_NUMBERS[law]})...")
            affairs = await discover_affairs_for_law(client, law, seed_ids)
            registry[law] = affairs
            print(f"  Found {len(affairs)} affair(s) with Botschaften for {law}")

    return registry


def main() -> None:
    """Run the discovery and write results to scripts/preparatory_materials/registry.json."""
    output_dir = Path(__file__).parent / "preparatory_materials"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "registry.json"

    print("Starting Botschaften discovery...")
    registry = asyncio.run(build_registry())

    total = sum(len(v) for v in registry.values())
    print(f"\nDiscovery complete: {total} affairs across {len(registry)} laws")

    output_path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Registry written to {output_path}")


if __name__ == "__main__":
    main()
