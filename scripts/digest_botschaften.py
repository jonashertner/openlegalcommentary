"""Digest extracted Botschaft texts through Claude to produce per-article structured JSON.

Reads extracted .txt files from data/botschaften/, queries Claude Opus per-law,
and writes structured per-article digests to scripts/preparatory_materials/{law}.json.

Usage:
    uv run python -m scripts.digest_botschaften --law BGFA
    uv run python -m scripts.digest_botschaften --law OR --max-budget 100
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path

import anthropic

REGISTRY_PATH = Path("scripts/preparatory_materials/registry.json")
TEXT_DIR = Path("data/botschaften")
OUTPUT_DIR = Path("scripts/preparatory_materials")
ARTICLE_LISTS_PATH = Path("scripts/article_lists.json")

DEFAULT_MODEL = "claude-opus-4-6"
DEFAULT_MAX_BUDGET = 50.0

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

DIGEST_SYSTEM_PROMPT = """\
You are a Swiss legal expert analyzing Botschaft (Federal Council message) texts
to extract structured legislative history data for a commentary database.

Given a Botschaft text and a list of article numbers for a Swiss federal law,
extract the following per article and for the general context:

For each article mentioned:
- legislative_intent: The primary purpose and goal of the provision as stated in the Botschaft
- key_arguments: Main arguments given for the provision (list of strings)
- design_choices: Specific design decisions made (e.g. thresholds, scope choices,
  procedural choices) (list of strings)
- rejected_alternatives: Alternative approaches that were considered but rejected
  (list of strings)
- bbl_page_refs: Page references in the BBl where this article is discussed
  (list of strings, e.g. ["6045", "6046-6048"])
- general_context: Brief note on how this article fits into the broader law (string)

For the general context (Allgemeiner Teil / general section):
- problem_statement: The problem or gap in the law this legislation addresses
- solution_overview: Overview of the legislative solution chosen
- international_comparison: Any references to foreign law or international models

Return ONLY valid JSON in this exact structure:
{
  "articles": {
    "<article_number>": {
      "legislative_intent": "...",
      "key_arguments": ["...", "..."],
      "design_choices": ["...", "..."],
      "rejected_alternatives": ["...", "..."],
      "bbl_page_refs": ["...", "..."],
      "general_context": "..."
    }
  },
  "general_context": {
    "problem_statement": "...",
    "solution_overview": "...",
    "international_comparison": "..."
  }
}

