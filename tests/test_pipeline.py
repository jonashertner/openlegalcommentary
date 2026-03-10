"""Tests for the pipeline CLI."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from agents.bootstrap import BootstrapState
from agents.config import AgentConfig
from agents.pipeline import bootstrap_article, bootstrap_law_resumable, daily_pipeline


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
    for layer in ("summary.md", "doctrine.md", "caselaw.md"):
        (art_dir / layer).write_text("# Placeholder\n")
    return AgentConfig(content_root=content_root)


def _mock_layer_result(success=True):
    from agents.evaluator import EvalResult
    from agents.generation import LayerResult
    return LayerResult(
        law="OR", article_number=41, article_suffix="",
        layer_type="summary", success=success, attempts=1,
        eval_result=EvalResult(
            verdict="publish", scores={"praezision": 0.96},
        ),
        cost_usd=0.05, flagged_for_review=not success,
    )


def test_bootstrap_article(config):
    with patch(
        "agents.pipeline.process_article",
        new_callable=AsyncMock,
        return_value=[_mock_layer_result()],
    ):
        results = asyncio.run(
            bootstrap_article(config, "OR", 41, "")
        )
        assert len(results) >= 1


def test_daily_pipeline_no_new_decisions(config):
    with patch(
        "agents.pipeline.find_new_decisions",
        new_callable=AsyncMock,
        return_value=[],
    ):
        stats = asyncio.run(daily_pipeline(config))
        assert stats["articles_processed"] == 0


def test_daily_pipeline_with_decisions(config):
    decisions = [
        {
            "reference": "BGE 150 III 100",
            "articles": [
                {"law": "OR", "article": 41, "suffix": ""},
            ],
        }
    ]
    with (
        patch(
            "agents.pipeline.find_new_decisions",
            new_callable=AsyncMock,
            return_value=decisions,
        ),
        patch(
            "agents.pipeline.process_article",
            new_callable=AsyncMock,
            return_value=[_mock_layer_result()],
        ),
    ):
        stats = asyncio.run(daily_pipeline(config))
        assert stats["articles_processed"] == 1


def test_bootstrap_resumes_from_state(config, tmp_path):
    """Bootstrap skips already-completed articles."""
    state_path = tmp_path / "state.json"
    state = BootstrapState(state_path)
    state.add_article("OR", 41, "")
    state.mark_completed("OR", 41, "", cost=0.10)
    state.add_article("OR", 42, "")
    state.save()

    # Scaffold art-042
    art_dir = config.content_root / "or" / "art-042"
    art_dir.mkdir(parents=True, exist_ok=True)
    (art_dir / "meta.yaml").write_text(
        "law: OR\narticle: 42\ntitle: Test\n"
        "sr_number: '220'\nabsatz_count: 1\n"
        "fedlex_url: https://example.com\nlayers: {}\n"
    )
    for layer in ("summary.md", "doctrine.md", "caselaw.md"):
        (art_dir / layer).write_text("# Placeholder\n")

    with patch(
        "agents.pipeline.process_article",
        new_callable=AsyncMock,
        return_value=[_mock_layer_result()],
    ) as mock_process:
        asyncio.run(
            bootstrap_law_resumable(
                config, "OR", state, max_concurrent=2,
            )
        )
        # Should only process art-042 (art-041 already completed)
        assert mock_process.call_count == 1
        call_args = mock_process.call_args
        assert call_args.args[2] == 42  # article_number


def test_bootstrap_stops_on_budget(config, tmp_path):
    """Bootstrap stops when cost budget is exceeded."""
    state_path = tmp_path / "state.json"
    state = BootstrapState(state_path)
    state.add_article("OR", 41, "")
    state.add_article("OR", 42, "")
    state.save()

    # Create art-042 directory too
    art_dir = config.content_root / "or" / "art-042"
    art_dir.mkdir(parents=True, exist_ok=True)
    (art_dir / "meta.yaml").write_text(
        "law: OR\narticle: 42\ntitle: Test\n"
        "sr_number: '220'\nabsatz_count: 1\n"
        "fedlex_url: https://example.com\nlayers: {}\n"
    )
    for layer in ("summary.md", "doctrine.md", "caselaw.md"):
        (art_dir / layer).write_text("# Placeholder\n")

    expensive_result = _mock_layer_result()
    expensive_result.cost_usd = 100.0

    with patch(
        "agents.pipeline.process_article",
        new_callable=AsyncMock,
        return_value=[expensive_result],
    ):
        results = asyncio.run(
            bootstrap_law_resumable(
                config, "OR", state,
                max_concurrent=1, max_budget=50.0,
            )
        )
        # Should stop after first article exceeds budget
        assert len(results) == 1
