"""Pass 1: Extract raw text from BSK/CR PDFs and split into per-article chunks.

Usage:
    uv run python -m scripts.extract_commentary data/commentary_pdfs/bsk_or_i.pdf --volume bsk_or_i
    uv run python -m scripts.extract_commentary --all  # process all PDFs in data/commentary_pdfs/
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

VOLUME_CONFIG: dict[str, dict] = {
    "bsk_or_i": {"law": "OR", "source": "bsk", "article_range": (1, 529)},
    "bsk_or_ii": {"law": "OR", "source": "bsk", "article_range": (530, 1186)},
    "cr_co_i": {"law": "OR", "source": "cr", "article_range": (1, 529)},
    "bsk_bv": {"law": "BV", "source": "bsk", "article_range": (1, 197)},
    "bsk_stgb": {"law": "StGB", "source": "bsk", "article_range": (1, 401)},
    "bsk_zpo": {"law": "ZPO", "source": "bsk", "article_range": (1, 408)},
    "bsk_stpo": {"law": "StPO", "source": "bsk", "article_range": (1, 457)},
}

# Regex for article headers — matches "Art. 41", "Art. 6a", "Art. 706b" etc.
ART_HEADER_RE = re.compile(r"^Art\.\s+(\d+[a-z]?)\b", re.MULTILINE)


def clean_ocr_text(text: str) -> str:
    """Fix common OCR artifacts in extracted text."""
    # Normalize Randziffern spacing
    text = re.sub(r"N\.\s*(\d+)", r"N. \1", text)
    # Fix BGE double spaces
    text = re.sub(r"(BGE\s+\d+\s+[IVX]+)\s{2,}(\d+)", r"\1 \2", text)
    # Collapse excessive whitespace
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def split_articles(raw_text: str, law: str) -> dict[str, str]:
    """Split raw text into per-article chunks keyed by article number."""
    matches = list(ART_HEADER_RE.finditer(raw_text))
    if not matches:
        logger.warning("No article headers found in text for %s", law)
        return {}

    articles = {}
    for i, match in enumerate(matches):
        art_key = match.group(1)
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
        articles[art_key] = clean_ocr_text(raw_text[start:end])

    return articles


def extract_pdf(pdf_path: Path) -> str:
    """Extract all text from a PDF using PyMuPDF."""
    import pymupdf

    doc = pymupdf.open(str(pdf_path))
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return "\n".join(pages)


def process_volume(
    pdf_path: Path, volume_name: str, output_dir: Path,
) -> Path:
    """Extract and split a single BSK/CR volume."""
    config = VOLUME_CONFIG[volume_name]
    law = config["law"]
    source = config["source"]

    logger.info("Extracting %s (%s %s)...", volume_name, law, source)
    raw_text = extract_pdf(pdf_path)
    articles = split_articles(raw_text, law)
    logger.info("Found %d articles in %s", len(articles), volume_name)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{law.lower()}_{source}.json"

    # Merge with existing data (for multi-volume laws like OR I + OR II)
    existing = {}
    if output_path.exists():
        data = json.loads(output_path.read_text())
        existing = data.get(law.upper(), {})

    existing.update(articles)
    output = {law.upper(): existing}
    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
    )
    logger.info("Wrote %s", output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Extract raw text from BSK/CR PDFs",
    )
    parser.add_argument(
        "pdf_path", nargs="?", type=Path, help="Path to a single PDF",
    )
    parser.add_argument(
        "--volume", choices=VOLUME_CONFIG.keys(),
        help="Volume identifier",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Process all PDFs in data/commentary_pdfs/",
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("scripts/commentary_raw"),
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s: %(message)s",
    )

    if args.all:
        pdf_dir = Path("data/commentary_pdfs")
        for volume_name in VOLUME_CONFIG:
            pdf_path = pdf_dir / f"{volume_name}.pdf"
            if pdf_path.exists():
                process_volume(pdf_path, volume_name, args.output_dir)
            else:
                logger.warning("PDF not found: %s", pdf_path)
    elif args.pdf_path and args.volume:
        process_volume(args.pdf_path, args.volume, args.output_dir)
    else:
        parser.error("Provide --all or both pdf_path and --volume")


if __name__ == "__main__":
    main()
