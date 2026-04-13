# Cross-Model Evaluation & Opus Extended Thinking

Date: 2026-04-13

## Goal

1. Add cross-model evaluation: every generated article must pass three independent evaluators (Claude Opus 4.6, ChatGPT 5.4 Pro, Grok 4.20 Reasoning) before publication.
2. A/B test Opus 4.6 extended thinking as the doctrine generator against the current Sonnet 4.6 baseline.

## Architecture

### New module: `agents/openai_client.py`

Thin wrapper around the OpenAI Python SDK. Handles both OpenAI and xAI since xAI's API is OpenAI SDK-compatible.

```python
async def run_evaluation(
    *, system_prompt: str, prompt: str,
    model: str, base_url: str, api_key_env: str
) -> tuple[str, float]
```

- `base_url="https://api.openai.com/v1"` for ChatGPT
- `base_url="https://api.x.ai/v1"` for Grok
- No tool use — evaluators receive content inline in the prompt
- Returns `(response_text, estimated_cost_usd)`

### Changes to `agents/anthropic_client.py`

- Add `"opus-thinking"` to `MODEL_MAP` → `"claude-opus-4-6"`
- When model is `"opus-thinking"`:
  - Set `thinking: {"type": "enabled", "budget_tokens": null}` (no cap)
  - Increase `max_tokens` to 16384 to accommodate output after thinking
- Extended thinking tokens included in cost estimate at standard input rate

### Changes to `agents/config.py`

```python
# Generation
model_doctrine: str = "sonnet"  # also accepts "opus-thinking"

# Evaluation
model_evaluator: str = "opus"              # Claude Opus 4.6
model_evaluator_2: str = "chatgpt"         # ChatGPT 5.4 Pro
model_evaluator_3: str = "grok"            # Grok 4.20 Reasoning
evaluator_mode: str = "all_must_pass"      # future: "majority", "advisory"
```

### Changes to `agents/evaluator.py`

Current `evaluate_layer()` becomes the orchestrator.

```
evaluate_layer()
  ├── _evaluate_anthropic()   # existing logic, Claude Opus with tools
  ├── _evaluate_openai()      # ChatGPT 5.4 Pro, content inline
  └── _evaluate_xai()         # Grok 4.20 Reasoning, content inline
```

**Parallel execution:** All three run via `asyncio.gather`.

**Content injection for non-Anthropic evaluators:** Before calling OpenAI/xAI, read the generated layer content from disk and inject it directly into the user prompt. These evaluators have no tool access.

**Verdict logic (`all_must_pass`):** All three must return `verdict: "publish"`. If any rejects, the combined result is `verdict: "reject"` with merged feedback.

**Shared evaluation prompt:** Same rubric and JSON output schema across all three. The evaluation prompt from `build_evaluator_prompt()` is reused. Only difference: Claude's prompt tells it to use tools to read content; OpenAI/Grok's prompt includes the content inline.

**Model IDs:**
- Claude Opus: `claude-opus-4-6` (via Anthropic API)
- ChatGPT: `chatgpt-5.4-pro` (via OpenAI API, confirm exact ID)
- Grok: `grok-4.20-0309-reasoning` (via xAI API, OpenAI SDK-compatible)

### Changes to `agents/generation.py`

**Interface unchanged:** `evaluate_layer()` still returns a single `EvalResult`. Internally it runs 3 evaluators, merges verdicts (all must pass), and combines feedback. The generation loop's pass/fail logic does not change.

**Feedback merging on retry:** When evaluators reject, their feedback is merged into the single `EvalResult` with source labels:

```
[Claude Opus] Blocking issues:
- Missing Entstehungsgeschichte section

[Grok] Blocking issues:
- Art. 36 cross-reference incorrect
```

**Scores:** The merged `EvalResult.scores` takes the minimum per dimension across all evaluators. Individual per-evaluator results are logged for diagnostics.

**meta.yaml quality score:** Minimum quality score across all evaluators.

### Environment variables

- `ANTHROPIC_API_KEY` (existing)
- `OPENAI_API_KEY` (new)
- `XAI_API_KEY` (new)

Pipeline runs without OpenAI/xAI keys — if keys are absent, those evaluators are skipped and only Claude evaluates (graceful degradation).

## A/B Test: Opus Extended Thinking

### Test articles

| Article | Complexity | Materialien | Why |
|---------|-----------|-------------|-----|
| Art. 99 BV (Geld- und Währungspolitik) | Medium | Yes | Substantive, not Grundrecht |
| Art. 36 BV (Einschränkung von Grundrechten) | Medium-hard | Yes | Key structural article |
| Art. 10 BV (Recht auf Leben) | Hard | Full (all 4 sources) | Already regenerated with Sonnet — baseline exists |

### Procedure

1. Generate Art. 99 and Art. 36 with `model_doctrine: "opus-thinking"` (Art. 10 already has a Sonnet 4.6 version)
2. Evaluate all 3 Opus-thinking versions with triple-evaluator pipeline
3. Re-evaluate existing Sonnet 4.6 versions of Art. 36 and Art. 10 with triple-evaluator pipeline (Art. 99 may not have a recent Sonnet version — generate one if needed)
4. Compare: quality scores from all 3 evaluators, evaluator feedback, generation cost, wall-clock time

### Decision criteria

- If Opus thinking scores measurably higher (>0.03 average across evaluators) AND cost is <10x Sonnet: adopt for all doctrine
- If quality delta is marginal (<0.02): keep Sonnet, the cost doesn't justify it
- If quality is higher but cost is >10x: adopt selectively for complex articles (Grundrechte, key procedural)

### Output

Results documented in `docs/superpowers/specs/2026-04-13-opus-thinking-ab-test-results.md`.

## Cost impact

| Component | Current | With cross-model eval |
|-----------|---------|----------------------|
| Generation (Sonnet) | ~$0.50-1.50 | unchanged |
| Generation (Opus thinking) | — | ~$5-15 (A/B test only) |
| Evaluation (Claude Opus) | ~$0.30-0.50 | ~$0.30-0.50 |
| Evaluation (ChatGPT) | — | ~$0.30-0.80 |
| Evaluation (Grok) | — | ~$0.30-0.80 |
| **Per-article total** | **~$1.50-3.00** | **~$2.50-5.00** |

Per-article cost increase of ~$1-2 for cross-model evaluation. Well within the CHF 6 per-article budget (which includes translation, retries, and reserve).

## Files to create/modify

| File | Action |
|------|--------|
| `agents/openai_client.py` | Create — OpenAI/xAI evaluation client |
| `agents/anthropic_client.py` | Modify — add `opus-thinking` support |
| `agents/config.py` | Modify — add evaluator_2, evaluator_3, evaluator_mode |
| `agents/evaluator.py` | Modify — parallel multi-evaluator orchestration |
| `agents/generation.py` | Modify — merged feedback, multi eval_results |
| `tests/test_evaluator.py` | Modify — tests for multi-evaluator logic |
| `tests/test_openai_client.py` | Create — tests for new client |
