"""Evaluator agent — quality gate for generated commentary.

Evaluates layers against guidelines/evaluate.md criteria:
- 5 non-negotiable binary checks (any failure = reject)
- 5 scored dimensions with thresholds (all must meet minimum)

Supports cross-model evaluation: Claude Opus (primary, tool-based),
plus optional ChatGPT and Grok evaluators via OpenAI-compatible API.
All evaluators must pass for the merged verdict to be "publish".
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass, field

from agents.anthropic_client import run_agent
from agents.config import AgentConfig
from agents.openai_client import run_evaluation as run_openai_evaluation
from agents.prompts import build_evaluator_prompt, build_evaluator_prompt_inline
from agents.references import (
    format_article_text,
    format_commentary_refs,
    format_preparatory_materials,
)
from agents.tools.content import create_content_tools

logger = logging.getLogger(__name__)

EVALUATOR_REGISTRY = {
    "chatgpt": {
        "model": "gpt-5.4",
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
    },
    "grok": {
        "model": "grok-4.20-0309-reasoning",
        "base_url": "https://api.x.ai/v1",
        "api_key_env": "XAI_API_KEY",
    },
}


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


def merge_eval_results(
    results: dict[str, EvalResult],
    advisory: set[str] | None = None,
) -> EvalResult:
    """Merge multiple evaluator results into a single verdict.

    Evaluators in ``advisory`` contribute feedback and suggestions but
    their verdict does not block publication.  All non-advisory evaluators
    must pass for the merged verdict to be "publish".
    Scores take the minimum per dimension across non-advisory evaluators.
    """
    if not results:
        raise ValueError("No evaluation results to merge")

    advisory = advisory or set()
    binding = {k: v for k, v in results.items() if k not in advisory}
    all_passed = all(r.passed for r in binding.values()) if binding else True

    # Merge scores: minimum per dimension (binding only)
    all_dims: set[str] = set()
    for r in binding.values():
        all_dims.update(r.scores.keys())
    merged_scores = {}
    for dim in all_dims:
        values = [r.scores[dim] for r in binding.values() if dim in r.scores]
        merged_scores[dim] = min(values) if values else 0.0

    # Merge non-negotiables: AND across binding evaluators
    all_nn_keys: set[str] = set()
    for r in binding.values():
        all_nn_keys.update(r.non_negotiables.keys())
    merged_nn = {}
    for key in all_nn_keys:
        merged_nn[key] = all(
            r.non_negotiables.get(key, True) for r in binding.values()
        )

    # Merge feedback with source labels (all evaluators, incl. advisory)
    merged_blocking: list[str] = []
    merged_suggestions: list[str] = []
    for name, r in results.items():
        label = f"[{name}]" if name not in advisory else f"[{name} advisory]"
        for issue in r.feedback.get("blocking_issues", []):
            merged_blocking.append(f"{label} {issue}")
        for sug in r.feedback.get("improvement_suggestions", []):
            merged_suggestions.append(f"{label} {sug}")

    return EvalResult(
        verdict="publish" if all_passed else "reject",
        non_negotiables=merged_nn,
        scores=merged_scores,
        feedback={
            "blocking_issues": merged_blocking,
            "improvement_suggestions": merged_suggestions,
        },
    )


def _build_inline_eval_prompt(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_type: str,
) -> str:
    """Build a content-inlined evaluation prompt for external evaluators."""
    suffix_str = article_suffix or ""
    dir_name = f"art-{article_number:03d}{suffix_str}"
    layer_path = config.content_root / law.lower() / dir_name / f"{layer_type}.md"
    layer_content = layer_path.read_text() if layer_path.exists() else ""

    article_text = format_article_text(law, article_number, suffix_str)

    parts = [
        f"Evaluate the {layer_type} layer for "
        f"Art. {article_number}{suffix_str} {law}.",
    ]
    if article_text:
        parts.append(f"\n## Gesetzestext\n\n{article_text}")
    parts.append(f"\n## Generated Content\n\n{layer_content}")

    if layer_type in ("doctrine", "summary"):
        refs = format_commentary_refs(
            config.commentary_refs_root, law, article_number, suffix_str,
        )
        if refs:
            parts.append(f"\n\n{refs}")
        prep = format_preparatory_materials(law, article_number, suffix_str)
        if prep:
            parts.append(f"\n\n{prep}")

    parts.append("\nReturn your JSON verdict.")
    return "\n".join(parts)


async def _evaluate_anthropic(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_type: str,
) -> EvalResult:
    """Run the Claude Opus evaluator (tool-based)."""
    system_prompt = build_evaluator_prompt(config.guidelines_root)

    content_tools = create_content_tools(config.content_root)

    suffix_str = article_suffix or ""

    # Inject article text directly for verification
    article_text = format_article_text(law, article_number, suffix_str)
    article_text_block = ""
    if article_text:
        article_text_block = (
            f"\n\nHere is the official Gesetzestext of "
            f"Art. {article_number}{suffix_str} {law}:\n\n{article_text}\n"
        )

    # Inject commentary references for cross-checking
    commentary_refs_block = ""
    if layer_type in ("doctrine", "summary"):
        commentary_refs_block = format_commentary_refs(
            config.commentary_refs_root, law, article_number, suffix_str,
        )

    # Inject preparatory materials for cross-checking
    prep_materials_block = ""
    if layer_type in ("doctrine", "summary"):
        prep_materials_block = format_preparatory_materials(
            law, article_number, suffix_str,
        )

    prompt = (
        f"Evaluate the {layer_type} layer for "
        f"Art. {article_number}{suffix_str} {law}. "
        f"Read the content and evaluate its quality "
        f"based on the rubric criteria. "
        f"Do NOT reject content solely because you cannot "
        f"verify external citations — evaluate what is written."
        f"{article_text_block}"
        f"Return your JSON verdict."
    )
    if commentary_refs_block:
        prompt += f"\n\n{commentary_refs_block}"
    if prep_materials_block:
        prompt += f"\n\n{prep_materials_block}"

    response_text, _ = await run_agent(
        system_prompt=system_prompt,
        prompt=prompt,
        model=config.model_evaluator,
        content_tools=content_tools,
        opencaselaw_tools=None,
        allowed_tools=[
            "read_article_meta",
            "read_layer_content",
        ],
        max_turns=config.max_turns_per_agent,
    )

    return parse_eval_response(response_text)


async def _evaluate_external(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_type: str,
    model: str,
    base_url: str,
    api_key_env: str,
) -> EvalResult:
    """Run an external evaluator (ChatGPT/Grok) via OpenAI-compatible API."""
    system_prompt = build_evaluator_prompt_inline(config.guidelines_root)
    prompt = _build_inline_eval_prompt(
        config, law, article_number, article_suffix, layer_type,
    )
    response_text, _ = await run_openai_evaluation(
        system_prompt=system_prompt,
        prompt=prompt,
        model=model,
        base_url=base_url,
        api_key_env=api_key_env,
    )
    return parse_eval_response(response_text)


async def evaluate_layer(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_type: str,
) -> EvalResult:
    """Run evaluation across all configured evaluators.

    Returns a single merged EvalResult. All evaluators must pass
    for the merged verdict to be "publish".
    """
    tasks: dict[str, asyncio.Task] = {}

    # Always run Claude Opus
    tasks["claude"] = asyncio.ensure_future(
        _evaluate_anthropic(config, law, article_number, article_suffix, layer_type)
    )

    # External evaluators — skip if API key not set
    for eval_key, eval_cfg in EVALUATOR_REGISTRY.items():
        if not os.environ.get(eval_cfg["api_key_env"]):
            logger.info(
                "Skipping %s evaluator — %s not set",
                eval_key, eval_cfg["api_key_env"],
            )
            continue
        tasks[eval_key] = asyncio.ensure_future(
            _evaluate_external(
                config, law, article_number, article_suffix, layer_type,
                model=eval_cfg["model"],
                base_url=eval_cfg["base_url"],
                api_key_env=eval_cfg["api_key_env"],
            )
        )

    # Await all
    results: dict[str, EvalResult] = {}
    for name, task in tasks.items():
        try:
            results[name] = await task
            logger.info(
                "Evaluator %s: verdict=%s scores=%s",
                name, results[name].verdict, results[name].scores,
            )
        except Exception as e:
            logger.error(
                "Evaluator %s failed: %s — treating as reject", name, e,
            )
            results[name] = EvalResult(
                verdict="reject",
                feedback={"blocking_issues": [f"Evaluator {name} error: {e}"]},
            )

    # ChatGPT is advisory — its feedback is included but its verdict
    # does not block publication (A/B test showed it lacks Swiss law
    # domain knowledge for reliable precision/rigor scoring).
    return merge_eval_results(results, advisory={"chatgpt"})
