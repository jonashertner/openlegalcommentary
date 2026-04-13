# Cross-Model Evaluation & Opus Extended Thinking — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add triple-evaluator pipeline (Claude Opus, ChatGPT 5.4 Pro, Grok 4.20) and extended thinking support for Opus doctrine generation, then A/B test.

**Architecture:** New `agents/openai_client.py` wraps the OpenAI SDK for both OpenAI and xAI APIs. `agents/evaluator.py` orchestrates three parallel evaluators with merged feedback. `agents/anthropic_client.py` gains `opus-thinking` mode with extended thinking enabled.

**Tech Stack:** Python 3.12, `openai` SDK, `anthropic` SDK, `asyncio.gather`, pytest with AsyncMock

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `agents/openai_client.py` | Create | OpenAI/xAI evaluation API client |
| `agents/anthropic_client.py` | Modify | Add `opus-thinking` model with extended thinking |
| `agents/config.py` | Modify | Add evaluator_2, evaluator_3, evaluator_mode fields |
| `agents/evaluator.py` | Modify | Multi-evaluator orchestration, merged feedback |
| `agents/prompts.py` | Modify | Add `build_evaluator_prompt_inline()` for non-tool evaluators |
| `tests/test_openai_client.py` | Create | Tests for OpenAI/xAI client |
| `tests/test_evaluator.py` | Modify | Tests for multi-evaluator merging |
| `tests/test_generation.py` | Modify | Update mocks to match new evaluator signature |
| `pyproject.toml` | Modify | Add `openai` dependency |

---

### Task 1: Add `openai` dependency

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add openai to dependencies**

In `pyproject.toml`, add `"openai>=1.30"` to the `dependencies` list:

```toml
dependencies = [
    "pydantic>=2.0",
    "httpx>=0.27",
    "pyyaml>=6.0",
    "anthropic>=0.84.0",
    "pymupdf>=1.24",
    "openai>=1.30",
]
```

- [ ] **Step 2: Install**

Run: `uv sync`
Expected: resolves and installs `openai` package

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add openai SDK dependency for cross-model evaluation"
```

---

### Task 2: Create `agents/openai_client.py`

**Files:**
- Create: `agents/openai_client.py`
- Create: `tests/test_openai_client.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_openai_client.py`:

```python
"""Tests for the OpenAI/xAI evaluation client."""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.openai_client import run_evaluation


def _mock_chat_response(content: str):
    """Build a mock OpenAI ChatCompletion response."""
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


def test_run_evaluation_returns_text_and_cost():
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


def test_run_evaluation_uses_correct_base_url():
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_openai_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.openai_client'`

- [ ] **Step 3: Write the implementation**

Create `agents/openai_client.py`:

```python
"""OpenAI/xAI API client for cross-model evaluation.

Uses the OpenAI Python SDK, which is compatible with xAI's Grok API
via base_url override. Evaluation-only — no tool use.
"""
from __future__ import annotations

import logging
import os

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


async def run_evaluation(
    *,
    system_prompt: str,
    prompt: str,
    model: str,
    base_url: str,
    api_key_env: str,
) -> tuple[str, float]:
    """Run a single evaluation call against an OpenAI-compatible API.

    Args:
        system_prompt: The evaluation rubric / system instructions.
        prompt: The user prompt containing the content to evaluate.
        model: Model ID (e.g. "gpt-5.4-pro", "grok-4.20-0309-reasoning").
        base_url: API base URL ("https://api.openai.com/v1" or "https://api.x.ai/v1").
        api_key_env: Name of the environment variable holding the API key.

    Returns:
        (response_text, estimated_cost_usd)

    Raises:
        ValueError: If the API key environment variable is not set.
    """
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise ValueError(
            f"API key environment variable '{api_key_env}' is not set"
        )

    client = AsyncOpenAI(base_url=base_url, api_key=api_key)

    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        max_tokens=4096,
    )

    text = response.choices[0].message.content or ""
    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0

    # Rough cost estimate — actual pricing varies by model.
    # Using conservative $10/M input, $30/M output as a baseline.
    cost = (prompt_tokens * 10.0 + completion_tokens * 30.0) / 1_000_000

    logger.info(
        "run_evaluation(%s @ %s) tokens: in=%d out=%d cost=$%.4f",
        model, base_url, prompt_tokens, completion_tokens, cost,
    )

    return text, cost
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_openai_client.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add agents/openai_client.py tests/test_openai_client.py
git commit -m "feat: add OpenAI/xAI evaluation client"
```

