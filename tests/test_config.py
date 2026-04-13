# tests/test_config.py
from pathlib import Path

from agents.config import AgentConfig


def test_default_config():
    config = AgentConfig()
    assert config.content_root.name == "content"
    assert config.guidelines_root.name == "guidelines"
    assert config.mcp_base_url == "https://mcp.opencaselaw.ch"
    assert config.max_retries == 3


def test_model_for_layer():
    config = AgentConfig()
    # Doctrine uses Opus 4.6 extended thinking after A/B test (2026-04-13)
    assert config.model_for_layer("doctrine") == "opus-thinking"
    assert config.model_for_layer("caselaw") == "sonnet"
    assert config.model_for_layer("summary") == "sonnet"


def test_thresholds():
    config = AgentConfig()
    assert config.threshold_precision == 0.95
    assert config.threshold_academic_rigor == 0.95
    assert config.threshold_concision == 0.90


def test_custom_config():
    config = AgentConfig(max_retries=5, model_doctrine="sonnet")
    assert config.max_retries == 5
    assert config.model_for_layer("doctrine") == "sonnet"


def test_config_has_commentary_refs_root():
    config = AgentConfig()
    assert config.commentary_refs_root == Path("scripts/commentary_refs")
