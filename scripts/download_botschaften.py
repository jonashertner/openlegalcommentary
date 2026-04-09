"""Download Botschaft PDFs from the registry to data/botschaften/.

Reads scripts/preparatory_materials/registry.json, collects all unique Botschaften
(deduplicated by bbl_ref_normalized), and downloads each PDF.

PDFs are fetched via the Fedlex filestore (admin.ch direct URLs are blocked by
CloudFront WAF). A SPARQL query to Fedlex resolves each BBl ref to an ELI path,
which is then used to build the filestore URL.

Usage:
    uv run python -m scripts.download_botschaften
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import httpx

REGISTRY_PATH = Path("scripts/preparatory_materials/registry.json")
OUTPUT_DIR = Path("data/botschaften")

SPARQL_ENDPOINT = "https://fedlex.data.admin.ch/sparqlendpoint"
FEDLEX_FILESTORE_BASE = "https://fedlex.data.admin.ch/filestore/fedlex.data.admin.ch"

# Delay between SPARQL requests to be polite to the endpoint
SPARQL_RATE_LIMIT_SECONDS = 1.0


def parse_bbl_ref(bbl_ref_normalized: str) -> tuple[str, str] | None:
    """Parse a normalised BBl ref and return (year, page) or None.

    Handles formats:
      - "BBl 1999 6013"   → ("1999", "6013")
      - "BBl 1997 I 1"    → ("1997", "1")   (Roman-volume refs)
      - "BBl 2017 399"    → ("2017", "399")
    """
    # Strip leading "BBl " prefix (case-insensitive)
    text = bbl_ref_normalized.strip()
    m = re.match(r"BBl\s+(\d{4})\s+(?:[IVX]+\s+)?(\d+)", text, re.IGNORECASE)
    if m:
        return m.group(1), m.group(2)
    return None


def resolve_fedlex_eli(client: httpx.Client, year: str, page: str) -> str | None:
    """Query Fedlex SPARQL to find the ELI path for a BBl ref.

    Returns the ELI path (e.g. "eli/fga/1999/1_6013_5331_4983") or None.
    Only base ELI URIs are considered — language/doc suffixes are filtered out.
    """
    sparql = f"""