---

### Task 3: Add `opus-thinking` to Anthropic client

**Files:**
- Modify: `agents/anthropic_client.py`

- [ ] **Step 1: Update MODEL_MAP and add thinking support**

In `agents/anthropic_client.py`, update the `MODEL_MAP` and the `run_agent` function:

```python
MODEL_MAP = {
    "opus": "claude-opus-4-6",
    "opus-thinking": "claude-opus-4-6",
    "sonnet": "claude-sonnet-4-6",
}
```

In the `run_agent` function, after `model_id = MODEL_MAP.get(model, model)`, add thinking mode detection and adjust the `messages.create()` call:

```python
    model_id = MODEL_MAP.get(model, model)
    use_thinking = model == "opus-thinking"
    client = anthropic.Anthropic()
```

Replace the `response = client.messages.create(...)` block inside the turn loop:

```python
        create_kwargs = dict(
            model=model_id,
            max_tokens=16384 if use_thinking else 8192,
            system=system_blocks,
            tools=tool_schemas,
            messages=messages,
        )
        if use_thinking:
            create_kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": 100000,
            }
        response = client.messages.create(**create_kwargs)
```

In the text extraction loop, skip thinking blocks:

```python
        for block in assistant_content:
            if block.type == "text":
                final_text = block.text
            # Skip thinking blocks — they don't contain usable output
```

In the cost calculation, add thinking token tracking. After the existing `total_output_tokens` line:

```python
    total_thinking_tokens = 0
```

Inside the turn loop, after the existing usage tracking:

```python
        total_thinking_tokens += getattr(
            usage, "thinking_tokens", 0,
        ) or 0
```

Add thinking tokens to cost (billed at output rate):

```python
    cost = (
        total_input_tokens * input_rate
        + total_cache_creation_tokens * cache_write_rate
        + total_cache_read_tokens * cache_read_rate
        + (total_output_tokens + total_thinking_tokens) * output_rate
    ) / 1_000_000
```

- [ ] **Step 2: Run existing tests**

