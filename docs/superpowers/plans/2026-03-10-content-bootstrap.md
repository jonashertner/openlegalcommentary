# Content Bootstrap Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the bootstrap pipeline production-ready with resumability, progress tracking, cost budgets, and concurrency — then scaffold all ~4,050 articles and fetch their metadata.

**Architecture:** Add a `BootstrapState` tracker persisted to JSON that records per-article completion status, enabling crash-safe resumption. Enhance `bootstrap_law` with bounded concurrency via `asyncio.Semaphore` and a cost budget that halts processing when exceeded. Scaffold all article directories from opencaselaw article lists.

**Tech Stack:** Python, asyncio, pydantic, yaml, existing agents/ pipeline

---

## File Structure

| File | Responsibility |
|------|---------------|
| `agents/bootstrap.py` (create) | BootstrapState tracker, resumable bootstrap logic |
| `tests/test_bootstrap.py` (create) | Tests for state tracking and resumability |
| `agents/pipeline.py` (modify) | Wire enhanced bootstrap into CLI |
| `tests/test_pipeline.py` (modify) | Add test for enhanced bootstrap CLI |
| `scripts/scaffold_content.py` (modify) | Add title enrichment from article text |
| `scripts/article_lists.json` (create, runtime) | Cached article lists from opencaselaw |

---

## Chunk 1: Bootstrap State Tracker

### Task 1: Bootstrap state tracker

**Files:**
- Create: `agents/bootstrap.py`
- Create: `tests/test_bootstrap.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_bootstrap.py
"""Tests for the bootstrap state tracker."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.bootstrap import ArticleStatus, BootstrapState


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_bootstrap.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write agents/bootstrap.py**

```python
"""Bootstrap state tracker for resumable content generation.

Tracks per-article completion status in a JSON file, enabling
crash-safe resumption of the bootstrap pipeline.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class ArticleStatus:
    """Status of a single article in the bootstrap."""

    law: str
    article_number: int
    article_suffix: str = ""
    status: str = "pending"  # pending, completed, failed
    cost_usd: float = 0.0
    error: str = ""

    @property
    def key(self) -> str:
        return f"{self.law}:{self.article_number}:{self.article_suffix}"


class BootstrapState:
    """Persistent state tracker for bootstrap runs."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._articles: dict[str, ArticleStatus] = {}
        self._total_cost: float = 0.0

    @classmethod
    def load(cls, path: Path) -> BootstrapState:
        """Load state from a JSON file."""
        state = cls(path)
        if path.exists():
            data = json.loads(path.read_text())
            for item in data.get("articles", []):
                status = ArticleStatus(**item)
                state._articles[status.key] = status
            state._total_cost = data.get("total_cost", 0.0)
        return state

    def save(self) -> None:
        """Persist state to JSON file."""
        data = {
            "articles": [
                asdict(a) for a in self._articles.values()
            ],
            "total_cost": self._total_cost,
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False)
        )

    def add_article(
        self, law: str, article_number: int, suffix: str,
    ) -> None:
        """Register an article for bootstrapping (idempotent)."""
        key = f"{law}:{article_number}:{suffix}"
        if key not in self._articles:
            self._articles[key] = ArticleStatus(
                law=law,
                article_number=article_number,
                article_suffix=suffix,
            )

    def mark_completed(
        self, law: str, article_number: int, suffix: str,
        cost: float,
    ) -> None:
        """Mark an article as successfully completed."""
        key = f"{law}:{article_number}:{suffix}"
        if key in self._articles:
            self._articles[key].status = "completed"
            self._articles[key].cost_usd = cost
            self._total_cost += cost

    def mark_failed(
        self, law: str, article_number: int, suffix: str,
        error: str = "",
    ) -> None:
        """Mark an article as failed."""
        key = f"{law}:{article_number}:{suffix}"
        if key in self._articles:
            self._articles[key].status = "failed"
            self._articles[key].error = error

    def get_pending(self) -> list[ArticleStatus]:
        """Return all articles that still need processing."""
        return [
            a for a in self._articles.values()
            if a.status == "pending"
        ]

    def budget_exceeded(self, max_budget: float) -> bool:
        """Check if total cost exceeds budget."""
        return self._total_cost > max_budget

    @property
    def total(self) -> int:
        return len(self._articles)

    @property
    def completed(self) -> int:
        return sum(
            1 for a in self._articles.values()
            if a.status == "completed"
        )

    @property
    def failed(self) -> int:
        return sum(
            1 for a in self._articles.values()
            if a.status == "failed"
        )

    @property
    def pending(self) -> int:
        return sum(
            1 for a in self._articles.values()
            if a.status == "pending"
        )

    @property
    def total_cost(self) -> float:
        return self._total_cost

    def summary(self) -> dict:
        """Return a summary dict for logging/reporting."""
        return {
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "pending": self.pending,
            "total_cost": self._total_cost,
        }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_bootstrap.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add agents/bootstrap.py tests/test_bootstrap.py
