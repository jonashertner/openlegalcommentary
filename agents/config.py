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

    # Model selection per role (spec: Opus for doctrine+eval, Sonnet for caselaw+translation)
    model_doctrine: str = "opus"
    model_caselaw: str = "sonnet"
    model_summary: str = "sonnet"
    model_evaluator: str = "opus"
    model_translator: str = "sonnet"

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