Run: `uv run pytest tests/ -v -k "test_evaluator or test_generation" --timeout=10`
Expected: All existing tests pass (they mock `run_agent` so the thinking changes don't affect them)

- [ ] **Step 3: Commit**

```bash
git add agents/anthropic_client.py
git commit -m "feat: add opus-thinking mode with extended thinking"
```

---

### Task 4: Update `agents/config.py`

**Files:**
- Modify: `agents/config.py`
- Modify: `tests/test_config.py`

- [ ] **Step 1: Add new config fields**

Add these fields to the `AgentConfig` dataclass after `model_translator`:

```python
    # Cross-model evaluation
    model_evaluator_2: str = "chatgpt"
    model_evaluator_3: str = "grok"
    evaluator_mode: str = "all_must_pass"  # "all_must_pass", "majority", "claude_only"
```

- [ ] **Step 2: Run existing config tests**

Run: `uv run pytest tests/test_config.py -v`
Expected: All pass (new fields have defaults, no breakage)

- [ ] **Step 3: Commit**

```bash
git add agents/config.py
git commit -m "feat: add cross-model evaluator config fields"
```

---

### Task 5: Add inline evaluator prompt builder

**Files:**
- Modify: `agents/prompts.py`

- [ ] **Step 1: Add `build_evaluator_prompt_inline()`**

Add this function after the existing `build_evaluator_prompt()` in `agents/prompts.py`:

```python
def build_evaluator_prompt_inline(guidelines_root: Path) -> str:
    """Build evaluator system prompt for non-tool evaluators (OpenAI/xAI).

    Same rubric as build_evaluator_prompt(), but instructs the evaluator
    to evaluate the content provided directly in the user message rather
    than reading it via tools.
    """
    evaluate_md = (guidelines_root / "evaluate.md").read_text()

    return (
        "You are the quality evaluator for openlegalcommentary.ch. Your role is to "
        "assess whether generated commentary meets the publication threshold.\n\n"
        "You evaluate rigorously and objectively. "
        "You do not generate commentary — you only judge it.\n\n"
        f"## Evaluation Rubric\n\n{evaluate_md}\n\n"
        "## Your Task\n\n"
        "The generated content, article text, and reference data are provided "
        "directly in the user message below. Evaluate the content against the rubric.\n\n"
        "1. Evaluate against all non-negotiable criteria (binary pass/fail)\n"
        "2. Score all five dimensions (0.0–1.0)\n"
        "3. When doctrinal reference data is provided, cross-check cited BSK/CR "
        "authors and Randziffern against the reference data\n"
        "4. When preparatory materials reference data is provided, verify that "
        "cited BBl page references and legislative intent claims match the "
        "reference data. Reject fabricated Botschaft quotes.\n"
        "5. Do NOT reject content solely because you cannot "
        "verify external citations — evaluate what is written.\n"
        "6. Return your verdict as JSON in EXACTLY this format:\n\n"
        "```json\n"
        "{\n"
        '  "verdict": "publish" or "reject",\n'
        '  "non_negotiables": {\n'
        '    "keine_unbelegten_rechtsaussagen": true/false,\n'
        '    "keine_faktischen_fehler": true/false,\n'
        '    "keine_fehlenden_leitentscheide": true/false,\n'
        '    "korrekte_legalbegriffe": true/false,\n'
        '    "strukturelle_vollstaendigkeit": true/false\n'
        "  },\n"
        '  "scores": {\n'
        '    "praezision": 0.00,\n'
        '    "konzision": 0.00,\n'
        '    "zugaenglichkeit": 0.00,\n'
        '    "relevanz": 0.00,\n'
        '    "akademische_strenge": 0.00\n'
        "  },\n"
        '  "feedback": {\n'
        '    "blocking_issues": ["..."],\n'
        '    "improvement_suggestions": ["..."]\n'
        "  }\n"
        "}\n"
        "```\n\n"
        'A "publish" verdict requires ALL non-negotiables to be true AND all scores to '
        "meet thresholds (precision \u2265 0.95, concision \u2265 0.90, "
        "accessibility \u2265 0.90, relevance \u2265 0.90, academic rigor \u2265 0.95)."
    )