Only include articles that are actually discussed in the text.
If an article is not mentioned, omit it from the output.
Use the article numbers as strings (e.g. "12", "12a").
"""


def load_article_numbers(law: str) -> list[str]:
    """Load article number strings for the given law.

    Tries article_lists.json first, falls back to scanning content directory.
    """
    if ARTICLE_LISTS_PATH.exists():
        data = json.loads(ARTICLE_LISTS_PATH.read_text(encoding="utf-8"))
        law_data = data.get(law, {})
        articles = law_data.get("articles", [])
        nums = [a["raw"] for a in articles if a.get("raw")]
        if nums:
            return nums

    # Fallback: scan content directory
    content_dir = Path("content") / law.lower()
    if content_dir.exists():
        nums = []
        for d in sorted(content_dir.iterdir()):
            if d.is_dir() and d.name.startswith("art-"):
                # art-001 -> "1", art-012a -> "12a"
                raw = d.name[4:].lstrip("0") or "0"
                nums.append(raw)
        return nums

    return []


def load_article_titles(law: str) -> dict[str, str]:
    """Load article number → title mapping from meta.yaml files.

    Returns a dict like {"1": "Schweizerische Eidgenossenschaft", "8": "Rechtsgleichheit"}.
    Used to help Claude map Botschaft sections (which use draft numbering)
    to the correct final article numbers.
    """
    import yaml

    titles: dict[str, str] = {}
    content_dir = Path("content") / law.lower()
    if not content_dir.exists():
        return titles
    for d in sorted(content_dir.iterdir()):
        if not d.is_dir() or not d.name.startswith("art-"):
            continue
        meta_path = d / "meta.yaml"
        if not meta_path.exists():
            continue
        meta = yaml.safe_load(meta_path.read_text())
        raw = d.name[4:].lstrip("0") or "0"
        title = meta.get("title", "")
        if title:
            titles[raw] = title
    return titles


def _repair_json(raw: str) -> str:
    """Best-effort repair of common LLM JSON formatting errors.

    Handles: trailing commas before ``}`` or ``]``, truncated output
    (unclosed braces/brackets), and stray control characters.
    """
    # Remove trailing commas before closing braces/brackets
    repaired = re.sub(r",\s*([}\]])", r"\1", raw)
    # Close any unclosed braces/brackets (truncated output)
    open_braces = repaired.count("{") - repaired.count("}")
    open_brackets = repaired.count("[") - repaired.count("]")
    if open_braces > 0 or open_brackets > 0:
        # Close innermost structures first
        repaired += "]" * max(0, open_brackets)
        repaired += "}" * max(0, open_braces)
    return repaired


def digest_botschaft(
    client: anthropic.Anthropic,
    text: str,
    bbl_ref: str,
    article_numbers: list[str],
    model: str = DEFAULT_MODEL,
    article_titles: dict[str, str] | None = None,
) -> dict:
    """Send a Botschaft text to Claude and parse the structured JSON response.

    Returns a dict with 'articles' and 'general_context' keys.
    Handles JSON code blocks, trailing commas, and truncated output
    (unclosed braces from hitting max_tokens).
    """
    # Build the article list with titles to help Claude map draft numbering
    # to final article numbers. Without titles, Claude maps Botschaft sections
    # (which use draft VE 96 numbering) to the wrong final articles.
    if article_titles:
        articles_lines = []
        for num in article_numbers[:80]:
            title = article_titles.get(num, "")
            articles_lines.append(f"  Art. {num}: {title}" if title else f"  Art. {num}")
        articles_str = "\n".join(articles_lines)
    else:
        articles_str = ", ".join(article_numbers[:50]) if article_numbers else "(unknown)"

    user_prompt = (
        f"Botschaft reference: {bbl_ref}\n\n"
        f"IMPORTANT: The Botschaft may use DRAFT article numbers that differ "
        f"from the FINAL law. Use the article TITLES below to match each "
        f"Botschaft section to the correct FINAL article number. For example, "
        f"if the Botschaft discusses 'Rechtsgleichheit' under a different "
        f"article number, map it to the FINAL article that has "
        f"'Rechtsgleichheit' as its title.\n\n"
        f"Final law articles to look for:\n{articles_str}\n\n"
        f"--- BEGIN BOTSCHAFT TEXT ---\n{text}\n--- END BOTSCHAFT TEXT ---"
    )

    with client.messages.stream(
        model=model,
        max_tokens=32768,
        system=DIGEST_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        response_text = stream.get_final_text()
        response = stream.get_final_message()

    # Handle ```json ... ``` code blocks
    json_match = re.search(r"```json\s*([\s\S]*?)```", response_text)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        # Try to extract raw JSON object
        json_match = re.search(r"\{[\s\S]*\}", response_text)
        if json_match:
            json_str = json_match.group(0)
        else:
            raise ValueError(f"No JSON found in response: {response_text[:200]}")

    # First try direct parse
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        # Attempt repair (trailing commas, unclosed structures)
        repaired = _repair_json(json_str)
        data = json.loads(repaired)

    return {
        "articles": data.get("articles", {}),
        "general_context": data.get("general_context", {}),
        "usage": {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        },
    }


def merge_digests(existing: dict, new_digest: dict, bbl_ref: str) -> dict:
    """Merge a new digest (from one Botschaft) into the existing articles dict.

    Each article accumulates sources from multiple Botschaften.
    """
    for art_num, art_data in new_digest.get("articles", {}).items():
        if art_num not in existing:
            existing[art_num] = {
                "provisions_discussed": [f"Art. {art_num}"],
                "sources": [],
                "parliamentary_modifications": [],
            }
        source_entry = {
            "bbl_ref": bbl_ref,
            "bbl_page_refs": art_data.get("bbl_page_refs", []),
            "legislative_intent": art_data.get("legislative_intent", ""),
            "key_arguments": art_data.get("key_arguments", []),
            "design_choices": art_data.get("design_choices", []),
            "rejected_alternatives": art_data.get("rejected_alternatives", []),
            "general_context": art_data.get("general_context", ""),
        }
        existing[art_num]["sources"].append(source_entry)
    return existing


def add_parliamentary_data(articles: dict, registry_affairs: list[dict]) -> dict:
    """Add parliamentary resolution data to articles from registry affairs."""
    # Collect all resolutions across all affairs
    all_resolutions: list[dict] = []
    for affair in registry_affairs:
        for resolution in affair.get("resolutions", []):
            all_resolutions.append(resolution)

    if not all_resolutions:
        return articles

    # Add resolutions to all articles (they apply law-wide, not per-article)
    for art_num in articles:
        existing = articles[art_num].get("parliamentary_modifications", [])
        for res in all_resolutions:
            entry = {
                "council": res.get("council", ""),
                "date": res.get("date", ""),
                "text": res.get("text", ""),
            }
            if entry not in existing:
                existing.append(entry)
        articles[art_num]["parliamentary_modifications"] = existing

    return articles


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Rough cost estimate in USD for Claude Opus."""
    return (input_tokens * 15 + output_tokens * 75) / 1_000_000


