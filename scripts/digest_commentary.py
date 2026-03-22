"""Pass 2: Digest raw commentary text into structured reference data via Claude.

Usage:
    uv run python -m scripts.digest_commentary scripts/commentary_raw/or_refs.json
    uv run python -m scripts.digest_commentary --all
    uv run python -m scripts.digest_commentary scripts/commentary_raw/or_refs.json --resume
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import anthropic

from scripts.commentary_schema import ArticleRef, Controversy, Position

logger = logging.getLogger(__name__)

DIGESTION_PROMPT_TEMPLATE = """\
You are extracting structured reference data from a legal commentary article.

The text below is from a {source_type} commentary on Swiss law ({law}).
{lang_note}

Extract the following as JSON — do NOT summarize or paraphrase the text. Identify:

1. **authors**: List of author names for this article
2. **edition**: Full edition string (e.g., "Doctrinal OR I, 7. Aufl. 2019")
3. **randziffern_map**: Map of N. ranges to topics (e.g., "1-3": "Entstehungsgeschichte")
4. **positions**: List of named doctrinal positions, each with:
   - author: who holds this position
   - n: the Randziffer reference (e.g., "N. 12")
   - topic: what the position is about
   - position: one-sentence summary of the position
5. **controversies**: Doctrinal disagreements with at least 2 named positions
   - topic: what the debate is about
   - positions: dict mapping "Author (citation)" to their position
6. **cross_refs**: List of articles referenced (e.g., "Art. 97 OR")
7. **key_literature**: List of secondary sources cited

Return ONLY valid JSON matching this schema. No markdown, no explanation.

---

{text}"""


def build_digestion_prompt(text: str, law: str, lang: str) -> str:
    """Build the prompt for structured extraction."""
    source_type = (
        "leading commentary" if lang == "de"
        else "Commentaire Romand (CR)"
    )
    lang_note = ""
    if lang == "fr":
        lang_note = (
            "The source text is in French. "
            "Output all position summaries in German."
        )
    return DIGESTION_PROMPT_TEMPLATE.format(
        source_type=source_type, law=law, lang_note=lang_note, text=text,
    )


def parse_digest_response(response_text: str) -> ArticleRef:
    """Parse Claude's JSON response into a validated ArticleRef."""
    json_match = re.search(r"```json\s*([\s\S]*?)```", response_text)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        json_match = re.search(r"\{[\s\S]*\}", response_text)
        if json_match:
            json_str = json_match.group(0)
        else:
            raise ValueError(
                f"No JSON found in response: {response_text[:200]}",
            )

    data = json.loads(json_str)
    return ArticleRef(**data)


@dataclass
class DigestState:
    """Track which articles have been digested for resume support."""

    path: Path
    completed_keys: set[str] = field(default_factory=set)

    @classmethod
    def load(cls, path: Path) -> DigestState:
        state = cls(path=path)
        if path.exists():
            data = json.loads(path.read_text())
            state.completed_keys = set(data.get("completed", []))
        return state

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(
            {"completed": sorted(self.completed_keys)}, indent=2,
        ))

    def mark_completed(self, key: str) -> None:
        self.completed_keys.add(key)

    def is_completed(self, key: str) -> bool:
        return key in self.completed_keys


DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_MAX_INPUT_TOKENS = 20000
# Rough estimate: 1 token ≈ 4 chars for European languages
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Rough token count estimate."""
    return len(text) // CHARS_PER_TOKEN


def chunk_long_article(
    text: str, max_tokens: int,
) -> list[tuple[str, tuple[int, int] | None]]:
    """Split a long article into overlapping chunks with primary ranges.

    Returns list of (chunk_text, primary_n_range) tuples.
    primary_n_range is (start_n, end_n) — the N. range this chunk "owns"
    for deduplication. None if no chunking needed.
    """
    if estimate_tokens(text) <= max_tokens:
        return [(text, None)]

    # Find all Randziffern to determine split points
    rz_matches = list(re.finditer(r"\bN\.\s*(\d+)\b", text))
    if not rz_matches:
        # No Randziffern found — can't split intelligently, send as-is
        return [(text, None)]

    rz_numbers = [int(m.group(1)) for m in rz_matches]
    max_rz = max(rz_numbers)
    min_rz = min(rz_numbers)

    # Split into roughly equal chunks by character count
    chunk_size_chars = max_tokens * CHARS_PER_TOKEN
    overlap_chars = chunk_size_chars // 5  # 20% overlap

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size_chars, len(text))
        chunk_text = text[start:end]

        # Determine primary N. range for this chunk
        chunk_rz = [
            m for m in rz_matches
            if start <= m.start() < end - overlap_chars
        ]
        if chunk_rz:
            primary_start = int(chunk_rz[0].group(1))
            primary_end = int(chunk_rz[-1].group(1))
        else:
            primary_start = min_rz
            primary_end = max_rz

        chunks.append((chunk_text, (primary_start, primary_end)))

        if end >= len(text):
            break
        start = end - overlap_chars

    return chunks


def merge_chunk_results(
    chunk_results: list[tuple[ArticleRef, tuple[int, int] | None]],
) -> ArticleRef:
    """Merge multiple chunk digestion results into a single ArticleRef.

    Deduplication: positions are kept from the chunk whose primary range
    contains the referenced N. number. Cross-refs and literature are
    deduplicated by string equality.
    """
    if len(chunk_results) == 1:
        return chunk_results[0][0]

    # Use first chunk as base for authors/edition
    base = chunk_results[0][0]
    merged_rz_map: dict[str, str] = {}
    merged_positions: list[dict] = []
    merged_controversies: list[dict] = []
    seen_cross_refs: set[str] = set()
    seen_literature: set[str] = set()
    cross_refs: list[str] = []
    key_literature: list[str] = []

    for ref, primary_range in chunk_results:
        merged_rz_map.update(ref.randziffern_map)

        for p in ref.positions:
            # Extract N. number from position
            n_match = re.search(r"(\d+)", p.n)
            if n_match and primary_range:
                n_num = int(n_match.group(1))
                if not (primary_range[0] <= n_num <= primary_range[1]):
                    continue  # Skip — belongs to another chunk
            merged_positions.append(p.model_dump())

        for c in ref.controversies:
            merged_controversies.append(c.model_dump())

        for cr in ref.cross_refs:
            if cr not in seen_cross_refs:
                seen_cross_refs.add(cr)
                cross_refs.append(cr)

        for lit in ref.key_literature:
            if lit not in seen_literature:
                seen_literature.add(lit)
                key_literature.append(lit)

    return ArticleRef(
        authors=base.authors,
        edition=base.edition,
        randziffern_map=merged_rz_map,
        positions=[Position(**p) for p in merged_positions],
        controversies=[Controversy(**c) for c in merged_controversies],
        cross_refs=cross_refs,
        key_literature=key_literature,
    )


async def digest_article(
    client: anthropic.AsyncAnthropic,
    text: str,
    law: str,
    lang: str,
    model: str = DEFAULT_MODEL,
    max_input_tokens: int = DEFAULT_MAX_INPUT_TOKENS,
) -> ArticleRef:
    """Send a single article to Claude for structured extraction.

    Long articles are split into overlapping chunks and merged.
    """
    chunks = chunk_long_article(text, max_input_tokens)

    if len(chunks) == 1:
        prompt = build_digestion_prompt(chunks[0][0], law, lang)
        response = await client.messages.create(
            model=model, max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return parse_digest_response(response.content[0].text)

    # Multi-chunk: digest each, then merge
    logger.info("Splitting long article into %d chunks", len(chunks))
    chunk_results = []
    for chunk_text, primary_range in chunks:
        prompt = build_digestion_prompt(chunk_text, law, lang)
        response = await client.messages.create(
            model=model, max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        ref = parse_digest_response(response.content[0].text)
        chunk_results.append((ref, primary_range))

    return merge_chunk_results(chunk_results)


async def process_file(
    raw_path: Path,
    output_dir: Path,
    resume: bool = False,
    lang: str = "de",
    model: str = DEFAULT_MODEL,
    max_input_tokens: int = DEFAULT_MAX_INPUT_TOKENS,
) -> None:
    """Digest all articles in a raw extraction file."""
    data = json.loads(raw_path.read_text())
    # File has one top-level key (the law abbreviation)
    law = next(iter(data))
    articles = data[law]

    source = "refs" if "_refs" in raw_path.name else "cr"
    state_path = (
        raw_path.parent / f"{law.lower()}_{source}_digest_state.json"
    )
    state = DigestState.load(state_path) if resume else DigestState(state_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{law.lower()}_{source}.json"

    # Load existing output for incremental writes
    existing = {}
    if output_path.exists():
        existing_data = json.loads(output_path.read_text())
        existing = existing_data.get(law, {})

    client = anthropic.AsyncAnthropic()
    total = len(articles)
    completed = 0

    for art_key, text in articles.items():
        if state.is_completed(art_key):
            completed += 1
            continue

        try:
            ref = await digest_article(
                client, text, law, lang, model, max_input_tokens,
            )
            existing[art_key] = ref.model_dump()
            state.mark_completed(art_key)
            completed += 1
            logger.info(
                "[%d/%d] Digested %s Art. %s", completed, total, law, art_key,
            )
        except Exception:
            logger.exception("Failed to digest %s Art. %s", law, art_key)

        # Save after each article for crash safety
        output_path.write_text(json.dumps(
            {law: existing}, indent=2, ensure_ascii=False,
        ))
        state.save()

    logger.info(
        "Done: %d/%d articles for %s %s", completed, total, law, source,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Digest raw commentary into structured refs",
    )
    parser.add_argument(
        "raw_path", nargs="?", type=Path,
        help="Path to raw extraction JSON",
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Process all files in scripts/commentary_raw/",
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("scripts/commentary_refs"),
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Resume from previous state",
    )
    parser.add_argument(
        "--lang", default="de", choices=["de", "fr"],
        help="Source language",
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL,
        help="Claude model for digestion",
    )
    parser.add_argument(
        "--max-input-tokens", type=int, default=DEFAULT_MAX_INPUT_TOKENS,
        help="Max tokens per chunk",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s: %(message)s",
    )

    if args.all:
        raw_dir = Path("scripts/commentary_raw")
        for path in sorted(raw_dir.glob("*.json")):
            if "_digest_state" in path.name:
                continue
            lang = "fr" if "_cr" in path.name else "de"
            asyncio.run(process_file(
                path, args.output_dir, args.resume, lang,
                args.model, args.max_input_tokens,
            ))
    elif args.raw_path:
        asyncio.run(process_file(
            args.raw_path, args.output_dir, args.resume, args.lang,
            args.model, args.max_input_tokens,
        ))
    else:
        parser.error("Provide --all or a raw_path")


if __name__ == "__main__":
    main()