```

- [ ] **Step 2: Run prompt tests**

Run: `uv run pytest tests/test_prompts.py -v`
Expected: All pass

- [ ] **Step 3: Commit**

```bash
git add agents/prompts.py
git commit -m "feat: add inline evaluator prompt for non-tool evaluators"
```

---

### Task 6: Rewrite `agents/evaluator.py` for multi-evaluator

**Files:**
- Modify: `agents/evaluator.py`
- Modify: `tests/test_evaluator.py`

- [ ] **Step 1: Write tests for multi-evaluator merging**

Add these tests to `tests/test_evaluator.py`:

```python
from agents.evaluator import merge_eval_results


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
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_evaluator.py -v -k "merge"`
Expected: FAIL — `ImportError: cannot import name 'merge_eval_results'`

- [ ] **Step 3: Implement `merge_eval_results()`**

Add to `agents/evaluator.py`, after the `parse_eval_response` function:

```python
def merge_eval_results(results: dict[str, EvalResult]) -> EvalResult:
    """Merge multiple evaluator results into a single verdict.

    All must pass for the merged verdict to be "publish".
    Scores take the minimum per dimension across all evaluators.
    Feedback is combined with source labels.
    """
    if not results:
        raise ValueError("No evaluation results to merge")

    all_passed = all(r.passed for r in results.values())

    # Merge scores: minimum per dimension
    all_dims: set[str] = set()
    for r in results.values():
        all_dims.update(r.scores.keys())
    merged_scores = {}
    for dim in all_dims:
        values = [r.scores[dim] for r in results.values() if dim in r.scores]
        merged_scores[dim] = min(values) if values else 0.0

    # Merge non-negotiables: AND across evaluators
    all_nn_keys: set[str] = set()
    for r in results.values():
        all_nn_keys.update(r.non_negotiables.keys())
    merged_nn = {}
    for key in all_nn_keys:
        merged_nn[key] = all(
            r.non_negotiables.get(key, True) for r in results.values()
        )

    # Merge feedback with source labels
    merged_blocking: list[str] = []
    merged_suggestions: list[str] = []
    for name, r in results.items():
        for issue in r.feedback.get("blocking_issues", []):
            merged_blocking.append(f"[{name}] {issue}")
        for sug in r.feedback.get("improvement_suggestions", []):
            merged_suggestions.append(f"[{name}] {sug}")

    return EvalResult(
        verdict="publish" if all_passed else "reject",
        non_negotiables=merged_nn,
        scores=merged_scores,
        feedback={
            "blocking_issues": merged_blocking,
            "improvement_suggestions": merged_suggestions,
        },
    )
```

- [ ] **Step 4: Run merge tests**

Run: `uv run pytest tests/test_evaluator.py -v -k "merge"`
Expected: 3 passed

- [ ] **Step 5: Rewrite `evaluate_layer()` for multi-evaluator orchestration**

Replace the existing `evaluate_layer()` in `agents/evaluator.py`:

```python
import asyncio
import os

from agents.openai_client import run_evaluation as run_openai_evaluation
from agents.prompts import build_evaluator_prompt, build_evaluator_prompt_inline


async def _evaluate_anthropic(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_type: str,
) -> EvalResult:
    """Run evaluation via Claude Opus (existing logic, with tools)."""
    system_prompt = build_evaluator_prompt(config.guidelines_root)
    content_tools = create_content_tools(config.content_root)
    suffix_str = article_suffix or ""

    article_text = format_article_text(law, article_number, suffix_str)
    article_text_block = ""
    if article_text:
        article_text_block = (
            f"\n\nHere is the official Gesetzestext of "
            f"Art. {article_number}{suffix_str} {law}:\n\n{article_text}\n"
        )

    commentary_refs_block = ""
    if layer_type in ("doctrine", "summary"):
        commentary_refs_block = format_commentary_refs(
            config.commentary_refs_root, law, article_number, suffix_str,
        )

    prep_materials_block = ""
    if layer_type in ("doctrine", "summary"):
        prep_materials_block = format_preparatory_materials(
            law, article_number, suffix_str,
        )

    prompt = (
        f"Evaluate the {layer_type} layer for "
        f"Art. {article_number}{suffix_str} {law}. "
        f"Read the content and evaluate its quality "
        f"based on the rubric criteria. "
        f"Do NOT reject content solely because you cannot "
        f"verify external citations — evaluate what is written."
        f"{article_text_block}"
        f"Return your JSON verdict."
    )
    if commentary_refs_block:
        prompt += f"\n\n{commentary_refs_block}"
    if prep_materials_block:
        prompt += f"\n\n{prep_materials_block}"

    response_text, _ = await run_agent(
        system_prompt=system_prompt,
        prompt=prompt,
        model=config.model_evaluator,
        content_tools=content_tools,
        opencaselaw_tools=None,
        allowed_tools=["read_article_meta", "read_layer_content"],
        max_turns=config.max_turns_per_agent,
    )
    return parse_eval_response(response_text)


