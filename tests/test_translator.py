"""Tests for the translator agent."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from agents.config import AgentConfig
from agents.translator import translate_layer


@pytest.fixture
def config(tmp_path):
    content_root = tmp_path / "content"
    art_dir = content_root / "or" / "art-041"
    art_dir.mkdir(parents=True)
    (art_dir / "summary.md").write_text("# Übersicht\n\nDeutscher Text.")
    return AgentConfig(content_root=content_root)


def test_translate_layer_calls_query(config):
    mock_run = AsyncMock(return_value=("Translated.", 0.02))
    with patch("agents.translator.run_agent", mock_run):
        asyncio.run(translate_layer(config, "OR", 41, "", "summary", "fr"))
        mock_run.assert_called_once()


def test_translate_layer_uses_sonnet(config):
    mock_run = AsyncMock(return_value=("Translated.", 0.02))
    with patch("agents.translator.run_agent", mock_run):
        asyncio.run(translate_layer(config, "OR", 41, "", "summary", "fr"))
        call_kwargs = mock_run.call_args.kwargs
        assert call_kwargs["model"] == "sonnet"


def test_translate_layer_prompt_includes_target(config):
    mock_run = AsyncMock(return_value=("Translated.", 0.02))
    with patch("agents.translator.run_agent", mock_run):
        asyncio.run(translate_layer(config, "OR", 41, "", "summary", "it"))
        call_kwargs = mock_run.call_args.kwargs
        assert "Italian" in call_kwargs["prompt"]


def test_translate_invalid_language(config):
    with pytest.raises(ValueError, match="Unknown target language"):
        asyncio.run(translate_layer(config, "OR", 41, "", "summary", "en"))