def main() -> None:
    """Main entry point: parse args, load registry, process Botschaften, write output."""
    parser = argparse.ArgumentParser(
        description="Digest Botschaft texts per article using Claude",
    )
    parser.add_argument(
        "--law",
        required=True,
        choices=list(SR_NUMBERS.keys()),
        help="Law abbreviation (e.g. BGFA, OR)",
    )
    parser.add_argument(
        "--max-budget",
        type=float,
        default=DEFAULT_MAX_BUDGET,
        help=f"Maximum spend in USD (default: {DEFAULT_MAX_BUDGET})",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Claude model to use (default: {DEFAULT_MODEL})",
    )
    args = parser.parse_args()

    law = args.law
    max_budget = args.max_budget
    model = args.model

    # Load registry
    if not REGISTRY_PATH.exists():
        print(f"Registry not found at {REGISTRY_PATH}. Run scripts/discover_botschaften.py first.")
        return

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    # Registry structure: registry[law] = [affairs_list] (flat)
    # or registry["laws"][law]["affairs"] (nested). Handle both.
    if "laws" in registry:
        law_affairs = registry["laws"].get(law, {}).get("affairs", [])
    else:
        raw = registry.get(law, [])
        law_affairs = raw if isinstance(raw, list) else raw.get("affairs", [])
    if not law_affairs:
        print(f"No affairs found for {law} in registry.")
        return

    # Collect unique Botschaften for this law
    seen_refs: set[str] = set()
    botschaften_to_process: list[dict] = []
    for affair in law_affairs:
        for botschaft in affair.get("botschaften", []):
            key = botschaft.get("bbl_ref_normalized", "")
            if key and key not in seen_refs:
                seen_refs.add(key)
                botschaften_to_process.append(botschaft)

    if not botschaften_to_process:
        print(f"No Botschaften found in registry for {law}.")
        return

    print(f"Found {len(botschaften_to_process)} unique Botschaft(en) for {law}.")

    # Load article numbers and titles
    article_numbers = load_article_numbers(law)
    article_titles = load_article_titles(law)
    n_nums = len(article_numbers)
    n_titles = len(article_titles)
    print(f"Loaded {n_nums} article numbers for {law} ({n_titles} with titles).")

    # Load existing output if present (for resume)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{law.lower()}.json"
    existing_output: dict = {}
    processed_refs: set[str] = set()

    if output_path.exists():
        try:
            existing_output = json.loads(output_path.read_text(encoding="utf-8"))
            # Collect already-processed bbl_refs from sources
            for art_data in existing_output.get("articles", {}).values():
                for source in art_data.get("sources", []):
                    processed_refs.add(source.get("bbl_ref", ""))
            print(f"Resuming: {len(processed_refs)} Botschaft(en) already processed.")
        except Exception as exc:
            print(f"Warning: could not load existing output ({exc}), starting fresh.")
            existing_output = {}

    articles: dict = existing_output.get("articles", {})
    sr_number = SR_NUMBERS[law]

    client = anthropic.Anthropic()
    total_cost = 0.0

    for botschaft in botschaften_to_process:
        bbl_ref = botschaft.get("bbl_ref", "")
        bbl_ref_normalized = botschaft.get("bbl_ref_normalized", "")

        if bbl_ref in processed_refs:
            print(f"  SKIP [{bbl_ref}]: already processed")
            continue

        # Try both filename formats: BBl ref (from download script) and normalized
        txt_path = TEXT_DIR / f"{bbl_ref}.txt"
        if not txt_path.exists():
            txt_path = TEXT_DIR / f"{bbl_ref_normalized}.txt"
        if not txt_path.exists():
            print(f"  SKIP [{bbl_ref}]: no extracted text at {txt_path}")
            continue

        if total_cost >= max_budget:
            print(f"Budget limit of ${max_budget:.2f} reached. Stopping.")
            break

        text = txt_path.read_text(encoding="utf-8")

        # Split long texts into chunks to stay within context limits.
        # ~400k chars ≈ ~100k tokens, safely under the 200k context.
        chunk_size = 400_000
        if len(text) <= chunk_size:
            chunks = [text]
        else:
            # Split at page boundaries (marked by [Page N]) to avoid
            # cutting mid-sentence. Fall back to raw char splits.
            chunks = []
            current = ""
            for line in text.split("\n"):
                if line.startswith("[Page ") and len(current) >= chunk_size:
                    chunks.append(current)
                    current = ""
                current += line + "\n"
            if current.strip():
                chunks.append(current)
            sizes = ", ".join(f"{len(c):,}" for c in chunks)
            print(f"  Split into {len(chunks)} chunks ({sizes} chars)")

        for chunk_idx, chunk in enumerate(chunks, 1):
            if len(chunks) > 1:
                chunk_label = f"[{bbl_ref} chunk {chunk_idx}/{len(chunks)}]"
            else:
                chunk_label = f"[{bbl_ref}]"
            print(f"  Digesting {chunk_label} ({len(chunk):,} chars)...")
            try:
                result = digest_botschaft(
                    client, chunk, bbl_ref, article_numbers, model,
                    article_titles=article_titles,
                )
            except Exception as exc:
                print(f"  ERROR processing {chunk_label}: {exc}")
                continue

            usage = result.pop("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            cost = estimate_cost(input_tokens, output_tokens)
            total_cost += cost

            if total_cost >= max_budget:
                print(f"Budget limit of ${max_budget:.2f} reached. Stopping.")
                break

            n_articles = len(result.get("articles", {}))
            print(
                f"    -> {n_articles} article(s) extracted | "
                f"{input_tokens}+{output_tokens} tokens | ${cost:.4f} | total: ${total_cost:.4f}"
            )

            articles = merge_digests(articles, result, bbl_ref)

            # Save incrementally after each chunk
            output_data = {
                "law": law,
                "sr_number": sr_number,
                "generated": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "articles": articles,
            }
            output_path.write_text(
                json.dumps(output_data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    # Final pass: add parliamentary data
    articles = add_parliamentary_data(articles, law_affairs)

    output_data = {
        "law": law,
        "sr_number": sr_number,
        "generated": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "articles": articles,
    }
    output_path.write_text(
        json.dumps(output_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nDone. {len(articles)} article(s) digested for {law}.")
    print(f"Output written to {output_path}")
    print(f"Total estimated cost: ${total_cost:.4f}")


if __name__ == "__main__":
    main()
