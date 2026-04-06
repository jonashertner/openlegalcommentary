"""Download Botschaft PDFs from the registry to data/botschaften/.

Reads scripts/preparatory_materials/registry.json, collects all unique Botschaften
(deduplicated by bbl_ref_normalized), and downloads each PDF.

Usage:
    uv run python -m scripts.download_botschaften
"""
from __future__ import annotations

import json
from pathlib import Path

import httpx

REGISTRY_PATH = Path("scripts/preparatory_materials/registry.json")
OUTPUT_DIR = Path("data/botschaften")


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
    """Read registry, download PDFs, report stats."""
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

    with httpx.Client(timeout=60.0) as client:
        for botschaft in botschaften:
            key = botschaft.get("bbl_ref_normalized", "")
            url: str = botschaft.get("pdf_url", "") or ""

            if not url or "null" in url:
                print(f"  SKIP [{key}]: no valid URL")
                skipped += 1
                continue

            # Upgrade http:// to https://
            if url.startswith("http://"):
                url = "https://" + url[len("http://"):]

            dest = OUTPUT_DIR / f"{key}.pdf"
            if dest.exists():
                print(f"  SKIP [{key}]: already downloaded")
                skipped += 1
                continue

            print(f"  Downloading [{key}] from {url}")
            success = download_pdf(client, url, dest)
            if success:
                size_kb = dest.stat().st_size // 1024
                print(f"    -> saved {dest} ({size_kb} KB)")
                downloaded += 1
            else:
                failed += 1

    total = downloaded + skipped + failed
    print(f"\nDone: {total} total | {downloaded} downloaded | {skipped} skipped | {failed} failed")


if __name__ == "__main__":
    main()
