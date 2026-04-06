"""Extract text from Botschaft PDFs using PyMuPDF.

Reads all PDFs from data/botschaften/, extracts text with page markers,
cleans up hyphenation and BBl headers, and writes .txt files alongside the PDFs.

Usage:
    uv run python -m scripts.extract_botschaften
"""
from __future__ import annotations

import re
from pathlib import Path

import pymupdf

PDF_DIR = Path("data/botschaften")

# Matches standalone page numbers (digits only) or short BBl header lines like "BBl 1999"
_RE_PAGE_NUMBER = re.compile(r"^\d+$")
_RE_BBL_HEADER = re.compile(r"^BBl\s+\d{4}$", re.IGNORECASE)


def clean_extracted_text(text: str) -> str:
    """Clean raw extracted PDF text.

    - Rejoins hyphenated line breaks: "Bundes-\\nrechts" -> "Bundesrechts"
    - Removes lines that are only page numbers (bare integers)
    - Removes short BBl header lines like "BBl 1999"
    """
    # Rejoin hyphenated line breaks first
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # Filter out pure page-number lines and BBl header lines
    lines = text.split("\n")
    cleaned_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if _RE_PAGE_NUMBER.match(stripped):
            continue
        if _RE_BBL_HEADER.match(stripped):
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def extract_pdf(pdf_path: Path) -> str:
    """Extract text from a PDF file with [Page N] markers per page.

    Uses pymupdf.open() and page.get_text("text") for extraction.
    Returns the full extracted and cleaned text as a string.
    """
    parts: list[str] = []
    with pymupdf.open(str(pdf_path)) as doc:
        for page_num, page in enumerate(doc, start=1):
            raw = page.get_text("text")
            cleaned = clean_extracted_text(raw)
            parts.append(f"[Page {page_num}]\n{cleaned}")
    return "\n\n".join(parts)


def main() -> None:
    """Process all PDFs in data/botschaften/, write .txt files, flag low-density results."""
    if not PDF_DIR.exists():
        print(f"PDF directory not found: {PDF_DIR}. Run scripts/download_botschaften.py first.")
        return

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {PDF_DIR}.")
        return

    print(f"Found {len(pdf_files)} PDF(s) to process.")

    processed = 0
    skipped = 0
    low_density: list[str] = []

    for pdf_path in pdf_files:
        txt_path = pdf_path.with_suffix(".txt")
        if txt_path.exists():
            print(f"  SKIP [{pdf_path.stem}]: .txt already exists")
            skipped += 1
            continue

        print(f"  Extracting [{pdf_path.stem}]...")
        try:
            with pymupdf.open(str(pdf_path)) as doc:
                num_pages = len(doc)

            text = extract_pdf(pdf_path)
            txt_path.write_text(text, encoding="utf-8")

            chars = len(text)
            chars_per_page = chars / num_pages if num_pages > 0 else 0

            if chars_per_page < 1000:
                low_density.append(pdf_path.stem)
                print(
                    f"    WARNING: low text density ({chars_per_page:.0f} chars/page avg) "
                    f"— may be scanned/image PDF"
                )
            else:
                print(f"    -> {txt_path} ({chars} chars, {chars_per_page:.0f} chars/page avg)")

            processed += 1
        except Exception as exc:
            print(f"  ERROR extracting {pdf_path.name}: {exc}")

    print(f"\nDone: {processed} extracted | {skipped} skipped")
    if low_density:
        print(f"Low text density (< 1000 chars/page): {', '.join(low_density)}")


if __name__ == "__main__":
    main()