def _build_inline_eval_prompt(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_type: str,
) -> str:
    """Build evaluation prompt with content inlined (for non-tool evaluators)."""
    suffix_str = article_suffix or ""

    # Read the generated content from disk
    dir_name = f"art-{article_number:03d}{suffix_str}"
    layer_path = config.content_root / law.lower() / dir_name / f"{layer_type}.md"
    layer_content = layer_path.read_text() if layer_path.exists() else ""

    article_text = format_article_text(law, article_number, suffix_str)

    parts = [
        f"Evaluate the {layer_type} layer for "
        f"Art. {article_number}{suffix_str} {law}.",
    ]

    if article_text:
        parts.append(
            f"\n## Gesetzestext\n\n{article_text}"
        )

    parts.append(
        f"\n## Generated Content\n\n{layer_content}"
    )

    if layer_type in ("doctrine", "summary"):
        refs = format_commentary_refs(
            config.commentary_refs_root, law, article_number, suffix_str,
        )
        if refs:
            parts.append(f"\n\n{refs}")
        prep = format_preparatory_materials(law, article_number, suffix_str)
        if prep:
            parts.append(f"\n\n{prep}")

    parts.append("\nReturn your JSON verdict.")
    return "\n".join(parts)


async def _evaluate_external(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_type: str,
    model: str,
    base_url: str,
    api_key_env: str,
    evaluator_name: str,
) -> EvalResult:
    """Run evaluation via an OpenAI-compatible API (ChatGPT/Grok)."""
    system_prompt = build_evaluator_prompt_inline(config.guidelines_root)
    prompt = _build_inline_eval_prompt(
        config, law, article_number, article_suffix, layer_type,
    )
    response_text, _ = await run_openai_evaluation(
        system_prompt=system_prompt,
        prompt=prompt,
        model=model,
        base_url=base_url,
        api_key_env=api_key_env,
    )
    return parse_eval_response(response_text)


# Model ID and endpoint mapping for external evaluators
EVALUATOR_REGISTRY = {
    "chatgpt": {
        "model": "chatgpt-5.4-pro",  # confirm exact model ID
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
    },
    "grok": {
        "model": "grok-4.20-0309-reasoning",
        "base_url": "https://api.x.ai/v1",
        "api_key_env": "XAI_API_KEY",
    },
}


async def evaluate_layer(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_type: str,
) -> EvalResult:
    """Run evaluation across all configured evaluators.

    Returns a single merged EvalResult. All evaluators must pass
    for the merged verdict to be "publish".
    """
    tasks: dict[str, asyncio.Task] = {}

    # Always run Claude Opus
    tasks["claude"] = asyncio.ensure_future(
        _evaluate_anthropic(config, law, article_number, article_suffix, layer_type)
    )

    # External evaluators — skip if API key not set
    for eval_key, eval_cfg in EVALUATOR_REGISTRY.items():
        if not os.environ.get(eval_cfg["api_key_env"]):
            logger.info("Skipping %s evaluator — %s not set", eval_key, eval_cfg["api_key_env"])
            continue
        tasks[eval_key] = asyncio.ensure_future(
            _evaluate_external(
                config, law, article_number, article_suffix, layer_type,
                model=eval_cfg["model"],
                base_url=eval_cfg["base_url"],
                api_key_env=eval_cfg["api_key_env"],
                evaluator_name=eval_key,
            )
        )

    # Await all
    results: dict[str, EvalResult] = {}
    for name, task in tasks.items():
        try:
            results[name] = await task
            logger.info(
                "Evaluator %s: verdict=%s scores=%s",
                name, results[name].verdict, results[name].scores,
            )
        except Exception as e:
            logger.error("Evaluator %s failed: %s — treating as reject", name, e)
            results[name] = EvalResult(
                verdict="reject",
                feedback={"blocking_issues": [f"Evaluator {name} error: {e}"]},
            )

    return merge_eval_results(results)
