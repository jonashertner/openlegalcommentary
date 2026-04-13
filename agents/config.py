"""Agent pipeline configuration."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AgentConfig:
    """Configuration for the agent pipeline."""

    content_root: Path = field(default_factory=lambda: Path("content"))
    guidelines_root: Path = field(default_factory=lambda: Path("guidelines"))
    mcp_base_url: str = "https://mcp.opencaselaw.ch"

    # Model selection per role.
    # Doctrine was originally Opus but the Phase 0 Sonnet experiment
    # (docs/superpowers/specs/2026-04-10-phase-0-sonnet-test-results.md)
    # showed Sonnet 4.6 producing measurably better doctrine than the
    # Opus-4 baseline at roughly 10-13x lower cost, scoring 0.92 from
    # the Opus 4.6 evaluator. Evaluator stays on Opus as an independent
    # judge. The write-skip safeguard in agents/generation.py protects
    # against the silent failure mode observed in the experiment.
    model_doctrine: str = "sonnet"
    model_caselaw: str = "sonnet"
    model_summary: str = "sonnet"
    model_evaluator: str = "opus"
    model_translator: str = "sonnet"

    # Cross-model evaluation
    model_evaluator_2: str = "chatgpt"
    model_evaluator_3: str = "grok"
    evaluator_mode: str = "all_must_pass"  # "all_must_pass", "majority", "claude_only"

    commentary_refs_root: Path = field(
        default_factory=lambda: Path("scripts/commentary_refs"),
    )

    # Quality thresholds (from guidelines/evaluate.md)
    threshold_precision: float = 0.95
    threshold_concision: float = 0.90
    threshold_accessibility: float = 0.90
    threshold_relevance: float = 0.90
    threshold_academic_rigor: float = 0.95

    # Agent execution limits
    max_retries: int = 3
    max_turns_per_agent: int = 25
    max_budget_per_layer: float = 0.50

    def model_for_layer(self, layer_type: str) -> str:
        """Return the model name for a given layer type."""
        models = {
            "summary": self.model_summary,
            "doctrine": self.model_doctrine,
            "caselaw": self.model_caselaw,
        }
        if layer_type not in models:
            raise ValueError(f"Unknown layer type: {layer_type}")
        return models[layer_type]
