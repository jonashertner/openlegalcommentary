"""Tests for the OpenAI/xAI evaluation client."""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.openai_client import run_evaluation


def _mock_chat_response(content: str):
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    usage = MagicMock()
    usage.prompt_tokens = 1000
    usage.completion_tokens = 500
    resp = MagicMock()
    resp.choices = [choice]
    resp.usage = usage
    return resp


def test_run_evaluation_returns_text_and_cost(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    verdict = json.dumps({"verdict": "publish", "scores": {"praezision": 0.96}})
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=_mock_chat_response(verdict),
    )
    with patch("agents.openai_client.AsyncOpenAI", return_value=mock_client):
        text, cost = asyncio.run(run_evaluation(
            system_prompt="You are an evaluator.",
            prompt="Evaluate this.",
            model="gpt-5.4-pro",
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
        ))
    assert "publish" in text
    assert cost > 0


def test_run_evaluation_uses_correct_base_url(monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    verdict = json.dumps({"verdict": "publish"})
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=_mock_chat_response(verdict),
    )
    with patch("agents.openai_client.AsyncOpenAI", return_value=mock_client) as mock_cls:
        asyncio.run(run_evaluation(
            system_prompt="System",
            prompt="Prompt",
            model="grok-4.20-0309-reasoning",
            base_url="https://api.x.ai/v1",
            api_key_env="XAI_API_KEY",
        ))
    mock_cls.assert_called_once()
    call_kwargs = mock_cls.call_args[1]
    assert call_kwargs["base_url"] == "https://api.x.ai/v1"


def test_run_evaluation_missing_key_raises(monkeypatch):
    monkeypatch.delenv("NONEXISTENT_KEY", raising=False)
    with pytest.raises(ValueError, match="not set"):
        asyncio.run(run_evaluation(
            system_prompt="System",
            prompt="Prompt",
            model="test-model",
            base_url="https://api.openai.com/v1",
            api_key_env="NONEXISTENT_KEY",
        ))
