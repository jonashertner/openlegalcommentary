"""Tests for the law agent."""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

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
    (art_dir / "summary.md").write_text("# Uebersicht\n\nPlaceholder.")
    (art_dir / "doctrine.md").write_text("# Doktrin\n\nPlaceholder.")
    (art_dir / "caselaw.md").write_text("# Rechtsprechung\n\nPlaceholder.")
    return AgentConfig(content_root=content_root)


def _mock_query_messages():
    """Return a mock async generator that yields a ResultMessage."""
    from claude_agent_sdk import ResultMessage
    msg = MagicMock(spec=ResultMessage)
    msg.total_cost_usd = 0.05

    async def gen(*args, **kwargs):
        yield msg

    return gen


def test_generate_layer_calls_query(config):
    with patch("agents.law_agent.query") as mock_query:
        mock_query.side_effect = _mock_query_messages()

        asyncio.run(
            generate_layer(config, "OR", 41, "", "summary")
        )
        mock_query.assert_called_once()
        call_kwargs = mock_query.call_args
        assert "prompt" in call_kwargs.kwargs or len(call_kwargs.args) > 0


def test_generate_layer_uses_correct_model(config):
    with patch("agents.law_agent.query") as mock_query:
        mock_query.side_effect = _mock_query_messages()

        asyncio.run(generate_layer(config, "OR", 41, "", "doctrine"))
        options = mock_query.call_args.kwargs.get("options")
        assert options is not None
        assert options.model == "opus"


def test_generate_layer_with_feedback(config):
    with patch("agents.law_agent.query") as mock_query:
        mock_query.side_effect = _mock_query_messages()

        asyncio.run(
            generate_layer(config, "OR", 41, "", "summary", feedback="Missing example")
        )
        call_args = mock_query.call_args
        if "prompt" in call_args.kwargs:
            prompt = call_args.kwargs["prompt"]
        else:
            prompt = call_args.args[0]
        assert "Missing example" in prompt


def test_generate_layer_returns_cost(config):
    with patch("agents.law_agent.query") as mock_query:
        mock_query.side_effect = _mock_query_messages()

        cost = asyncio.run(generate_layer(config, "OR", 41, "", "summary"))
        assert cost == pytest.approx(0.05)
