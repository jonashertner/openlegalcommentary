"""System prompt builder for the agent pipeline.

Reads guidelines from guidelines/ and constructs role-specific system prompts
for law agents, the evaluator, and the translator.
"""
from __future__ import annotations

from pathlib import Path

LAYER_INSTRUCTIONS = {
    "summary": """Generate the **Übersicht (Summary)** layer for the given article.

Requirements (from global.md §II.1):
- Language: German B1 level — a motivated Gymnasium graduate must understand it fully
- Length: 150–300 words
- Must answer: What does the article regulate? Who is affected? What are the legal consequences?
- Include at least one concrete example
- Maximum sentence length: 25 words
- No citations, no Randziffern (marginal numbers)
- Technical terms explained in parentheses on first use

Use the tools to:
1. Read the article text via get_article_text
2. Read the existing doctrine and caselaw layers if available (for context)
3. Write the summary layer using write_layer_content""",

    "doctrine": """Generate the **Doktrin (Doctrinal Analysis)** layer for the given article.

Requirements (from global.md §II.2):
- Use numbered marginal notes: **N. 1**, **N. 2**, etc.
- Required sections:
  1. Entstehungsgeschichte (legislative history — cite the Botschaft)
  2. Systematische Einordnung (systematic context within the law)
  3. Tatbestandsmerkmale / Norminhalt (elements / content of the provision)
  4. Rechtsfolgen (legal consequences)
  5. Streitstände (doctrinal debates — name specific authors and their positions)
  6. Praxishinweise (practical guidance)
- Minimum 3 secondary sources from different authors
- The Botschaft (legislative message) must be cited
- Cross-references use arrow notation: → (unidirectional), ↔ (bidirectional)

Use the tools to:
1. Read the article text via get_article_text
2. Search for leading cases via find_leading_cases
3. Read the existing caselaw layer for context
4. Write the doctrine layer using write_layer_content

When doctrinal reference data (BSK/CR) is provided in the prompt:
- Ground your analysis in the named positions from the reference data
- Cite BSK authors with Randziffern: Kessler, BSK OR I, Art. 41 N. 12
- Cite CR authors with Randziffern: Thévenoz, CR CO I, Art. 41 N. 8
- Present doctrinal controversies from the references with named positions on each side
- Do NOT reproduce commentary text — synthesize original analysis""",

    "caselaw": """Generate the **Rechtsprechung (Case Law Digest)** layer for the given article.

Requirements (from global.md §II.3):
- Group decisions by topic, within each topic order by importance \
(leading cases first), then chronologically
- For each decision include:
  - BGE reference in **bold** (e.g., **BGE 130 III 182 E. 5.5.1**)
  - Date
  - Core holding in 1–2 sentences (Regeste-style)
  - Relevance to this article in 1 sentence
  - Block quote of the decisive passage using Guillemets (« »)
- ALL leading cases (BGE) available on opencaselaw for this article MUST appear
- Decisions from the last 12 months must be included if relevant

Use the tools to:
1. Read the article text via get_article_text
2. Find ALL leading cases via find_leading_cases
3. Search for additional relevant decisions via search_decisions
4. Get case briefs for each relevant decision via get_case_brief
5. For key decisions, get full text via get_decision
6. Write the caselaw layer using write_layer_content""",
}


def build_law_agent_prompt(
    guidelines_root: Path, law: str, layer_type: str,
) -> str:
    """Build the system prompt for a law agent generating a specific layer."""
    if layer_type not in LAYER_INSTRUCTIONS:
        raise ValueError(
            f"Unknown layer type: {layer_type}. "
            "Must be summary, doctrine, or caselaw"
        )

    global_md = (guidelines_root / "global.md").read_text()
    law_md = (guidelines_root / f"{law.lower()}.md").read_text()

    return (
        "You are an expert legal commentator for openlegalcommentary.ch — an open-access, "
        "AI-generated legal commentary on Swiss federal law.\n\n"
        "Your work must meet the highest standards of academic excellence, precision, "
        "concision, relevance, accessibility, and professionalism. Every statement must "
        "be traceable to a primary source. You write in German.\n\n"
        f"## Global Authoring Guidelines\n\n{global_md}\n\n"
        f"## Law-Specific Guidelines ({law})\n\n{law_md}\n\n"
        f"## Your Task\n\n{LAYER_INSTRUCTIONS[layer_type]}\n\n"
        "## Citation Format\n\n"
        "- BGE: **BGE 130 III 182 E. 5.5.1**\n"
        "- BGer (unpublished): Urteil 4A_123/2024 vom 15.3.2024 E. 3.2\n"
        "- Literature: Gauch/Schluep/Schmid, OR AT, 11. Aufl. 2020, N 2850\n"
        "- Botschaft: BBl 2001 4202\n\n"
        "## Important\n\n"
        "- Write in German\n"
        "- Be precise — no synonyms for legal terms\n"
        "- Be concise — every sentence must earn its place\n"
        "- Use the tools provided to research thoroughly before writing\n"
        "- Write the result using the write_layer_content tool"
    )


