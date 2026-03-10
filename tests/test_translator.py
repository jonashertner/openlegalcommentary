"""Tests for the translator agent."""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from agents.config import AgentConfig
from agents.translator import translate_layer


@pytest.fixture
def config(tmp_path):
    content_root = tmp_path / "content"
    art_dir = content_root / "or" / "art-041"
    art_dir.mkdir(parents=True)
    (art_dir / "summary.md").write_text("# Uebersicht\n\nDeutscher Text.")
    return AgentConfig(content_root=content_root)


def _mock_query():
    from claude_agent_sdk import ResultMessage
    msg = MagicMock(spec=ResultMessage)
    msg.total_cost_usd = 0.02

    async def gen(*args, **kwargs):
        yield msg
    return gen


def test_translate_layer_calls_query(config):
    with patch("agents.translator.query") as mock_query:
        mock_query.side_effect = _mock_query()

        asyncio.run(translate_layer(config, "OR", 41, "", "summary", "fr"))
        mock_query.assert_called_once()


def test_translate_layer_uses_sonnet(config):
    with patch("agents.translator.query") as mock_query:
        mock_query.side_effect = _mock_query()

        asyncio.run(translate_layer(config, "OR", 41, "", "summary", "fr"))
        options = mock_query.call_args.kwargs.get("options")
        assert options.model == "sonnet"


def test_translate_layer_prompt_includes_target(config):
    with patch("agents.translator.query") as mock_query:
        mock_query.side_effect = _mock_query()

        asyncio.run(translate_layer(config, "OR", 41, "", "summary", "it"))
        prompt = mock_query.call_args.kwargs.get("prompt")
        if prompt is None:
            prompt = mock_query.call_args.args[0]
        assert "summary.it" in prompt or "Italian" in prompt or "it" in prompt


def test_translate_invalid_language(config):
    with pytest.raises(ValueError):
        asyncio.run(translate_layer(config, "OR", 41, "", "summary", "es"))