SELECT ?s WHERE {{
  ?s ?p ?o .
  FILTER(CONTAINS(str(?s), '/fga/{year}') && CONTAINS(str(?s), '{page}'))
}} LIMIT 50
"""
    try:
        response = client.get(
            SPARQL_ENDPOINT,
            params={"query": sparql},
            headers={"Accept": "application/sparql-results+json"},
        )
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPStatusError, httpx.RequestError, json.JSONDecodeError) as exc:
        print(f"    SPARQL error for year={year} page={page}: {exc}")
        return None

    # ELI base URI pattern: ends with /fga/{year}/{id}  (no language/doc suffix)
    eli_base_pattern = re.compile(
        r"https://fedlex\.data\.admin\.ch/(eli/fga/\d{4}/[^/]+)$"
    )

    candidates: list[str] = []
    for binding in data.get("results", {}).get("bindings", []):
        uri = binding.get("s", {}).get("value", "")
        m = eli_base_pattern.match(uri)
        if m:
            eli_path = m.group(1)
            # Confirm the page number appears as a component of the ELI id
            # ELI id format: 1_{de_page}_{fr_page}_{it_page}  or  {de_page}
            eli_id = eli_path.split("/")[-1]
            parts = eli_id.split("_")
            if page in parts:
                candidates.append(eli_path)

    if not candidates:
        return None

    # Prefer the shortest / most canonical ELI path if there are multiple hits
    return sorted(candidates, key=len)[0]


def build_fedlex_filestore_url(eli_path: str) -> str:
    """Construct the Fedlex filestore PDF URL from an ELI path.

    eli_path example: "eli/fga/1999/1_6013_5331_4983"
    """
    dashed = eli_path.replace("/", "-")
    return (
        f"{FEDLEX_FILESTORE_BASE}/{eli_path}/de/pdf-a/"
        f"fedlex-data-admin-ch-{dashed}-de-pdf-a.pdf"
    )


def collect_botschaften(registry: dict) -> list[dict]:
    """Collect unique Botschaften from the registry, deduplicated by bbl_ref_normalized."""
    seen: set[str] = set()
    result: list[dict] = []

    for law, affairs in registry.items():
        for affair in affairs:
            for botschaft in affair.get("botschaften", []):
                key = botschaft.get("bbl_ref_normalized", "")
                if not key or key in seen:
                    continue
                seen.add(key)
                result.append(botschaft)

    return result


def download_pdf(client: httpx.Client, url: str, dest: Path) -> bool:
    """Download a PDF from url to dest. Returns True on success.

    Validates that the downloaded file starts with the PDF magic bytes %PDF.
    """
    try:
        response = client.get(url, follow_redirects=True)
        response.raise_for_status()
        content = response.content
        if not content.startswith(b"%PDF"):
            print(f"  ERROR: Response from {url} does not appear to be a PDF (no %PDF header)")
            return False
        dest.write_bytes(content)
        return True
    except httpx.HTTPStatusError as exc:
        print(f"  ERROR: HTTP {exc.response.status_code} for {url}")
        return False
    except httpx.RequestError as exc:
        print(f"  ERROR: Request failed for {url}: {exc}")
        return False


def main() -> None:
    """Read registry, download PDFs via Fedlex filestore, report stats."""
    if not REGISTRY_PATH.exists():
        print(f"Registry not found at {REGISTRY_PATH}. Run scripts/discover_botschaften.py first.")
        return

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    botschaften = collect_botschaften(registry)
    print(f"Found {len(botschaften)} unique Botschaften in registry.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    skipped = 0
    failed = 0

    with httpx.Client(timeout=120.0) as client:
        for botschaft in botschaften:
            key = botschaft.get("bbl_ref_normalized", "")
            fallback_url: str = botschaft.get("pdf_url", "") or ""

            dest = OUTPUT_DIR / f"{key}.pdf"
            if dest.exists():
                print(f"  SKIP [{key}]: already downloaded")
                skipped += 1
                continue

            # --- Step 1: try to resolve via Fedlex SPARQL ---
            parsed = parse_bbl_ref(key)
            fedlex_url: str | None = None

            if parsed:
                year, page = parsed
                print(f"  Resolving [{key}] via Fedlex SPARQL (year={year}, page={page}) ...")
                time.sleep(SPARQL_RATE_LIMIT_SECONDS)
                eli_path = resolve_fedlex_eli(client, year, page)
                if eli_path:
                    fedlex_url = build_fedlex_filestore_url(eli_path)
                    print(f"    ELI: {eli_path}")
                else:
                    print(f"    No ELI found in Fedlex for [{key}]")
            else:
                print(f"  Could not parse BBl ref [{key}], skipping SPARQL lookup")

            # --- Step 2: pick URL to try ---
            if fedlex_url:
                url_to_try = fedlex_url
            elif fallback_url and "null" not in fallback_url:
                # Upgrade http:// to https://
                if fallback_url.startswith("http://"):
                    fallback_url = "https://" + fallback_url[len("http://"):]
                url_to_try = fallback_url
                print(f"    Falling back to original URL: {url_to_try}")
            else:
                print(f"  SKIP [{key}]: no resolvable URL")
                skipped += 1
                continue

            # --- Step 3: download ---
            print(f"  Downloading [{key}] from {url_to_try}")
            success = download_pdf(client, url_to_try, dest)
            if success:
                size_kb = dest.stat().st_size // 1024
                print(f"    -> saved {dest} ({size_kb} KB)")
                downloaded += 1
            else:
                # If Fedlex filestore failed, try fallback URL as last resort
                can_fallback = (
                    fedlex_url and fallback_url
                    and "null" not in fallback_url
                    and url_to_try != fallback_url
                )
                if can_fallback:
                    if fallback_url.startswith("http://"):
                        fallback_url = "https://" + fallback_url[len("http://"):]
                    print(f"    Fedlex download failed, trying fallback: {fallback_url}")
                    success = download_pdf(client, fallback_url, dest)
                    if success:
                        size_kb = dest.stat().st_size // 1024
                        print(f"    -> saved {dest} ({size_kb} KB)")
                        downloaded += 1
                        continue
                failed += 1

    total = downloaded + skipped + failed
    print(f"\nDone: {total} total | {downloaded} downloaded | {skipped} skipped | {failed} failed")


if __name__ == "__main__":
    main()
