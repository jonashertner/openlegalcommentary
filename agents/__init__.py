"""Agent pipeline for openlegalcommentary.

Public API:
  - AgentConfig: Pipeline configuration
  - generate_layer: Run law agent for one article layer
  - evaluate_layer: Run evaluator agent
  - translate_layer: Run translator agent
  - process_article: Full generate → evaluate → retry → translate loop
  - daily_pipeline: Daily update pipeline
"""
from agents.config import AgentConfig

__all__ = ["AgentConfig"]
