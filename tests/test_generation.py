"""Tests for the generation loop (generate → evaluate → retry → translate)."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from agents.config import AgentConfig
from agents.evaluator import EvalResult
from agents.generation import LayerResult, generate_and_evaluate, process_article


@pytest.fixture
def config(tmp_path):
    content_root = tmp_path / "content"
    art_dir = content_root / "or" / "art-041"
    art_dir.mkdir(parents=True)
    (art_dir / "meta.yaml").write_text(
        "law: OR\narticle: 41\ntitle: Test\n"
        "sr_number: '220'\nabsatz_count: 1\n"
        "fedlex_url: https://example.com\nlayers: {}\n"
    )
    for layer in ("summary.md", "doctrine.md", "caselaw.md"):
        (art_dir / layer).write_text("# Placeholder\n")
    return AgentConfig(content_root=content_root)


def _pass_result():
    return EvalResult(
        verdict="publish",
        non_negotiables={"keine_unbelegten_rechtsaussagen": True},
        scores={"praezision": 0.96},
        feedback={"blocking_issues": [], "improvement_suggestions": []},
    )


def _fail_result():
    return EvalResult(
        verdict="reject",
        non_negotiables={"keine_unbelegten_rechtsaussagen": False},
        scores={"praezision": 0.80},
        feedback={"blocking_issues": ["Unbelegte Aussage in N. 3"]},
    )


def test_generate_and_evaluate_passes_first_try(config):
    with (
        patch(
            "agents.generation.generate_layer",
            new_callable=AsyncMock,
            return_value=0.05,
        ),
        patch(
            "agents.generation.evaluate_layer",
            new_callable=AsyncMock,
            return_value=_pass_result(),
        ),
    ):
        result = asyncio.run(
            generate_and_evaluate(config, "OR", 41, "", "summary")
        )
        assert result.success is True
        assert result.attempts == 1


def test_generate_and_evaluate_retries_on_failure(config):
    fail = _fail_result()
    with (
        patch(
            "agents.generation.generate_layer",
            new_callable=AsyncMock,
            return_value=0.05,
        ),
        patch(
            "agents.generation.evaluate_layer",
            new_callable=AsyncMock,
            side_effect=[fail, fail, _pass_result()],
        ),
    ):
        result = asyncio.run(
            generate_and_evaluate(config, "OR", 41, "", "summary")
        )
        assert result.success is True
        assert result.attempts == 3


def test_generate_and_evaluate_flags_after_max_retries(config):
    fail = _fail_result()
    with (
        patch(
            "agents.generation.generate_layer",
            new_callable=AsyncMock,
            return_value=0.05,
        ),
        patch(
            "agents.generation.evaluate_layer",
            new_callable=AsyncMock,
            return_value=fail,
        ),
    ):
        result = asyncio.run(
            generate_and_evaluate(config, "OR", 41, "", "summary")
        )
        assert result.success is False
        assert result.attempts == 3
        assert result.flagged_for_review is True


def test_layer_result_dataclass():
    result = LayerResult(
        law="OR", article_number=41, article_suffix="",
        layer_type="summary", success=True, attempts=1,
        eval_result=_pass_result(), cost_usd=0.10,
        flagged_for_review=False,
    )
    assert result.success is True
    assert result.cost_usd == pytest.approx(0.10)


def test_process_article_generates_all_layers(config):
    with (
        patch(
            "agents.generation.generate_and_evaluate",
            new_callable=AsyncMock,
            return_value=LayerResult(
                law="OR", article_number=41, article_suffix="",
                layer_type="summary", success=True, attempts=1,
                eval_result=_pass_result(), cost_usd=0.05,
                flagged_for_review=False,
            ),
        ),
        patch(
            "agents.generation.translate_layer",
            new_callable=AsyncMock,
            return_value=0.02,
        ),
    ):
        results = asyncio.run(
            process_article(config, "OR", 41, "", ["summary", "doctrine", "caselaw"])
        )
        assert len(results) == 3
