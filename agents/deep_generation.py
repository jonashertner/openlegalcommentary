"""Multi-pass deep generation for high-significance articles.

Instead of a single generation pass, Tier 1 and Tier 2 articles go through
specialized sub-agents that each produce a section:

  Pass 1: Research brief (agents/research_agent.py)
  Pass 2: Entstehungsgeschichte (legislative history)
  Pass 3: Systematic context + comparative law
  Pass 4: Norminhalt (doctrinal core, per-paragraph)
  Pass 5: Case law narrative
  Pass 6: Practical application + critical assessment
  Pass 7: Assembly — merge passes, unify N. numbering, cross-ref

The assembled result is evaluated and verified like standard generation.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from agents.anthropic_client import run_agent
from agents.config import AgentConfig
from agents.research_agent import (
    build_research_brief,
    format_research_brief_for_prompt,
    save_research_brief,
)

logger = logging.getLogger(__name__)

# Pass definitions per tier
PASSES_TIER_1 = [
    "history",
    "systematic",
    "norminhalt",
    "caselaw_narrative",
    "practice",
    "assembly",
]

PASSES_TIER_2 = [
    "history",
    "norminhalt",
    "caselaw_narrative",
    "assembly",
]


@dataclass
class PassResult:
    """Result of a single generation pass."""

    pass_type: str
    content: str
    cost_usd: float


PASS_PROMPTS: dict[str, str] = {
    "history": (
        "Generate ONLY the Entstehungsgeschichte (legislative history) section "
        "for {article_display}.\n\n"
        "Requirements:\n"
        "- Trace the provision's origins (constitutional genealogy if BV)\n"
        "- Quote the Botschaft with exact BBl page references\n"
        "- Include the Federal Council's stated intent\n"
        "- Note parliamentary modifications (if any)\n"
        "- Use numbered marginal notes: **N. 1**, **N. 2**, etc.\n"
        "- Start numbering at N. 1\n\n"
        "Output ONLY the section content (with ## heading). "
        "Do NOT write a complete commentary — just this section."
    ),
    "systematic": (
        "Generate ONLY the Systematische Einordnung (systematic context) "
        "section for {article_display}.\n\n"
        "Requirements:\n"
        "- Position within the law's structure\n"
        "- Relationship to related provisions (use → and ↔ notation)\n"
        "- International parallels (EMRK, EU law) if applicable\n"
        "- Implementing legislation if applicable\n"
        "- Continue marginal note numbering from N. {start_n}\n\n"
        "Output ONLY the section content (with ## heading)."
    ),
    "norminhalt": (
        "Generate ONLY the Tatbestandsmerkmale / Norminhalt (elements and "
        "content) section for {article_display}.\n\n"
        "Requirements:\n"
        "- Analyze each paragraph/element of the article separately\n"
        "- For each element: definition, scope, limits\n"
        "- Ground analysis in case law with BGE references\n"
        "- Cite doctrinal positions with author attribution\n"
        "- Minimum 10 Randziffern for the whole section\n"
        "- Continue numbering from N. {start_n}\n\n"
        "Output ONLY the section content (with ## heading and ### sub-headings)."
    ),
    "caselaw_narrative": (
        "Generate ONLY a narrative case law analysis for {article_display}.\n\n"
        "Requirements:\n"
        "- NOT a list of decisions — a narrative of doctrinal evolution\n"
        "- Trace how the court's interpretation has developed over time\n"
        "- Identify landmark shifts and their significance\n"
        "- Group by thematic lines of jurisprudence\n"
        "- Include key quotes with Guillemets (« »)\n"
        "- ALL leading cases must appear\n"
        "- Continue numbering from N. {start_n}\n\n"
        "Output ONLY the section content (with ## heading)."
    ),
    "practice": (
        "Generate ONLY the Praxishinweise (practical guidance) and critical "
        "assessment section for {article_display}.\n\n"
        "Requirements:\n"
        "- Domain-specific application scenarios\n"
        "- Procedural aspects (burden of proof, standing, remedies)\n"
        "- Common pitfalls and best practices\n"
        "- Open questions and current debates\n"
        "- Continue numbering from N. {start_n}\n\n"
        "Output ONLY the section content (with ## heading)."
    ),
    "assembly": (
        "You are given the separately generated sections of a doctrinal "
        "commentary for {article_display}. Assemble them into a unified, "
        "publication-ready commentary.\n\n"
        "Tasks:\n"
        "1. Merge all sections under a single # heading\n"
        "2. Renumber ALL Randziffern sequentially: N. 1, N. 2, ...\n"
        "3. Fix internal cross-references between sections\n"
        "4. Remove any redundancies between sections\n"
        "5. Ensure consistent terminology throughout\n"
        "6. Add Streitstände section if not already present\n"
        "7. Verify citation format consistency\n\n"
        "The assembled commentary must read as a single, coherent work.\n\n"
        "=== SECTIONS TO ASSEMBLE ===\n\n{sections}"
    ),
}


def _build_pass_system_prompt(
    config: AgentConfig,
    law: str,
    pass_type: str,
) -> str:
    """Build system prompt for a specific pass."""
    from agents.prompts import build_law_agent_prompt
    # Use the doctrine layer prompt as base for all deep passes
    base = build_law_agent_prompt(config.guidelines_root, law, "doctrine")
    return base


async def run_pass(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    pass_type: str,
    research_brief: dict,
    previous_passes: list[PassResult],
) -> PassResult:
    """Run a single generation pass."""
    suffix_str = article_suffix or ""
    article_display = f"Art. {article_number}{suffix_str} {law}"

    # Calculate starting N. for this pass
    start_n = 1
    for prev in previous_passes:
        # Count N. occurrences in previous content
        import re
        n_matches = re.findall(r"\*\*N\.\s*(\d+)\*\*", prev.content)
        if n_matches:
            start_n = max(start_n, max(int(n) for n in n_matches) + 1)

    # Build the prompt
    template = PASS_PROMPTS[pass_type]
    if pass_type == "assembly":
        sections = "\n\n---\n\n".join(
            f"### {p.pass_type}\n\n{p.content}" for p in previous_passes
        )
        prompt = template.format(
            article_display=article_display,
            sections=sections,
        )
    else:
        prompt = template.format(
            article_display=article_display,
            start_n=start_n,
        )

    # Add research brief context
    brief_text = format_research_brief_for_prompt(research_brief)
    prompt = f"{brief_text}\n\n---\n\n{prompt}"

    system_prompt = _build_pass_system_prompt(config, law, pass_type)

    from agents.tools.content import create_content_tools
    from agents.tools.opencaselaw import create_opencaselaw_tools

    content_tools = create_content_tools(config.content_root)
    opencaselaw_tools = create_opencaselaw_tools(config.mcp_base_url)

    response_text, cost = await run_agent(
        system_prompt=system_prompt,
        prompt=prompt,
        model=config.model_doctrine,
        content_tools=content_tools,
        opencaselaw_tools=opencaselaw_tools,
        allowed_tools=[
            "read_article_meta",
            "read_layer_content",
            "search_decisions",
            "find_leading_cases",
            "get_decision",
            "get_case_brief",
            "get_doctrine",
            "get_commentary",
        ],
        max_turns=config.max_turns_per_agent,
    )

    return PassResult(
        pass_type=pass_type,
        content=response_text,
        cost_usd=cost,
    )


async def deep_generate_article(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    tier: str = "tier_1",
) -> tuple[str, float]:
    """Run multi-pass deep generation for an article.

    Returns (assembled_content, total_cost_usd).
    """
    suffix_str = article_suffix or ""

    logger.info(
        "Deep generation for Art. %d%s %s (tier: %s)",
        article_number, suffix_str, law, tier,
    )

    # Step 1: Build research brief
    research_brief = await build_research_brief(
        config, law, article_number, suffix_str,
    )
    save_research_brief(
        config, law, article_number, suffix_str, research_brief,
    )

    # Step 2: Run passes based on tier
    passes = PASSES_TIER_1 if tier == "tier_1" else PASSES_TIER_2
    results: list[PassResult] = []
    total_cost = 0.0

    for pass_type in passes:
        logger.info(
            "Running pass '%s' for Art. %d%s %s",
            pass_type, article_number, suffix_str, law,
        )
        result = await run_pass(
            config, law, article_number, suffix_str,
            pass_type, research_brief,
            [r for r in results if r.pass_type != "assembly"],
        )
        results.append(result)
        total_cost += result.cost_usd

    # The assembly pass produces the final content
    assembly = next(
        (r for r in results if r.pass_type == "assembly"),
        results[-1],
    )

    # Step 3: Write the assembled doctrine layer
    from agents.tools.content import create_content_tools
    content_tools = create_content_tools(config.content_root)
    await content_tools["write_layer_content"]({
        "law": law,
        "article_number": article_number,
        "article_suffix": suffix_str,
        "layer": "doctrine",
        "content": assembly.content,
    })

    logger.info(
        "Deep generation complete for Art. %d%s %s: "
        "%d passes, $%.2f total",
        article_number, suffix_str, law,
        len(results), total_cost,
    )

    return assembly.content, total_cost