git commit -m "feat: add bootstrap state tracker for resumable content generation"
```

---

## Chunk 2: Enhanced Bootstrap Pipeline

### Task 2: Resumable bootstrap with concurrency and cost budget

**Files:**
- Modify: `agents/pipeline.py`
- Modify: `tests/test_pipeline.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_pipeline.py`:

```python
# Add these imports at the top
from agents.bootstrap import BootstrapState

# Add these tests

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
        results = asyncio.run(
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_pipeline.py -v`
Expected: FAIL with `ImportError` (bootstrap_law_resumable not found)

- [ ] **Step 3: Add bootstrap_law_resumable to agents/pipeline.py**

Add to `agents/pipeline.py` (keep existing functions, add new ones):

```python
# Add import at top
from agents.bootstrap import BootstrapState

# Add new function after existing bootstrap_law

async def bootstrap_law_resumable(
    config: AgentConfig,
    law: str,
    state: BootstrapState,
    max_concurrent: int = 3,
    max_budget: float = 1000.0,
) -> list[LayerResult]:
    """Bootstrap a law with resumability and concurrency.

    Skips articles already completed in state.
    Stops if cost budget is exceeded.
    Processes up to max_concurrent articles in parallel.
    Saves state after each article completes.
    """
    import yaml

    law_dir = config.content_root / law.lower()
    if not law_dir.exists():
        logger.error(
            "No content directory for %s at %s", law, law_dir,
        )
        return []

    # Register all articles in state (idempotent)
    for art_dir in sorted(law_dir.iterdir()):
        if not art_dir.is_dir():
            continue
        if not art_dir.name.startswith("art-"):
            continue
        meta_path = art_dir / "meta.yaml"
        if not meta_path.exists():
            continue
        meta = yaml.safe_load(meta_path.read_text()) or {}
        article_number = meta.get("article", 0)
        article_suffix = meta.get("article_suffix", "")
        if article_number > 0:
            state.add_article(law, article_number, article_suffix)

    state.save()

    # Filter to pending articles for this law
    pending = [
        a for a in state.get_pending() if a.law == law
    ]

    if not pending:
        logger.info("No pending articles for %s", law)
        return []

    logger.info(
        "Bootstrap %s: %d pending articles "
        "(max_concurrent=%d, max_budget=$%.2f)",
        law, len(pending), max_concurrent, max_budget,
    )

    results: list[LayerResult] = []
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _process_one(article: "ArticleStatus"):
        async with semaphore:
            if state.budget_exceeded(max_budget):
                return []

            logger.info(
                "Processing Art. %d%s %s (%d/%d)",
                article.article_number,
                article.article_suffix,
                article.law,
                state.completed + 1,
                state.total,
            )

            try:
                art_results = await bootstrap_article(
                    config, article.law,
                    article.article_number,
                    article.article_suffix,
                )
                cost = sum(r.cost_usd for r in art_results)
                all_passed = all(
                    r.success for r in art_results
                )

                if all_passed:
                    state.mark_completed(
                        article.law,
                        article.article_number,
                        article.article_suffix,
                        cost=cost,
                    )
                else:
                    state.mark_failed(
                        article.law,
                        article.article_number,
                        article.article_suffix,
                        error="One or more layers failed",
                    )

                state.save()
                return art_results

            except Exception as e:
                logger.exception(
                    "Error processing Art. %d%s %s",
                    article.article_number,
                    article.article_suffix,
                    article.law,
                )
                state.mark_failed(
                    article.law,
                    article.article_number,
                    article.article_suffix,
                    error=str(e),
                )
                state.save()
                return []

    # Process sequentially to respect budget checks
    # (parallel within semaphore would race on budget)
    for article in pending:
        if state.budget_exceeded(max_budget):
            logger.warning(
                "Budget exceeded ($%.2f > $%.2f). Stopping.",
                state.total_cost, max_budget,
            )
            break

        art_results = await _process_one(article)
        results.extend(art_results)

    logger.info(
        "Bootstrap %s complete: %s",
        law, json.dumps(state.summary()),
    )
    return results
```

Update the `main()` function's bootstrap branch to use the new resumable version:

```python
    elif args.command == "bootstrap":
        from scripts.schema import LAWS

        state_path = Path(args.state_file)
        if state_path.exists():
            state = BootstrapState.load(state_path)
            logger.info(
                "Resuming bootstrap from %s: %s",
                state_path, json.dumps(state.summary()),
            )
        else:
            state = BootstrapState(state_path)

        laws = [args.law] if args.law else list(LAWS)
        for law in laws:
            if state.budget_exceeded(args.max_budget):
                logger.warning("Budget exceeded. Stopping.")
                break
            logger.info("Bootstrapping %s...", law)
            results = asyncio.run(
                bootstrap_law_resumable(
                    config, law, state,
                    max_concurrent=args.max_concurrent,
                    max_budget=args.max_budget,
                )
            )
            passed = sum(1 for r in results if r.success)
            logger.info(
                "%s: %d/%d layers passed",
                law, passed, len(results),
            )

        print(json.dumps(state.summary(), indent=2))
```

Add CLI arguments to the bootstrap subparser:

```python
    boot_parser.add_argument(
        "--state-file", default="bootstrap_state.json",
        help="Path to bootstrap state file for resumability",
    )
    boot_parser.add_argument(
        "--max-concurrent", type=int, default=3,
        help="Max articles to process in parallel",
    )
    boot_parser.add_argument(
        "--max-budget", type=float, default=1000.0,
        help="Max USD budget before stopping",
    )
```

Also update the import at the top of `tests/test_pipeline.py`:

```python
from agents.pipeline import (
    bootstrap_article,
    bootstrap_law_resumable,
    daily_pipeline,
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_pipeline.py -v`
Expected: 5 passed (3 existing + 2 new)

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add agents/pipeline.py tests/test_pipeline.py
git commit -m "feat: add resumable bootstrap with concurrency control and cost budget"
```

---

### Task 3: Fetch article lists and scaffold content directories

**Files:**
- Runtime output: `scripts/article_lists.json`
- Runtime output: `content/{law}/art-{NNN}/` directories

This task runs existing scripts against the live opencaselaw MCP server. No new code — just executing.

- [ ] **Step 1: Fetch article lists from opencaselaw**

```bash
uv run python scripts/fetch_articles.py
```

Expected: Creates `scripts/article_lists.json` with ~4,050 articles across 8 laws.

Verify:
```bash
cat scripts/article_lists.json | python3 -c "import json,sys; d=json.load(sys.stdin); print(sum(v['article_count'] for v in d.values()), 'articles')"
```

- [ ] **Step 2: Scaffold all content directories**

```bash
uv run python scripts/scaffold_content.py
```

Expected: Creates `content/{law}/art-{NNN}/` directories with `meta.yaml`, `summary.md`, `doctrine.md`, `caselaw.md` for each article.

Verify:
```bash
find content -name "meta.yaml" | wc -l
```
Should match article count from step 1.

- [ ] **Step 3: Validate the scaffolded content**

```bash
uv run python scripts/validate_content.py
```

Expected: All articles pass validation (meta.yaml exists, required layer files exist).

- [ ] **Step 4: Commit the article lists (but NOT the content directory — it's too large for git)**

```bash
git add scripts/article_lists.json
git commit -m "data: add cached article lists from opencaselaw ($(cat scripts/article_lists.json | python3 -c 'import json,sys; d=json.load(sys.stdin); print(sum(v["article_count"] for v in d.values()))') articles)"
```

- [ ] **Step 5: Add content/ to .gitignore (content will be managed by the pipeline, not committed to repo)**

Check if `content/` should be in `.gitignore` or committed. Given ~4,050 articles × 4 files = ~16,000 files, plus generated content that changes daily, content should be generated at deployment time, not committed.

If not already ignored:
```bash
echo "content/*" >> .gitignore
echo "!content/.gitkeep" >> .gitignore
git add .gitignore
git commit -m "chore: ignore generated content directory"
```

- [ ] **Step 6: Commit**

```bash
git add bootstrap_state.json 2>/dev/null || true
git commit -m "chore: scaffold complete — ready for bootstrap run" --allow-empty
```

---

### Task 4: Update CLAUDE.md with bootstrap commands

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Add bootstrap commands to CLAUDE.md**

Add to the Commands section:

```markdown
- `uv run python -m agents.pipeline bootstrap --law OR` — bootstrap one law
- `uv run python -m agents.pipeline bootstrap --max-budget 50` — bootstrap with budget limit
- `uv run python -m agents.pipeline bootstrap --state-file state.json` — resume bootstrap from state
```

- [ ] **Step 2: Lint and test**

```bash
uv run ruff check . --fix
uv run pytest -v
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add bootstrap CLI commands to CLAUDE.md"
```
