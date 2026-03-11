"""Tests for the law agent."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from agents.config import AgentConfig
from agents.law_agent import generate_layer


@pytest.fixture
def config(tmp_path):
    content_root = tmp_path / "content"
    art_dir = content_root / "or" / "art-041"
    art_dir.mkdir(parents=True)
    (art_dir / "meta.yaml").write_text(
        "law: OR\narticle: 41\ntitle: Haftung\n"
        "sr_number: '220'\nabsatz_count: 2\n"
        "fedlex_url: https://example.com\nlayers: {}\n"
    )
    (art_dir / "summary.md").write_text("# Übersicht\n\nPlaceholder.")
    (art_dir / "doctrine.md").write_text("# Doktrin\n\nPlaceholder.")
    (art_dir / "caselaw.md").write_text("# Rechtsprechung\n\nPlaceholder.")
    return AgentConfig(content_root=content_root)


def test_generate_layer_calls_query(config):
    mock_run = AsyncMock(return_value=("Generated content.", 0.05))
    with patch("agents.law_agent.run_agent", mock_run):
        asyncio.run(generate_layer(config, "OR", 41, "", "summary"))
        mock_run.assert_called_once()


def test_generate_layer_uses_correct_model(config):
    mock_run = AsyncMock(return_value=("Generated content.", 0.05))
    with patch("agents.law_agent.run_agent", mock_run):
        asyncio.run(generate_layer(config, "OR", 41, "", "doctrine"))
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["model"] == "opus"


def test_generate_layer_with_feedback(config):
    mock_run = AsyncMock(return_value=("Generated content.", 0.05))
    with patch("agents.law_agent.run_agent", mock_run):
        asyncio.run(
            generate_layer(config, "OR", 41, "", "summary", feedback="Missing example")
        )
        call_kwargs = mock_run.call_args.kwargs
        assert "Missing example" in call_kwargs["prompt"]


def test_generate_layer_returns_cost(config):
    mock_run = AsyncMock(return_value=("Generated content.", 0.05))
    with patch("agents.law_agent.run_agent", mock_run):
        cost = asyncio.run(generate_layer(config, "OR", 41, "", "summary"))
        assert cost == pytest.approx(0.05)
