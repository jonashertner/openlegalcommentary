"""Tests for the evaluator agent."""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from agents.config import AgentConfig
from agents.evaluator import (
    EvalResult,
    evaluate_layer,
    merge_eval_results,
    parse_eval_response,
)


def test_eval_result_passed():
    result = EvalResult(
        verdict="publish",
        non_negotiables={
            "keine_unbelegten_rechtsaussagen": True,
            "keine_faktischen_fehler": True,
            "keine_fehlenden_leitentscheide": True,
            "korrekte_legalbegriffe": True,
            "strukturelle_vollstaendigkeit": True,
        },
        scores={
            "praezision": 0.96, "konzision": 0.92,
            "zugaenglichkeit": 0.91, "relevanz": 0.93,
            "akademische_strenge": 0.95,
        },
        feedback={"blocking_issues": [], "improvement_suggestions": []},
    )
    assert result.passed is True


def test_eval_result_rejected():
    result = EvalResult(
        verdict="reject",
        non_negotiables={"keine_unbelegten_rechtsaussagen": False},
        scores={"praezision": 0.80},
        feedback={"blocking_issues": ["Unbelegte Rechtsaussage in N. 3"]},
    )
    assert result.passed is False


def test_eval_result_feedback_text():
    result = EvalResult(
        verdict="reject",
        non_negotiables={},
        scores={},
        feedback={
            "blocking_issues": ["Issue A", "Issue B"],
            "improvement_suggestions": ["Suggestion C"],
        },
    )
    text = result.feedback_text()
    assert "Issue A" in text
    assert "Issue B" in text
    assert "Suggestion C" in text


def test_parse_eval_response_valid():
    response = json.dumps({
        "verdict": "publish",
        "non_negotiables": {"keine_unbelegten_rechtsaussagen": True},
        "scores": {"praezision": 0.96},
        "feedback": {"blocking_issues": [], "improvement_suggestions": []},
    })
    result = parse_eval_response(response)
    assert result.verdict == "publish"


def test_parse_eval_response_with_markdown():
    response = "Here is my evaluation:\n```json\n" + json.dumps({
        "verdict": "reject",
        "non_negotiables": {"keine_unbelegten_rechtsaussagen": False},
        "scores": {"praezision": 0.80},
        "feedback": {"blocking_issues": ["Error"]},
    }) + "\n```"
    result = parse_eval_response(response)
    assert result.verdict == "reject"


def test_parse_eval_response_invalid():
    with pytest.raises(ValueError):
        parse_eval_response("This is not JSON at all")


@pytest.fixture
def config(tmp_path):
    content_root = tmp_path / "content"
    art_dir = content_root / "or" / "art-041"
    art_dir.mkdir(parents=True)
    (art_dir / "meta.yaml").write_text("law: OR\narticle: 41\n")
    (art_dir / "summary.md").write_text("# Übersicht\n\nTest.")
    return AgentConfig(content_root=content_root)


def test_evaluate_layer_calls_query(config):
    verdict = {
        "verdict": "publish",
        "non_negotiables": {"keine_unbelegten_rechtsaussagen": True},
        "scores": {"praezision": 0.96},
        "feedback": {"blocking_issues": []},
    }
    mock_run = AsyncMock(return_value=(json.dumps(verdict), 0.05))
    with patch("agents.evaluator.run_agent", mock_run):
        result = asyncio.run(evaluate_layer(config, "OR", 41, "", "summary"))
        assert result.verdict == "publish"


def test_merge_eval_results_all_pass():
    results = {
        "claude": EvalResult(
            verdict="publish",
            non_negotiables={"keine_unbelegten_rechtsaussagen": True},
            scores={"praezision": 0.97},
            feedback={"blocking_issues": [], "improvement_suggestions": []},
        ),
        "chatgpt": EvalResult(
            verdict="publish",
            non_negotiables={"keine_unbelegten_rechtsaussagen": True},
            scores={"praezision": 0.95},
            feedback={"blocking_issues": [], "improvement_suggestions": []},
        ),
        "grok": EvalResult(
            verdict="publish",
            non_negotiables={"keine_unbelegten_rechtsaussagen": True},
            scores={"praezision": 0.96},
            feedback={"blocking_issues": [], "improvement_suggestions": []},
        ),
    }
    merged = merge_eval_results(results)
    assert merged.passed is True
    assert merged.scores["praezision"] == 0.95  # minimum


def test_merge_eval_results_one_rejects():
    results = {
        "claude": EvalResult(
            verdict="publish",
            non_negotiables={"keine_unbelegten_rechtsaussagen": True},
            scores={"praezision": 0.97},
            feedback={"blocking_issues": []},
        ),
        "chatgpt": EvalResult(
            verdict="reject",
            non_negotiables={"keine_unbelegten_rechtsaussagen": False},
            scores={"praezision": 0.80},
            feedback={"blocking_issues": ["Missing source in N. 3"]},
        ),
        "grok": EvalResult(
            verdict="publish",
            non_negotiables={"keine_unbelegten_rechtsaussagen": True},
            scores={"praezision": 0.96},
            feedback={"blocking_issues": []},
        ),
    }
    merged = merge_eval_results(results)
    assert merged.passed is False
    assert "[chatgpt]" in merged.feedback_text().lower()


def test_merge_eval_results_all_reject():
    results = {
        "claude": EvalResult(
            verdict="reject", non_negotiables={}, scores={"praezision": 0.80},
            feedback={"blocking_issues": ["Issue A"]},
        ),
        "grok": EvalResult(
            verdict="reject", non_negotiables={}, scores={"praezision": 0.75},
            feedback={"blocking_issues": ["Issue B"]},
        ),
    }
    merged = merge_eval_results(results)
    assert merged.passed is False
    assert merged.scores["praezision"] == 0.75
    text = merged.feedback_text()
    assert "Issue A" in text
    assert "Issue B" in text
