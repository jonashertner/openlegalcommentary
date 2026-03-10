"""Tests for the pipeline CLI."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from agents.config import AgentConfig
from agents.pipeline import bootstrap_article, daily_pipeline


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