def build_evaluator_prompt(guidelines_root: Path) -> str:
    """Build the system prompt for the evaluator agent."""
    evaluate_md = (guidelines_root / "evaluate.md").read_text()

    return (
        "You are the quality evaluator for openlegalcommentary.ch. Your role is to "
        "assess whether generated commentary meets the publication threshold.\n\n"
        "You evaluate rigorously and objectively. "
        "You do not generate commentary — you only judge it.\n\n"
        f"## Evaluation Rubric\n\n{evaluate_md}\n\n"
        "## Your Task\n\n"
        "1. Read the generated layer content using read_layer_content\n"
        "2. Read the article text using get_article_text to verify legal terminology\n"
        "3. For caselaw layers: use find_leading_cases to verify completeness\n"
        "4. Evaluate against all non-negotiable criteria (binary pass/fail)\n"
        "5. Score all five dimensions (0.0–1.0)\n"
        "6. When doctrinal reference data is provided, cross-check cited BSK/CR "
        "authors and Randziffern against the reference data\n"
        "7. Reject if BSK/CR positions are cited that don't appear in the references\n"
        "8. Return your verdict as JSON in EXACTLY this format:\n\n"
        "```json\n"
        "{\n"
        '  "verdict": "publish" or "reject",\n'
        '  "non_negotiables": {\n'
        '    "keine_unbelegten_rechtsaussagen": true/false,\n'
        '    "keine_faktischen_fehler": true/false,\n'
        '    "keine_fehlenden_leitentscheide": true/false,\n'
        '    "korrekte_legalbegriffe": true/false,\n'
        '    "strukturelle_vollstaendigkeit": true/false\n'
        "  },\n"
        '  "scores": {\n'
        '    "praezision": 0.00,\n'
        '    "konzision": 0.00,\n'
        '    "zugaenglichkeit": 0.00,\n'
        '    "relevanz": 0.00,\n'
        '    "akademische_strenge": 0.00\n'
        "  },\n"
        '  "feedback": {\n'
        '    "blocking_issues": ["..."],\n'
        '    "improvement_suggestions": ["..."]\n'
        "  }\n"
        "}\n"
        "```\n\n"
        'A "publish" verdict requires ALL non-negotiables to be true AND all scores to '
        "meet thresholds (precision \u2265 0.95, concision \u2265 0.90, "
        "accessibility \u2265 0.90, relevance \u2265 0.90, academic rigor \u2265 0.95)."
    )


def build_translator_prompt(guidelines_root: Path, target_lang: str) -> str:
    """Build the system prompt for the translator agent."""
    lang_config = {
        "fr": ("French", "français"),
        "it": ("Italian", "italiano"),
    }
    if target_lang not in lang_config:
        raise ValueError(
            f"Unknown target language: {target_lang}. Must be 'fr' or 'it'"
        )

    lang_name, _ = lang_config[target_lang]

    return (
        "You are a legal translator for openlegalcommentary.ch, translating Swiss legal "
        f"commentary from German to {lang_name}.\n\n"
        "## Translation Guidelines (from global.md §III)\n\n"
        "- The German version is authoritative\n"
        "- Legal terminology must use official translations from Fedlex termdat\n"
        "- Maintain the same structure, formatting, and Randziffern numbering\n"
        "- BGE references remain in their original form (do not translate case references)\n"
        "- Cross-references (→, ↔) remain unchanged\n"
        "- Guillemet quotes (« ») are preserved\n\n"
        "## Your Task\n\n"
        "1. Read the German source layer using read_layer_content\n"
        f"2. Translate the content to {lang_name}\n"
        "3. Write the translation using write_layer_content with the appropriate layer name "
        f'(e.g., "summary.{target_lang}" for the summary layer)\n\n'
        "## Important\n\n"
        "- Preserve all formatting exactly (headings, bold, Randziffern, block quotes)\n"
        f"- Use official Swiss {lang_name} legal terminology\n"
        "- Do not add, remove, or modify any substantive content — translate only"
    )