```

- [ ] **Step 6: Update existing test to match new imports**

In `tests/test_evaluator.py`, update the `test_evaluate_layer_calls_query` test. The existing test mocks `agents.evaluator.run_agent` — it now needs to mock `_evaluate_anthropic` or the underlying `run_agent` still works since `_evaluate_anthropic` calls it. The mock path stays the same:

```python
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
```

This test should still work since it only sets `ANTHROPIC_API_KEY` implicitly (mocked), and `OPENAI_API_KEY`/`XAI_API_KEY` are not set so external evaluators are skipped.

- [ ] **Step 7: Run all evaluator tests**

Run: `uv run pytest tests/test_evaluator.py -v`
Expected: All pass (existing + 3 new merge tests)

- [ ] **Step 8: Run full test suite**

Run: `uv run pytest tests/ -v --timeout=30`
Expected: All pass

- [ ] **Step 9: Commit**

```bash
git add agents/evaluator.py agents/prompts.py tests/test_evaluator.py
git commit -m "feat: multi-evaluator pipeline with Claude/ChatGPT/Grok"
```

---

### Task 7: Update generation.py mocks and verify integration

**Files:**
- Modify: `tests/test_generation.py` (verify, no changes expected)

- [ ] **Step 1: Run generation tests**

Run: `uv run pytest tests/test_generation.py -v`
Expected: All pass — the generation tests mock `evaluate_layer` at the function level, so the internal multi-evaluator changes are transparent.

If any fail due to import changes, fix the mock paths.

- [ ] **Step 2: Run full test suite + lint**

Run: `uv run pytest tests/ -v --timeout=30 && uv run ruff check .`
Expected: All tests pass, no lint errors

- [ ] **Step 3: Commit (only if fixes were needed)**

```bash
git add tests/test_generation.py
git commit -m "fix: update generation test mocks for multi-evaluator"
```

---

### Task 8: A/B test — run and document

**Files:**
- Create: `docs/superpowers/specs/2026-04-13-opus-thinking-ab-test-results.md`

This task is manual — run the pipeline commands and document results.

- [ ] **Step 1: Generate Art. 99 BV with Opus thinking**

Run:
```bash
uv run python -m agents.pipeline single BV 99 --layers doctrine --model-override opus-thinking
```

Note: if `--model-override` is not yet a CLI arg, temporarily edit `config.py` to set `model_doctrine = "opus-thinking"` and revert after.

Record: generation time, cost, evaluator verdicts from all 3 evaluators.

- [ ] **Step 2: Generate Art. 36 BV with Opus thinking**

Run:
```bash
uv run python -m agents.pipeline single BV 36 --layers doctrine --model-override opus-thinking
```

Record: generation time, cost, evaluator verdicts.

- [ ] **Step 3: Re-evaluate existing Sonnet versions with triple evaluator**

Run the pipeline in evaluate-only mode on existing Art. 36 and Art. 10 doctrine (Sonnet 4.6 versions). If no evaluate-only mode exists, call `evaluate_layer` directly via a small script:

```python
import asyncio
from agents.config import AgentConfig
from agents.evaluator import evaluate_layer

async def main():
    config = AgentConfig()
    for art in [36, 10, 99]:
        result = await evaluate_layer(config, "BV", art, "", "doctrine")
        print(f"Art. {art}: {result.verdict} scores={result.scores}")

asyncio.run(main())
```

- [ ] **Step 4: Document results**

Create `docs/superpowers/specs/2026-04-13-opus-thinking-ab-test-results.md` with:

- Side-by-side scores per evaluator per article
- Cost comparison (Sonnet vs Opus thinking)
- Generation time comparison
- Recommendation: adopt / adopt-selectively / keep-sonnet

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/specs/2026-04-13-opus-thinking-ab-test-results.md
git commit -m "docs: Opus extended thinking A/B test results"
```
