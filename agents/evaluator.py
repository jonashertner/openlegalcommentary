"""Evaluator agent — quality gate for generated commentary.

Evaluates layers against guidelines/evaluate.md criteria:
- 5 non-negotiable binary checks (any failure = reject)
- 5 scored dimensions with thresholds (all must meet minimum)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from agents.anthropic_client import run_agent
from agents.config import AgentConfig
from agents.prompts import build_evaluator_prompt
from agents.tools.content import create_content_tools
from agents.tools.opencaselaw import create_opencaselaw_tools


@dataclass
class EvalResult:
    """Result of a quality evaluation."""

    verdict: str  # "publish" or "reject"
    non_negotiables: dict[str, bool] = field(default_factory=dict)
    scores: dict[str, float] = field(default_factory=dict)
    feedback: dict[str, list[str]] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.verdict == "publish"

    def feedback_text(self) -> str:
        """Format feedback as readable text for retry prompts."""
        parts = []
        issues = self.feedback.get("blocking_issues", [])
        if issues:
            parts.append(
                "Blocking issues:\n"
                + "\n".join(f"- {i}" for i in issues)
            )
        suggestions = self.feedback.get("improvement_suggestions", [])
        if suggestions:
            parts.append(
                "Suggestions:\n"
                + "\n".join(f"- {s}" for s in suggestions)
            )
        failed_nn = [
            k for k, v in self.non_negotiables.items() if not v
        ]
        if failed_nn:
            parts.append(
                "Failed non-negotiables: " + ", ".join(failed_nn)
            )
        return "\n\n".join(parts) if parts else "No specific feedback."


def parse_eval_response(response_text: str) -> EvalResult:
    """Parse the evaluator's JSON response from text output."""
    json_match = re.search(r"```json\s*([\s\S]*?)```", response_text)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        json_match = re.search(r"\{[\s\S]*\}", response_text)
        if json_match:
            json_str = json_match.group(0)
        else:
            raise ValueError(
                "No JSON found in evaluator response: "
                f"{response_text[:200]}"
            )

    data = json.loads(json_str)
    return EvalResult(
        verdict=data["verdict"],
        non_negotiables=data.get("non_negotiables", {}),
        scores=data.get("scores", {}),
        feedback=data.get("feedback", {}),
    )


async def evaluate_layer(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_type: str,
) -> EvalResult:
    """Run the evaluator agent on a generated layer.

    Returns an EvalResult with verdict, scores, and feedback.
    """
    system_prompt = build_evaluator_prompt(config.guidelines_root)

    content_tools = create_content_tools(config.content_root)
    opencaselaw_tools = create_opencaselaw_tools(config.mcp_base_url)

    suffix_str = article_suffix or ""
    prompt = (
        f"Evaluate the {layer_type} layer for "
        f"Art. {article_number}{suffix_str} {law}. "
        f"Read the content, verify it against the article text "
        f"and case law, then return your JSON verdict."
    )

    response_text, _ = await run_agent(
        system_prompt=system_prompt,
        prompt=prompt,
        model=config.model_evaluator,
        content_tools=content_tools,
        opencaselaw_tools=opencaselaw_tools,
        allowed_tools=[
            "read_article_meta",
            "read_layer_content",
            "get_article_text",
            "find_leading_cases",
            "search_decisions",
        ],
        max_turns=config.max_turns_per_agent,
    )

    return parse_eval_response(response_text)
