"""Tests for the generation loop (generate → evaluate → retry → translate)."""
from __future__ import annotations

import asyncio
from pathlib import Path
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


def _make_writing_gen_mock(layer_path: Path):
    """Build a mock ``generate_layer`` that writes unique content per call.

    The write-skip safeguard in ``generate_and_evaluate`` hashes the target
    layer file before and after each ``generate_layer`` invocation; if the
    file is unchanged, the attempt is treated as a silent failure and
    retried. Tests that mock ``generate_layer`` must therefore touch the
    target file, or else all attempts will trip the safeguard.
    """
    counter = {"n": 0}

    async def _impl(*_args, **_kwargs):
        counter["n"] += 1
        layer_path.write_text(f"# Generated (attempt {counter['n']})\n")
        return 0.05

    return _impl


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
    layer_path = config.content_root / "or" / "art-041" / "summary.md"
    with (
        patch(
            "agents.generation.generate_layer",
            side_effect=_make_writing_gen_mock(layer_path),
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
    layer_path = config.content_root / "or" / "art-041" / "summary.md"
    fail = _fail_result()
    with (
        patch(
            "agents.generation.generate_layer",
            side_effect=_make_writing_gen_mock(layer_path),
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
    layer_path = config.content_root / "or" / "art-041" / "summary.md"
    fail = _fail_result()
    with (
        patch(
            "agents.generation.generate_layer",
            side_effect=_make_writing_gen_mock(layer_path),
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


def test_generate_and_evaluate_retries_on_write_skip(config):
    """Safeguard: if the law agent finishes without writing the target
    layer file, treat the attempt as failed and retry with explicit
    feedback rather than silently passing the pre-existing content
    through the evaluator.
    """
    layer_path = config.content_root / "or" / "art-041" / "summary.md"
    call_count = {"n": 0}

    async def _flaky_gen(*_args, **_kwargs):
        call_count["n"] += 1
        if call_count["n"] >= 2:
            # Second attempt onwards: write real content
            layer_path.write_text(
                f"# Written on attempt {call_count['n']}\n"
            )
        # First attempt: deliberately do not touch the file, simulating
        # Sonnet's observed write-skip failure mode
        return 0.05

    with (
        patch("agents.generation.generate_layer", side_effect=_flaky_gen),
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
        assert result.attempts == 2  # first attempt skipped, retried once
        assert call_count["n"] == 2


def test_generate_and_evaluate_fails_if_every_attempt_write_skips(config):
    """If the law agent never writes across all retries, the article is
    flagged for human review rather than silently passing.
    """
    async def _always_skip(*_args, **_kwargs):
        return 0.05

    with (
        patch("agents.generation.generate_layer", side_effect=_always_skip),
        patch(
            "agents.generation.evaluate_layer",
            new_callable=AsyncMock,
            return_value=_pass_result(),  # would pass if the evaluator were reached
        ),
    ):
        result = asyncio.run(
            generate_and_evaluate(config, "OR", 41, "", "summary")
        )
        assert result.success is False
        assert result.attempts == 3
        assert result.flagged_for_review is True


def test_generate_and_evaluate_rolls_back_on_total_failure(config):
    """Safeguard: if every attempt writes new content but every evaluator
    pass rejects it, the pipeline must restore the pre-regeneration snapshot
    rather than leaving the last rejected attempt's content on disk.

    Empirically observed on BV Art. 118 during Phase 1b where this exact
    pattern turned an 8-flagged article into a 12-flagged one.
    """
    layer_path = config.content_root / "or" / "art-041" / "summary.md"
    original_content = layer_path.read_text()
    assert "Placeholder" in original_content

    fail = _fail_result()
    with (
        patch(
            "agents.generation.generate_layer",
            side_effect=_make_writing_gen_mock(layer_path),
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
    assert result.flagged_for_review is True
    # Critical: the file on disk after total failure must equal the snapshot
    # captured before the first attempt, not the last rejected write
    assert layer_path.read_text() == original_content


def test_generate_and_evaluate_rolls_back_missing_file(config):
    """If the target layer file did not exist before regeneration and every
    attempt fails, the rollback should remove any partial file written by
    the failed attempts rather than leaving a stub.
    """
    layer_path = config.content_root / "or" / "art-041" / "summary.md"
    layer_path.unlink()
    assert not layer_path.exists()

    fail = _fail_result()
    with (
        patch(
            "agents.generation.generate_layer",
            side_effect=_make_writing_gen_mock(layer_path),
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
    assert result.flagged_for_review is True
    # Critical: the file must not exist after rollback — it didn't exist
    # before regeneration either
    assert not layer_path.exists()


def test_generate_and_evaluate_success_does_not_trigger_rollback(config):
    """Rollback logic must not touch successful attempts: after a PASS the
    new content must stay on disk.
    """
    layer_path = config.content_root / "or" / "art-041" / "summary.md"
    with (
        patch(
            "agents.generation.generate_layer",
            side_effect=_make_writing_gen_mock(layer_path),
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
    # The successful attempt's content (written by the mock) must remain
    assert "Generated (attempt 1)" in layer_path.read_text()


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
