"""Tests for the bootstrap state tracker."""
from __future__ import annotations

import pytest

from agents.bootstrap import BootstrapState


@pytest.fixture
def state_path(tmp_path):
    return tmp_path / "bootstrap_state.json"


def test_new_state_is_empty(state_path):
    state = BootstrapState(state_path)
    assert state.total == 0
    assert state.completed == 0
    assert state.failed == 0


def test_add_articles(state_path):
    state = BootstrapState(state_path)
    state.add_article("OR", 41, "")
    state.add_article("OR", 42, "")
    assert state.total == 2
    assert state.pending == 2


def test_mark_completed(state_path):
    state = BootstrapState(state_path)
    state.add_article("OR", 41, "")
    state.mark_completed("OR", 41, "", cost=0.15)
    assert state.completed == 1
    assert state.pending == 0
    assert state.total_cost == pytest.approx(0.15)


def test_mark_failed(state_path):
    state = BootstrapState(state_path)
    state.add_article("OR", 41, "")
    state.mark_failed("OR", 41, "", error="Quality too low")
    assert state.failed == 1
    assert state.pending == 0


def test_persistence_roundtrip(state_path):
    state = BootstrapState(state_path)
    state.add_article("OR", 41, "")
    state.mark_completed("OR", 41, "", cost=0.10)
    state.add_article("OR", 42, "")
    state.save()

    loaded = BootstrapState.load(state_path)
    assert loaded.total == 2
    assert loaded.completed == 1
    assert loaded.pending == 1
    assert loaded.total_cost == pytest.approx(0.10)


def test_pending_articles(state_path):
    state = BootstrapState(state_path)
    state.add_article("OR", 41, "")
    state.add_article("OR", 42, "")
    state.add_article("BV", 1, "")
    state.mark_completed("OR", 41, "", cost=0.10)

    pending = state.get_pending()
    assert len(pending) == 2
    keys = [(a.law, a.article_number) for a in pending]
    assert ("OR", 42) in keys
    assert ("BV", 1) in keys


def test_skip_already_added(state_path):
    state = BootstrapState(state_path)
    state.add_article("OR", 41, "")
    state.add_article("OR", 41, "")
    assert state.total == 1


def test_cost_budget_exceeded(state_path):
    state = BootstrapState(state_path)
    state.add_article("OR", 41, "")
    state.mark_completed("OR", 41, "", cost=100.0)
    assert state.budget_exceeded(max_budget=50.0) is True
    assert state.budget_exceeded(max_budget=200.0) is False


def test_summary(state_path):
    state = BootstrapState(state_path)
    state.add_article("OR", 41, "")
    state.add_article("OR", 42, "")
    state.mark_completed("OR", 41, "", cost=0.15)
    summary = state.summary()
    assert summary["total"] == 2
    assert summary["completed"] == 1
    assert summary["pending"] == 1
    assert summary["failed"] == 0
    assert summary["total_cost"] == pytest.approx(0.15)
