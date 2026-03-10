"""Tests for system prompt builder."""
from __future__ import annotations

from pathlib import Path

import pytest

from agents.prompts import (
    build_evaluator_prompt,
    build_law_agent_prompt,
    build_translator_prompt,
)


@pytest.fixture
def guidelines_root():
    """Use the actual guidelines directory."""
    root = Path("guidelines")
    assert root.exists(), "guidelines/ directory must exist"
    return root


def test_law_agent_prompt_includes_global(guidelines_root):
    prompt = build_law_agent_prompt(guidelines_root, "OR", "summary")
    assert "Akademische Exzellenz" in prompt
    assert "Präzision" in prompt


def test_law_agent_prompt_includes_law_specific(guidelines_root):
    prompt = build_law_agent_prompt(guidelines_root, "OR", "doctrine")
    assert "Obligationenrecht" in prompt
    assert "BSK OR" in prompt


def test_law_agent_prompt_includes_layer_instructions(guidelines_root):
    prompt_summary = build_law_agent_prompt(guidelines_root, "OR", "summary")
    assert "Übersicht" in prompt_summary or "Summary" in prompt_summary
    assert "B1" in prompt_summary or "150" in prompt_summary

    prompt_doctrine = build_law_agent_prompt(guidelines_root, "OR", "doctrine")
    assert "Randziffern" in prompt_doctrine or "N." in prompt_doctrine

    prompt_caselaw = build_law_agent_prompt(guidelines_root, "OR", "caselaw")
    assert "BGE" in prompt_caselaw or "Leitentscheid" in prompt_caselaw


def test_evaluator_prompt_includes_rubric(guidelines_root):
    prompt = build_evaluator_prompt(guidelines_root)
    assert "Unverhandelbare" in prompt or "non-negotiable" in prompt.lower()
    assert "publish" in prompt or "reject" in prompt


def test_translator_prompt_french(guidelines_root):
    prompt = build_translator_prompt(guidelines_root, "fr")
    assert "French" in prompt or "français" in prompt.lower()


def test_translator_prompt_italian(guidelines_root):
    prompt = build_translator_prompt(guidelines_root, "it")
    assert "Italian" in prompt or "italiano" in prompt.lower()


def test_invalid_layer_type(guidelines_root):
    with pytest.raises(ValueError):
        build_law_agent_prompt(guidelines_root, "OR", "invalid")


def test_all_eight_laws(guidelines_root):
    for law in ("BV", "ZGB", "OR", "ZPO", "StGB", "StPO", "SchKG", "VwVG"):
        prompt = build_law_agent_prompt(guidelines_root, law, "summary")
        assert len(prompt) > 500  # Should contain substantial guidelines
