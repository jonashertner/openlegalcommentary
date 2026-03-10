# Agent Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete agent pipeline — law agents that generate commentary, an evaluator that enforces quality, a translator for FR/IT, and a coordinator that orchestrates the daily pipeline.

**Architecture:** Each agent is a Claude API call via the Claude Agent SDK `query()` function, configured with custom MCP tools (content I/O + opencaselaw wrappers) and system prompts built from the authoring guidelines. The coordinator is pure Python orchestration — it finds new decisions, maps them to articles, dispatches law agents in parallel, runs evaluation, and triggers translation. A retry loop (max 3 attempts) ensures quality: generate → evaluate → retry with feedback.

**Tech Stack:** Claude Agent SDK (Python), httpx, asyncio/anyio, pydantic

**Spec:** `docs/superpowers/specs/2026-03-10-openlegalcommentary-design.md` §Agent Architecture

---

## File Structure

```
agents/
  __init__.py             (exists, update with public API)
  config.py               — AgentConfig dataclass: models, thresholds, paths
  prompts.py              — build system prompts from guidelines/ files
  mcp_client.py           — shared _mcp_call() HTTP helper (used by tools + coordinator)
  tools/
    __init__.py            (exists)
    content.py             — @tool functions for content/ file I/O
    opencaselaw.py         — @tool functions wrapping opencaselaw MCP HTTP API
  law_agent.py             — generate_layer(): run law agent for one article layer
  evaluator.py             — evaluate_layer(): quality gate, returns EvalResult
  translator.py            — translate_layer(): DE→FR/IT for one layer
  generation.py            — generate_and_evaluate(): retry loop + translate
  coordinator.py           — find_new_decisions(), map_decisions_to_articles(), parallel dispatch
  pipeline.py              — CLI entry point: daily, bootstrap, single-article
tests/
  test_content_tools.py
  test_opencaselaw_tools.py
  test_prompts.py
  test_law_agent.py
  test_evaluator.py
  test_translator.py
  test_generation.py
  test_coordinator.py
  test_pipeline.py
```

---

## Chunk 1: Foundation

### Task 1: Dependencies + agents/config.py

**Files:**
- Modify: `pyproject.toml`
- Create: `agents/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
from agents.config import AgentConfig


def test_default_config():
    config = AgentConfig()
    assert config.content_root.name == "content"
    assert config.guidelines_root.name == "guidelines"
    assert config.mcp_base_url == "https://mcp.opencaselaw.ch"
    assert config.max_retries == 3


def test_model_for_layer():
    config = AgentConfig()
    assert config.model_for_layer("doctrine") == "opus"
    assert config.model_for_layer("caselaw") == "sonnet"
    assert config.model_for_layer("summary") == "sonnet"


def test_thresholds():
    config = AgentConfig()
    assert config.threshold_precision == 0.95
    assert config.threshold_academic_rigor == 0.95
    assert config.threshold_concision == 0.90


def test_custom_config():
    config = AgentConfig(max_retries=5, model_doctrine="sonnet")
    assert config.max_retries == 5
    assert config.model_for_layer("doctrine") == "sonnet"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'agents.config'`

- [ ] **Step 3: Add claude-agent-sdk dependency**

In `pyproject.toml`, add `"claude-agent-sdk>=0.1"` to `dependencies`:

```toml
dependencies = [
    "pydantic>=2.0",
    "httpx>=0.27",
    "pyyaml>=6.0",
    "claude-agent-sdk>=0.1",
]
```

Run: `uv sync` to install.

- [ ] **Step 4: Write agents/config.py**

```python
"""Agent pipeline configuration."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AgentConfig:
    """Configuration for the agent pipeline."""

    content_root: Path = field(default_factory=lambda: Path("content"))
    guidelines_root: Path = field(default_factory=lambda: Path("guidelines"))
    mcp_base_url: str = "https://mcp.opencaselaw.ch"

    # Model selection per role (spec: Opus for doctrine+eval, Sonnet for caselaw+translation)
    model_doctrine: str = "opus"
    model_caselaw: str = "sonnet"
    model_summary: str = "sonnet"
    model_evaluator: str = "opus"
    model_translator: str = "sonnet"

    # Quality thresholds (from guidelines/evaluate.md)
    threshold_precision: float = 0.95
    threshold_concision: float = 0.90
    threshold_accessibility: float = 0.90
    threshold_relevance: float = 0.90
    threshold_academic_rigor: float = 0.95

    # Agent execution limits
    max_retries: int = 3
    max_turns_per_agent: int = 25
    max_budget_per_layer: float = 0.50

    def model_for_layer(self, layer_type: str) -> str:
        """Return the model name for a given layer type."""
        models = {
            "summary": self.model_summary,
            "doctrine": self.model_doctrine,
            "caselaw": self.model_caselaw,
        }
        if layer_type not in models:
            raise ValueError(f"Unknown layer type: {layer_type}")
        return models[layer_type]
```

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml agents/config.py tests/test_config.py
git commit -m "feat: add agent config with model selection and quality thresholds"
```

---

### Task 2: Content tools

**Files:**
- Create: `agents/tools/content.py`
- Create: `tests/test_content_tools.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_content_tools.py
"""Tests for content read/write tools."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from agents.tools.content import create_content_tools


@pytest.fixture
def content_root(tmp_path):
    art_dir = tmp_path / "or" / "art-041"
    art_dir.mkdir(parents=True)
    (art_dir / "meta.yaml").write_text(
        "law: OR\narticle: 41\ntitle: Test\n"
        "sr_number: '220'\nabsatz_count: 1\n"
        "fedlex_url: https://example.com\nlayers: {}\n"
    )
    (art_dir / "summary.md").write_text("# Uebersicht\n\nTest summary.")
    return tmp_path


def test_read_article_meta(content_root):
    tools = create_content_tools(content_root)
    result = asyncio.run(
        tools["read_article_meta"](
            {"law": "OR", "article_number": 41, "article_suffix": ""}
        )
    )
    assert "law: OR" in result["content"][0]["text"]


def test_read_layer_content(content_root):
    tools = create_content_tools(content_root)
    result = asyncio.run(
        tools["read_layer_content"](
            {"law": "OR", "article_number": 41, "article_suffix": "", "layer": "summary"}
        )
    )
    assert "Test summary" in result["content"][0]["text"]


def test_write_layer_content(content_root):
    tools = create_content_tools(content_root)
    new_content = "# Doktrin\n\n**N. 1** Test doctrine."
    asyncio.run(
        tools["write_layer_content"](
            {
                "law": "OR", "article_number": 41, "article_suffix": "",
                "layer": "doctrine", "content": new_content,
            }
        )
    )
    written = (content_root / "or" / "art-041" / "doctrine.md").read_text()
    assert written == new_content


def test_read_missing_meta(content_root):
    tools = create_content_tools(content_root)
    result = asyncio.run(
        tools["read_article_meta"](
            {"law": "OR", "article_number": 999, "article_suffix": ""}
        )
    )
    assert result.get("is_error") is True


def test_create_content_server(content_root):
    from agents.tools.content import create_content_server
    server = create_content_server(content_root)
    assert server is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_content_tools.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write agents/tools/content.py**

```python
"""Content read/write tools for the agent pipeline.

Tools are created via factory functions that capture the content_root path
via closure, ensuring agents can only access the content/ directory.
"""
from __future__ import annotations

from pathlib import Path

from claude_agent_sdk import create_sdk_mcp_server, tool

from scripts.fetch_articles import article_dir_name


def _article_path(content_root: Path, law: str, number: int, suffix: str) -> Path:
    dir_name = article_dir_name(number, suffix)
    return content_root / law.lower() / dir_name


def create_content_tools(content_root: Path) -> dict:
    """Create content tool functions bound to a content root.

    Returns a dict of tool_name -> async callable for direct testing.
    Use create_content_server() for SDK integration.
    """

    async def read_article_meta(args):
        path = _article_path(
            content_root, args["law"], args["article_number"],
            args.get("article_suffix", ""),
        )
        meta_path = path / "meta.yaml"
        if not meta_path.exists():
            return {
                "content": [{"type": "text", "text": f"meta.yaml not found at {path}"}],
                "is_error": True,
            }
        return {"content": [{"type": "text", "text": meta_path.read_text()}]}

    async def read_layer_content(args):
        path = _article_path(
            content_root, args["law"], args["article_number"],
            args.get("article_suffix", ""),
        )
        layer_file = path / f"{args['layer']}.md"
        if not layer_file.exists():
            return {
                "content": [{"type": "text", "text": f"{args['layer']}.md not found"}],
                "is_error": True,
            }
        return {"content": [{"type": "text", "text": layer_file.read_text()}]}

    async def write_layer_content(args):
        path = _article_path(
            content_root, args["law"], args["article_number"],
            args.get("article_suffix", ""),
        )
        path.mkdir(parents=True, exist_ok=True)
        layer_file = path / f"{args['layer']}.md"
        layer_file.write_text(args["content"])
        return {
            "content": [
                {"type": "text", "text": f"Written {len(args['content'])} chars to {layer_file}"}
            ],
        }

    return {
        "read_article_meta": read_article_meta,
        "read_layer_content": read_layer_content,
        "write_layer_content": write_layer_content,
    }


def create_content_server(content_root: Path):
    """Create an SDK MCP server with content tools."""
    tools_dict = create_content_tools(content_root)

    read_meta = tool(
        "read_article_meta",
        "Read meta.yaml for a commentary article",
        {"law": str, "article_number": int, "article_suffix": str},
    )(tools_dict["read_article_meta"])

    read_layer = tool(
        "read_layer_content",
        "Read a commentary layer markdown file (summary, doctrine, or caselaw)",
        {"law": str, "article_number": int, "article_suffix": str, "layer": str},
    )(tools_dict["read_layer_content"])

    write_layer = tool(
        "write_layer_content",
        "Write commentary content to a layer markdown file",
        {
            "law": str, "article_number": int, "article_suffix": str,
            "layer": str, "content": str,
        },
    )(tools_dict["write_layer_content"])

    return create_sdk_mcp_server(
        name="content",
        version="1.0.0",
        tools=[read_meta, read_layer, write_layer],
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_content_tools.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add agents/tools/content.py tests/test_content_tools.py
git commit -m "feat: add content read/write tools for agent pipeline"
```

---

### Task 3: Shared MCP client

**Files:**
- Create: `agents/mcp_client.py`
- Modify: `scripts/fetch_articles.py` (import from shared client)
- Create: `tests/test_mcp_client.py`

This extracts the `_mcp_call` function from `scripts/fetch_articles.py` into a shared module so both the existing fetch scripts and the new agent tools use the same HTTP client.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_mcp_client.py
"""Tests for the shared MCP HTTP client."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from agents.mcp_client import mcp_call


def _mock_response(text: str):
    resp = AsyncMock()
    resp.json.return_value = {
        "result": {"content": [{"type": "text", "text": text}]}
    }
    resp.raise_for_status = lambda: None
    return resp


def test_mcp_call_returns_text():
    with patch("agents.mcp_client.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_client.return_value
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.post = AsyncMock(
            return_value=_mock_response("Art. 41 OR text")
        )

        result = asyncio.run(
            mcp_call("https://mcp.test", "get_law", {"abbreviation": "OR"})
        )
        assert "Art. 41" in result


def test_mcp_call_raises_on_error():
    resp = AsyncMock()
    resp.json.return_value = {"error": {"code": -1, "message": "Not found"}}
    resp.raise_for_status = lambda: None

    with patch("agents.mcp_client.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_client.return_value
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.post = AsyncMock(return_value=resp)

        with pytest.raises(RuntimeError, match="MCP error"):
            asyncio.run(
                mcp_call("https://mcp.test", "get_law", {"abbreviation": "OR"})
            )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_mcp_client.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write agents/mcp_client.py**

```python
"""Shared MCP HTTP client for calling the opencaselaw MCP server.

Used by both scripts/fetch_articles.py and agents/tools/opencaselaw.py
to avoid duplication of the JSON-RPC HTTP transport layer.
"""
from __future__ import annotations

import httpx


async def mcp_call(
    mcp_base: str, tool_name: str, args: dict, timeout: float = 120.0,
) -> str:
    """Call an opencaselaw MCP tool via JSON-RPC over HTTP.

    Args:
        mcp_base: Base URL of the MCP server (e.g., "https://mcp.opencaselaw.ch").
        tool_name: MCP tool name (e.g., "get_law", "search_decisions").
        args: Tool arguments dict.
        timeout: HTTP timeout in seconds.

    Returns:
        Concatenated text content from the MCP response.

    Raises:
        RuntimeError: If the MCP server returns an error.
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            f"{mcp_base}/mcp",
            json={
                "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"name": tool_name, "arguments": args},
            },
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        result = response.json()
        if "error" in result:
            raise RuntimeError(f"MCP error: {result['error']}")
        content = result.get("result", {}).get("content", [])
        return "\n".join(c["text"] for c in content if c.get("type") == "text")
```

- [ ] **Step 4: Update scripts/fetch_articles.py to use shared client**

Replace the `_mcp_call` function in `scripts/fetch_articles.py` with an import:

```python
# In scripts/fetch_articles.py, replace the _mcp_call function with:
from agents.mcp_client import mcp_call

MCP_BASE = "https://mcp.opencaselaw.ch"

# Update all callers: _mcp_call(client, ...) → mcp_call(MCP_BASE, ...)
# The shared client creates its own httpx.AsyncClient internally.
```

Update `fetch_articles()` and `fetch_legislation_metadata()` to use `mcp_call(MCP_BASE, ...)` instead of `_mcp_call(client, ...)`.

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_mcp_client.py tests/test_fetch_articles.py -v`
Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add agents/mcp_client.py scripts/fetch_articles.py tests/test_mcp_client.py
git commit -m "refactor: extract shared MCP HTTP client from fetch_articles"
```

---

### Task 4: opencaselaw tools

**Files:**
- Create: `agents/tools/opencaselaw.py`
- Create: `tests/test_opencaselaw_tools.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_opencaselaw_tools.py
"""Tests for opencaselaw MCP wrapper tools."""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from agents.tools.opencaselaw import create_opencaselaw_tools


def _mock_mcp_response(text: str) -> dict:
    return {
        "result": {
            "content": [{"type": "text", "text": text}]
        }
    }


@pytest.fixture
def tools():
    return create_opencaselaw_tools("https://mcp.test.example")


def test_get_article_text(tools):
    mock_resp = AsyncMock()
    mock_resp.json.return_value = _mock_mcp_response("Art. 41\n1 Wer einem andern...")
    mock_resp.raise_for_status = lambda: None

    with patch("agents.mcp_client.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.post = AsyncMock(return_value=mock_resp)

        result = asyncio.run(tools["get_article_text"]({"law_abbreviation": "OR"}))
        assert "Art. 41" in result["content"][0]["text"]


def test_search_decisions(tools):
    mock_resp = AsyncMock()
    mock_resp.json.return_value = _mock_mcp_response("1. BGE 130 III 182\n2. BGE 133 III 323")
    mock_resp.raise_for_status = lambda: None

    with patch("agents.mcp_client.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.post = AsyncMock(return_value=mock_resp)

        result = asyncio.run(
            tools["search_decisions"]({"query": "Art. 41 OR Haftung", "law_abbreviation": "OR"})
        )
        assert "BGE 130 III 182" in result["content"][0]["text"]


def test_find_leading_cases(tools):
    mock_resp = AsyncMock()
    mock_resp.json.return_value = _mock_mcp_response("Leading: BGE 130 III 182")
    mock_resp.raise_for_status = lambda: None

    with patch("agents.mcp_client.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.post = AsyncMock(return_value=mock_resp)

        result = asyncio.run(
            tools["find_leading_cases"]({"article": "Art. 41", "law_abbreviation": "OR"})
        )
        assert "Leading" in result["content"][0]["text"]


def test_get_decision(tools):
    mock_resp = AsyncMock()
    mock_resp.json.return_value = _mock_mcp_response("BGE 130 III 182: Haftung...")
    mock_resp.raise_for_status = lambda: None

    with patch("agents.mcp_client.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.post = AsyncMock(return_value=mock_resp)

        result = asyncio.run(tools["get_decision"]({"decision_id": "130-III-182"}))
        assert "Haftung" in result["content"][0]["text"]


def test_get_case_brief(tools):
    mock_resp = AsyncMock()
    mock_resp.json.return_value = _mock_mcp_response("Brief: Haftungsrecht...")
    mock_resp.raise_for_status = lambda: None

    with patch("agents.mcp_client.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.post = AsyncMock(return_value=mock_resp)

        result = asyncio.run(tools["get_case_brief"]({"decision_id": "130-III-182"}))
        assert "Brief" in result["content"][0]["text"]


def test_mcp_error_handling(tools):
    mock_resp = AsyncMock()
    mock_resp.json.return_value = {"error": {"code": -1, "message": "Tool not found"}}
    mock_resp.raise_for_status = lambda: None

    with patch("agents.mcp_client.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client.return_value)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value.post = AsyncMock(return_value=mock_resp)

        result = asyncio.run(tools["get_article_text"]({"law_abbreviation": "OR"}))
        assert result.get("is_error") is True


def test_create_opencaselaw_server():
    from agents.tools.opencaselaw import create_opencaselaw_server
    server = create_opencaselaw_server("https://mcp.test.example")
    assert server is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_opencaselaw_tools.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write agents/tools/opencaselaw.py**

```python
"""opencaselaw MCP wrapper tools for the agent pipeline.

Wraps HTTP calls to the opencaselaw MCP server, providing tools for:
- Fetching article text from LexFind/Fedlex
- Searching court decisions
- Finding leading cases (BGE)
- Getting full decision details and case briefs
"""
from __future__ import annotations

from claude_agent_sdk import create_sdk_mcp_server, tool

from agents.mcp_client import mcp_call


def create_opencaselaw_tools(mcp_base: str) -> dict:
    """Create opencaselaw tool functions bound to an MCP base URL.

    Returns a dict of tool_name -> async callable for direct testing.
    Use create_opencaselaw_server() for SDK integration.
    """

    async def get_article_text(args):
        try:
            text = await mcp_call(mcp_base, "get_law", {
        response = await client.post(
            f"{mcp_base}/mcp",
            json={
                "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                "params": {"name": tool_name, "arguments": args},
            },
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        result = response.json()
        if "error" in result:
            raise RuntimeError(f"MCP error: {result['error']}")
        content = result.get("result", {}).get("content", [])
        return "\n".join(c["text"] for c in content if c.get("type") == "text")


def create_opencaselaw_tools(mcp_base: str) -> dict:
    """Create opencaselaw tool functions bound to an MCP base URL.

    Returns a dict of tool_name -> async callable for direct testing.
    Use create_opencaselaw_server() for SDK integration.
    """

    async def get_article_text(args):
        try:
            text = await mcp_call(mcp_base, "get_law", {
                "abbreviation": args["law_abbreviation"],
            })
            return {"content": [{"type": "text", "text": text}]}
        except RuntimeError as e:
            return {"content": [{"type": "text", "text": str(e)}], "is_error": True}

    async def search_decisions(args):
        try:
            params = {"query": args["query"]}
            if args.get("law_abbreviation"):
                params["law_abbreviation"] = args["law_abbreviation"]
            text = await mcp_call(mcp_base, "search_decisions", params)
            return {"content": [{"type": "text", "text": text}]}
        except RuntimeError as e:
            return {"content": [{"type": "text", "text": str(e)}], "is_error": True}

    async def find_leading_cases(args):
        try:
            text = await mcp_call(mcp_base, "find_leading_cases", {
                "article": args["article"],
                "law_abbreviation": args["law_abbreviation"],
            })
            return {"content": [{"type": "text", "text": text}]}
        except RuntimeError as e:
            return {"content": [{"type": "text", "text": str(e)}], "is_error": True}

    async def get_decision(args):
        try:
            text = await mcp_call(mcp_base, "get_decision", {
                "decision_id": args["decision_id"],
            })
            return {"content": [{"type": "text", "text": text}]}
        except RuntimeError as e:
            return {"content": [{"type": "text", "text": str(e)}], "is_error": True}

    async def get_case_brief(args):
        try:
            text = await mcp_call(mcp_base, "get_case_brief", {
                "decision_id": args["decision_id"],
            })
            return {"content": [{"type": "text", "text": text}]}
        except RuntimeError as e:
            return {"content": [{"type": "text", "text": str(e)}], "is_error": True}

    return {
        "get_article_text": get_article_text,
        "search_decisions": search_decisions,
        "find_leading_cases": find_leading_cases,
        "get_decision": get_decision,
        "get_case_brief": get_case_brief,
    }


def create_opencaselaw_server(mcp_base: str):
    """Create an SDK MCP server with opencaselaw tools."""
    tools_dict = create_opencaselaw_tools(mcp_base)

    t_article = tool(
        "get_article_text",
        "Get the full text of a law from LexFind/Fedlex. Returns all articles.",
        {"law_abbreviation": str},
    )(tools_dict["get_article_text"])

    t_search = tool(
        "search_decisions",
        "Search court decisions by query. Returns matching decisions with references.",
        {"query": str, "law_abbreviation": str},
    )(tools_dict["search_decisions"])

    t_leading = tool(
        "find_leading_cases",
        "Find leading cases (BGE) for a specific article. Returns Leitentscheide.",
        {"article": str, "law_abbreviation": str},
    )(tools_dict["find_leading_cases"])

    t_decision = tool(
        "get_decision",
        "Get the full text and details of a specific court decision.",
        {"decision_id": str},
    )(tools_dict["get_decision"])

    t_brief = tool(
        "get_case_brief",
        "Get a structured brief/summary of a court decision with key holdings.",
        {"decision_id": str},
    )(tools_dict["get_case_brief"])

    return create_sdk_mcp_server(
        name="opencaselaw",
        version="1.0.0",
        tools=[t_article, t_search, t_leading, t_decision, t_brief],
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_opencaselaw_tools.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add agents/tools/opencaselaw.py tests/test_opencaselaw_tools.py
git commit -m "feat: add opencaselaw MCP wrapper tools for agent pipeline"
```

---

## Chunk 2: Agent Core

### Task 5: Prompt builder

**Files:**
- Create: `agents/prompts.py`
- Create: `tests/test_prompts.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_prompts.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_prompts.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write agents/prompts.py**

```python
"""System prompt builder for the agent pipeline.

Reads guidelines from guidelines/ and constructs role-specific system prompts
for law agents, the evaluator, and the translator.
"""
from __future__ import annotations

from pathlib import Path

LAYER_INSTRUCTIONS = {
    "summary": """Generate the **Übersicht (Summary)** layer for the given article.

Requirements (from global.md §II.1):
- Language: German B1 level — a motivated Gymnasium graduate must understand it fully
- Length: 150–300 words
- Must answer: What does the article regulate? Who is affected? What are the legal consequences?
- Include at least one concrete example
- Maximum sentence length: 25 words
- No citations, no Randziffern (marginal numbers)
- Technical terms explained in parentheses on first use

Use the tools to:
1. Read the article text via get_article_text
2. Read the existing doctrine and caselaw layers if available (for context)
3. Write the summary layer using write_layer_content""",

    "doctrine": """Generate the **Doktrin (Doctrinal Analysis)** layer for the given article.

Requirements (from global.md §II.2):
- Use numbered marginal notes: **N. 1**, **N. 2**, etc.
- Required sections:
  1. Entstehungsgeschichte (legislative history — cite the Botschaft)
  2. Systematische Einordnung (systematic context within the law)
  3. Tatbestandsmerkmale / Norminhalt (elements / content of the provision)
  4. Rechtsfolgen (legal consequences)
  5. Streitstände (doctrinal debates — name specific authors and their positions)
  6. Praxishinweise (practical guidance)
- Minimum 3 secondary sources from different authors
- The Botschaft (legislative message) must be cited
- Cross-references use arrow notation: → (unidirectional), ↔ (bidirectional)

Use the tools to:
1. Read the article text via get_article_text
2. Search for leading cases via find_leading_cases
3. Read the existing caselaw layer for context
4. Write the doctrine layer using write_layer_content""",

    "caselaw": """Generate the **Rechtsprechung (Case Law Digest)** layer for the given article.

Requirements (from global.md §II.3):
- Group decisions by topic, within each topic order by importance (leading cases first), then chronologically
- For each decision include:
  - BGE reference in **bold** (e.g., **BGE 130 III 182 E. 5.5.1**)
  - Date
  - Core holding in 1–2 sentences (Regeste-style)
  - Relevance to this article in 1 sentence
  - Block quote of the decisive passage using Guillemets (« »)
- ALL leading cases (BGE) available on opencaselaw for this article MUST appear
- Decisions from the last 12 months must be included if relevant

Use the tools to:
1. Read the article text via get_article_text
2. Find ALL leading cases via find_leading_cases
3. Search for additional relevant decisions via search_decisions
4. Get case briefs for each relevant decision via get_case_brief
5. For key decisions, get full text via get_decision
6. Write the caselaw layer using write_layer_content""",
}


def build_law_agent_prompt(
    guidelines_root: Path, law: str, layer_type: str,
) -> str:
    """Build the system prompt for a law agent generating a specific layer."""
    if layer_type not in LAYER_INSTRUCTIONS:
        raise ValueError(f"Unknown layer type: {layer_type}. Must be summary, doctrine, or caselaw")

    global_md = (guidelines_root / "global.md").read_text()
    law_md = (guidelines_root / f"{law.lower()}.md").read_text()

    return f"""You are an expert legal commentator for openlegalcommentary.ch — an open-access, \
AI-generated legal commentary on Swiss federal law.

Your work must meet the highest standards of academic excellence, precision, concision, \
relevance, accessibility, and professionalism. Every statement must be traceable to a \
primary source. You write in German.

## Global Authoring Guidelines

{global_md}

## Law-Specific Guidelines ({law})

{law_md}

## Your Task

{LAYER_INSTRUCTIONS[layer_type]}

## Citation Format

- BGE: **BGE 130 III 182 E. 5.5.1**
- BGer (unpublished): Urteil 4A_123/2024 vom 15.3.2024 E. 3.2
- Literature: Gauch/Schluep/Schmid, OR AT, 11. Aufl. 2020, N 2850
- Botschaft: BBl 2001 4202

## Important

- Write in German
- Be precise — no synonyms for legal terms
- Be concise — every sentence must earn its place
- Use the tools provided to research thoroughly before writing
- Write the result using the write_layer_content tool"""


def build_evaluator_prompt(guidelines_root: Path) -> str:
    """Build the system prompt for the evaluator agent."""
    evaluate_md = (guidelines_root / "evaluate.md").read_text()

    return f"""You are the quality evaluator for openlegalcommentary.ch. Your role is to \
assess whether generated commentary meets the publication threshold.

You evaluate rigorously and objectively. You do not generate commentary — you only judge it.

## Evaluation Rubric

{evaluate_md}

## Your Task

1. Read the generated layer content using read_layer_content
2. Read the article text using get_article_text to verify legal terminology
3. For caselaw layers: use find_leading_cases to verify completeness
4. Evaluate against all non-negotiable criteria (binary pass/fail)
5. Score all five dimensions (0.0–1.0)
6. Return your verdict as JSON in EXACTLY this format:

```json
{{
  "verdict": "publish" or "reject",
  "non_negotiables": {{
    "keine_unbelegten_rechtsaussagen": true/false,
    "keine_faktischen_fehler": true/false,
    "keine_fehlenden_leitentscheide": true/false,
    "korrekte_legalbegriffe": true/false,
    "strukturelle_vollstaendigkeit": true/false
  }},
  "scores": {{
    "praezision": 0.00,
    "konzision": 0.00,
    "zugaenglichkeit": 0.00,
    "relevanz": 0.00,
    "akademische_strenge": 0.00
  }},
  "feedback": {{
    "blocking_issues": ["..."],
    "improvement_suggestions": ["..."]
  }}
}}
```

A "publish" verdict requires ALL non-negotiables to be true AND all scores to meet thresholds \
(precision ≥ 0.95, concision ≥ 0.90, accessibility ≥ 0.90, relevance ≥ 0.90, academic rigor ≥ 0.95)."""


def build_translator_prompt(guidelines_root: Path, target_lang: str) -> str:
    """Build the system prompt for the translator agent."""
    lang_config = {
        "fr": ("French", "français"),
        "it": ("Italian", "italiano"),
    }
    if target_lang not in lang_config:
        raise ValueError(f"Unknown target language: {target_lang}. Must be 'fr' or 'it'")

    lang_name, _ = lang_config[target_lang]

    return f"""You are a legal translator for openlegalcommentary.ch, translating Swiss legal \
commentary from German to {lang_name}.

## Translation Guidelines (from global.md §III)

- The German version is authoritative
- Legal terminology must use official translations from Fedlex termdat
- Maintain the same structure, formatting, and Randziffern numbering
- BGE references remain in their original form (do not translate case references)
- Cross-references (→, ↔) remain unchanged
- Guillemet quotes (« ») are preserved

## Your Task

1. Read the German source layer using read_layer_content
2. Translate the content to {lang_name}
3. Write the translation using write_layer_content with the appropriate layer name \
(e.g., "summary.{target_lang}" for the summary layer)

## Important

- Preserve all formatting exactly (headings, bold, Randziffern, block quotes)
- Use official Swiss {lang_name} legal terminology
- Do not add, remove, or modify any substantive content — translate only"""
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_prompts.py -v`
Expected: 9 passed

- [ ] **Step 5: Commit**

```bash
git add agents/prompts.py tests/test_prompts.py
git commit -m "feat: add system prompt builder for law, evaluator, and translator agents"
```

---

### Task 6: Law agent

**Files:**
- Create: `agents/law_agent.py`
- Create: `tests/test_law_agent.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_law_agent.py
"""Tests for the law agent."""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.config import AgentConfig
from agents.law_agent import generate_layer


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
    (art_dir / "summary.md").write_text("# Uebersicht\n\nPlaceholder.")
    (art_dir / "doctrine.md").write_text("# Doktrin\n\nPlaceholder.")
    (art_dir / "caselaw.md").write_text("# Rechtsprechung\n\nPlaceholder.")
    return AgentConfig(content_root=content_root)


def _mock_query_messages():
    """Return a mock async generator that yields a ResultMessage."""
    from claude_agent_sdk import ResultMessage
    msg = MagicMock(spec=ResultMessage)
    msg.total_cost_usd = 0.05

    async def gen(*args, **kwargs):
        yield msg

    return gen


def test_generate_layer_calls_query(config):
    with patch("agents.law_agent.query") as mock_query:
        mock_query.side_effect = _mock_query_messages()

        cost = asyncio.run(
            generate_layer(config, "OR", 41, "", "summary")
        )
        mock_query.assert_called_once()
        call_kwargs = mock_query.call_args
        assert "prompt" in call_kwargs.kwargs or len(call_kwargs.args) > 0


def test_generate_layer_uses_correct_model(config):
    with patch("agents.law_agent.query") as mock_query:
        mock_query.side_effect = _mock_query_messages()

        asyncio.run(generate_layer(config, "OR", 41, "", "doctrine"))
        options = mock_query.call_args.kwargs.get("options")
        assert options is not None
        assert options.model == "opus"


def test_generate_layer_with_feedback(config):
    with patch("agents.law_agent.query") as mock_query:
        mock_query.side_effect = _mock_query_messages()

        asyncio.run(
            generate_layer(config, "OR", 41, "", "summary", feedback="Missing example")
        )
        prompt = mock_query.call_args.kwargs.get("prompt", mock_query.call_args.args[0])
        assert "Missing example" in prompt


def test_generate_layer_returns_cost(config):
    with patch("agents.law_agent.query") as mock_query:
        mock_query.side_effect = _mock_query_messages()

        cost = asyncio.run(generate_layer(config, "OR", 41, "", "summary"))
        assert cost == pytest.approx(0.05)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_law_agent.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write agents/law_agent.py**

```python
"""Law agent — generates commentary layers for individual articles.

Each call runs a Claude agent with:
- System prompt built from global + per-law guidelines
- Content tools for reading/writing article files
- opencaselaw tools for fetching article text and case law
"""
from __future__ import annotations

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from agents.config import AgentConfig
from agents.prompts import build_law_agent_prompt
from agents.tools.content import create_content_server
from agents.tools.opencaselaw import create_opencaselaw_server


async def generate_layer(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_type: str,
    feedback: str | None = None,
) -> float:
    """Run the law agent to generate a commentary layer.

    The agent reads the article text and case law via tools, then writes
    the layer content directly to the content/ directory.

    Args:
        config: Pipeline configuration.
        law: Law abbreviation (e.g., "OR").
        article_number: Article number (e.g., 41).
        article_suffix: Article suffix (e.g., "a" for Art. 6a).
        layer_type: One of "summary", "doctrine", "caselaw".
        feedback: Optional feedback from a previous failed evaluation.

    Returns:
        Cost in USD for this generation.
    """
    system_prompt = build_law_agent_prompt(config.guidelines_root, law, layer_type)

    content_server = create_content_server(config.content_root)
    opencaselaw_server = create_opencaselaw_server(config.mcp_base_url)

    suffix_str = article_suffix or ""
    prompt = (
        f"Generate the {layer_type} layer for Art. {article_number}{suffix_str} {law}. "
        f"The article directory is at {law.lower()}/art-{str(article_number).zfill(3)}{suffix_str}/. "
        f"Use the tools to research the article, then write the layer content."
    )
    if feedback:
        prompt += (
            f"\n\nYour previous attempt was rejected by the evaluator. "
            f"Fix the following issues:\n{feedback}"
        )

    options = ClaudeAgentOptions(
        mcp_servers={
            "content": content_server,
            "opencaselaw": opencaselaw_server,
        },
        allowed_tools=[
            "mcp__content__read_article_meta",
            "mcp__content__read_layer_content",
            "mcp__content__write_layer_content",
            "mcp__opencaselaw__get_article_text",
            "mcp__opencaselaw__search_decisions",
            "mcp__opencaselaw__find_leading_cases",
            "mcp__opencaselaw__get_decision",
            "mcp__opencaselaw__get_case_brief",
        ],
        system_prompt=system_prompt,
        model=config.model_for_layer(layer_type),
        max_turns=config.max_turns_per_agent,
        max_budget_usd=config.max_budget_per_layer,
        permission_mode="bypassPermissions",
    )

    cost = 0.0
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage) and message.total_cost_usd:
            cost = message.total_cost_usd

    return cost
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_law_agent.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add agents/law_agent.py tests/test_law_agent.py
git commit -m "feat: add law agent for generating commentary layers"
```

---

### Task 7: Evaluator agent

**Files:**
- Create: `agents/evaluator.py`
- Create: `tests/test_evaluator.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_evaluator.py
"""Tests for the evaluator agent."""
from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from unittest.mock import MagicMock, patch

import pytest

from agents.config import AgentConfig
from agents.evaluator import EvalResult, evaluate_layer, parse_eval_response


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
    (art_dir / "summary.md").write_text("# Uebersicht\n\nTest.")
    return AgentConfig(content_root=content_root)


def _mock_eval_query(verdict_json):
    from claude_agent_sdk import AssistantMessage, TextBlock
    msg = MagicMock(spec=AssistantMessage)
    msg.content = [MagicMock(spec=TextBlock, text=json.dumps(verdict_json))]

    async def gen(*args, **kwargs):
        yield msg
    return gen


def test_evaluate_layer_calls_query(config):
    verdict = {
        "verdict": "publish",
        "non_negotiables": {"keine_unbelegten_rechtsaussagen": True},
        "scores": {"praezision": 0.96},
        "feedback": {"blocking_issues": []},
    }
    with patch("agents.evaluator.query") as mock_query:
        mock_query.side_effect = _mock_eval_query(verdict)

        result = asyncio.run(evaluate_layer(config, "OR", 41, "", "summary"))
        assert result.verdict == "publish"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_evaluator.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write agents/evaluator.py**

```python
"""Evaluator agent — quality gate for generated commentary.

Evaluates layers against guidelines/evaluate.md criteria:
- 5 non-negotiable binary checks (any failure = reject)
- 5 scored dimensions with thresholds (all must meet minimum)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

from agents.config import AgentConfig
from agents.prompts import build_evaluator_prompt
from agents.tools.content import create_content_server
from agents.tools.opencaselaw import create_opencaselaw_server


@dataclass
class EvalResult:
    """Result of a quality evaluation."""

    verdict: str  # "publish" or "reject"
    non_negotiables: dict[str, bool] = field(default_factory=dict)
    scores: dict[str, float] = field(default_factory=dict)
    feedback: dict[str, list[str]] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.verdict == "publish"

    def feedback_text(self) -> str:
        """Format feedback as readable text for retry prompts."""
        parts = []
        issues = self.feedback.get("blocking_issues", [])
        if issues:
            parts.append("Blocking issues:\n" + "\n".join(f"- {i}" for i in issues))
        suggestions = self.feedback.get("improvement_suggestions", [])
        if suggestions:
            parts.append("Suggestions:\n" + "\n".join(f"- {s}" for s in suggestions))
        failed_nn = [k for k, v in self.non_negotiables.items() if not v]
        if failed_nn:
            parts.append("Failed non-negotiables: " + ", ".join(failed_nn))
        return "\n\n".join(parts) if parts else "No specific feedback."


def parse_eval_response(response_text: str) -> EvalResult:
    """Parse the evaluator's JSON response from text output."""
    # Try to find JSON in the response (may be wrapped in markdown code block)
    json_match = re.search(r"```json\s*([\s\S]*?)```", response_text)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        # Try to find raw JSON object
        json_match = re.search(r"\{[\s\S]*\}", response_text)
        if json_match:
            json_str = json_match.group(0)
        else:
            raise ValueError(f"No JSON found in evaluator response: {response_text[:200]}")

    data = json.loads(json_str)
    return EvalResult(
        verdict=data["verdict"],
        non_negotiables=data.get("non_negotiables", {}),
        scores=data.get("scores", {}),
        feedback=data.get("feedback", {}),
    )


async def evaluate_layer(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_type: str,
) -> EvalResult:
    """Run the evaluator agent on a generated layer.

    Returns an EvalResult with verdict, scores, and feedback.
    """
    system_prompt = build_evaluator_prompt(config.guidelines_root)

    content_server = create_content_server(config.content_root)
    opencaselaw_server = create_opencaselaw_server(config.mcp_base_url)

    suffix_str = article_suffix or ""
    prompt = (
        f"Evaluate the {layer_type} layer for Art. {article_number}{suffix_str} {law}. "
        f"Read the content, verify it against the article text and case law, "
        f"then return your JSON verdict."
    )

    options = ClaudeAgentOptions(
        mcp_servers={
            "content": content_server,
            "opencaselaw": opencaselaw_server,
        },
        allowed_tools=[
            "mcp__content__read_article_meta",
            "mcp__content__read_layer_content",
            "mcp__opencaselaw__get_article_text",
            "mcp__opencaselaw__find_leading_cases",
            "mcp__opencaselaw__search_decisions",
        ],
        system_prompt=system_prompt,
        model=config.model_evaluator,
        max_turns=config.max_turns_per_agent,
        max_budget_usd=config.max_budget_per_layer,
        permission_mode="bypassPermissions",
    )

    response_text = ""
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    response_text += block.text

    return parse_eval_response(response_text)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_evaluator.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add agents/evaluator.py tests/test_evaluator.py
git commit -m "feat: add evaluator agent with quality gate and JSON verdict parsing"
```

---

## Chunk 3: Translation & Generation Loop

### Task 8: Translator agent

**Files:**
- Create: `agents/translator.py`
- Create: `tests/test_translator.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_translator.py
"""Tests for the translator agent."""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from agents.config import AgentConfig
from agents.translator import translate_layer


@pytest.fixture
def config(tmp_path):
    content_root = tmp_path / "content"
    art_dir = content_root / "or" / "art-041"
    art_dir.mkdir(parents=True)
    (art_dir / "summary.md").write_text("# Uebersicht\n\nDeutscher Text.")
    return AgentConfig(content_root=content_root)


def _mock_query():
    from claude_agent_sdk import ResultMessage
    msg = MagicMock(spec=ResultMessage)
    msg.total_cost_usd = 0.02

    async def gen(*args, **kwargs):
        yield msg
    return gen


def test_translate_layer_calls_query(config):
    with patch("agents.translator.query") as mock_query:
        mock_query.side_effect = _mock_query()

        cost = asyncio.run(translate_layer(config, "OR", 41, "", "summary", "fr"))
        mock_query.assert_called_once()


def test_translate_layer_uses_sonnet(config):
    with patch("agents.translator.query") as mock_query:
        mock_query.side_effect = _mock_query()

        asyncio.run(translate_layer(config, "OR", 41, "", "summary", "fr"))
        options = mock_query.call_args.kwargs.get("options")
        assert options.model == "sonnet"


def test_translate_layer_prompt_includes_target(config):
    with patch("agents.translator.query") as mock_query:
        mock_query.side_effect = _mock_query()

        asyncio.run(translate_layer(config, "OR", 41, "", "summary", "it"))
        prompt = mock_query.call_args.kwargs.get("prompt", mock_query.call_args.args[0])
        assert "summary.it" in prompt or "Italian" in prompt or "it" in prompt


def test_translate_invalid_language(config):
    with pytest.raises(ValueError):
        asyncio.run(translate_layer(config, "OR", 41, "", "summary", "es"))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_translator.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write agents/translator.py**

```python
"""Translator agent — translates commentary layers from German to French/Italian.

Uses the translation guidelines from global.md §III and official Fedlex termdat
terminology for legal terms.
"""
from __future__ import annotations

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from agents.config import AgentConfig
from agents.prompts import build_translator_prompt
from agents.tools.content import create_content_server

VALID_LANGUAGES = ("fr", "it")


async def translate_layer(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_type: str,
    target_lang: str,
) -> float:
    """Translate a commentary layer from German to the target language.

    The agent reads the German source layer, translates it, and writes
    the translation (e.g., summary.fr.md) to the content directory.

    Returns cost in USD.
    """
    if target_lang not in VALID_LANGUAGES:
        raise ValueError(
            f"Unknown target language: {target_lang}. Must be one of {VALID_LANGUAGES}"
        )

    system_prompt = build_translator_prompt(config.guidelines_root, target_lang)
    content_server = create_content_server(config.content_root)

    suffix_str = article_suffix or ""
    prompt = (
        f"Translate the {layer_type} layer for Art. {article_number}{suffix_str} {law} "
        f"from German to {'French' if target_lang == 'fr' else 'Italian'}. "
        f"Read the source layer '{layer_type}' and write the translation as '{layer_type}.{target_lang}'."
    )

    options = ClaudeAgentOptions(
        mcp_servers={"content": content_server},
        allowed_tools=[
            "mcp__content__read_layer_content",
            "mcp__content__write_layer_content",
        ],
        system_prompt=system_prompt,
        model=config.model_translator,
        max_turns=10,
        max_budget_usd=0.20,
        permission_mode="bypassPermissions",
    )

    cost = 0.0
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage) and message.total_cost_usd:
            cost = message.total_cost_usd

    return cost
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_translator.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add agents/translator.py tests/test_translator.py
git commit -m "feat: add translator agent for DE->FR/IT commentary translation"
```

---

### Task 9: Generation loop (generate → evaluate → retry → translate)

**Files:**
- Create: `agents/generation.py`
- Create: `tests/test_generation.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_generation.py
"""Tests for the generation loop (generate → evaluate → retry → translate)."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
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
        (art_dir / layer).write_text(f"# Placeholder\n")
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
        patch("agents.generation.generate_layer", new_callable=AsyncMock, return_value=0.05),
        patch("agents.generation.evaluate_layer", new_callable=AsyncMock, return_value=_pass_result()),
    ):
        result = asyncio.run(
            generate_and_evaluate(config, "OR", 41, "", "summary")
        )
        assert result.success is True
        assert result.attempts == 1


def test_generate_and_evaluate_retries_on_failure(config):
    fail = _fail_result()
    with (
        patch("agents.generation.generate_layer", new_callable=AsyncMock, return_value=0.05),
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
        patch("agents.generation.generate_layer", new_callable=AsyncMock, return_value=0.05),
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
        patch("agents.generation.translate_layer", new_callable=AsyncMock, return_value=0.02),
    ):
        results = asyncio.run(
            process_article(config, "OR", 41, "", ["summary", "doctrine", "caselaw"])
        )
        assert len(results) == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_generation.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write agents/generation.py**

```python
"""Generation loop — generate, evaluate, retry, translate.

Orchestrates the per-article workflow:
1. Generate a layer with the law agent
2. Evaluate with the evaluator
3. If rejected, retry with feedback (max 3 attempts)
4. If approved, translate to FR and IT
5. Update meta.yaml with results
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

import yaml

from agents.config import AgentConfig
from agents.evaluator import EvalResult, evaluate_layer
from agents.law_agent import generate_layer
from agents.translator import translate_layer
from scripts.fetch_articles import article_dir_name

logger = logging.getLogger(__name__)


@dataclass
class LayerResult:
    """Result of generating and evaluating a single layer."""

    law: str
    article_number: int
    article_suffix: str
    layer_type: str
    success: bool
    attempts: int
    eval_result: EvalResult | None
    cost_usd: float
    flagged_for_review: bool


async def generate_and_evaluate(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_type: str,
) -> LayerResult:
    """Generate a layer, evaluate it, retry on failure.

    Returns a LayerResult with success/failure status and cost.
    """
    total_cost = 0.0
    feedback = None
    eval_result = None

    for attempt in range(1, config.max_retries + 1):
        logger.info(
            "Generating %s for Art. %d%s %s (attempt %d/%d)",
            layer_type, article_number, article_suffix, law, attempt, config.max_retries,
        )

        gen_cost = await generate_layer(
            config, law, article_number, article_suffix, layer_type, feedback=feedback,
        )
        total_cost += gen_cost

        logger.info("Evaluating %s for Art. %d%s %s", layer_type, article_number, article_suffix, law)
        eval_result = await evaluate_layer(
            config, law, article_number, article_suffix, layer_type,
        )
        total_cost += 0.0  # Evaluation cost tracked separately

        if eval_result.passed:
            logger.info("✓ %s passed evaluation", layer_type)
            return LayerResult(
                law=law, article_number=article_number, article_suffix=article_suffix,
                layer_type=layer_type, success=True, attempts=attempt,
                eval_result=eval_result, cost_usd=total_cost, flagged_for_review=False,
            )

        feedback = eval_result.feedback_text()
        logger.warning(
            "✗ %s rejected (attempt %d/%d): %s",
            layer_type, attempt, config.max_retries, feedback[:200],
        )

    # Failed after max retries — flag for human review
    logger.error(
        "✗ %s for Art. %d%s %s flagged for review after %d attempts",
        layer_type, article_number, article_suffix, law, config.max_retries,
    )
    return LayerResult(
        law=law, article_number=article_number, article_suffix=article_suffix,
        layer_type=layer_type, success=False, attempts=config.max_retries,
        eval_result=eval_result, cost_usd=total_cost, flagged_for_review=True,
    )


def _update_meta_layer(
    config: AgentConfig, law: str, article_number: int,
    article_suffix: str, layer_type: str, eval_result: EvalResult,
) -> None:
    """Update meta.yaml with layer generation results."""
    dir_name = article_dir_name(article_number, article_suffix)
    meta_path = config.content_root / law.lower() / dir_name / "meta.yaml"

    if meta_path.exists():
        meta = yaml.safe_load(meta_path.read_text()) or {}
    else:
        meta = {}

    if "layers" not in meta:
        meta["layers"] = {}

    existing = meta["layers"].get(layer_type, {})
    version = existing.get("version", 0) + 1

    meta["layers"][layer_type] = {
        "last_generated": date.today().isoformat(),
        "version": version,
        "quality_score": min(eval_result.scores.values()) if eval_result.scores else None,
    }

    meta_path.write_text(
        yaml.dump(meta, default_flow_style=False, allow_unicode=True, sort_keys=False)
    )


async def process_article(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
    layer_types: list[str],
) -> list[LayerResult]:
    """Generate, evaluate, and translate all requested layers for one article.

    For each layer:
    1. Generate and evaluate (with retry loop)
    2. If successful, update meta.yaml
    3. Translate to FR and IT
    """
    results = []

    for layer_type in layer_types:
        result = await generate_and_evaluate(
            config, law, article_number, article_suffix, layer_type,
        )
        results.append(result)

        if result.success and result.eval_result:
            _update_meta_layer(
                config, law, article_number, article_suffix,
                layer_type, result.eval_result,
            )

            # Translate approved layers
            for lang in ("fr", "it"):
                try:
                    await translate_layer(
                        config, law, article_number, article_suffix,
                        layer_type, lang,
                    )
                    logger.info(
                        "Translated %s to %s for Art. %d%s %s",
                        layer_type, lang, article_number, article_suffix, law,
                    )
                except Exception:
                    logger.exception(
                        "Translation failed: %s -> %s for Art. %d%s %s",
                        layer_type, lang, article_number, article_suffix, law,
                    )

    return results
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_generation.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add agents/generation.py tests/test_generation.py
git commit -m "feat: add generation loop with evaluate-retry cycle and translation"
```

---

## Chunk 4: Orchestration & Pipeline

### Task 10: Coordinator (decision mapping)

**Files:**
- Create: `agents/coordinator.py`
- Create: `tests/test_coordinator.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_coordinator.py
"""Tests for the coordinator — decision mapping and pipeline orchestration."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from agents.coordinator import (
    ArticleRef,
    map_decisions_to_articles,
    parse_decision_list,
)


def test_parse_decision_list():
    text = """1. **BGE 130 III 182** - Haftung aus unerlaubter Handlung
   Court: BGer, Date: 2004-02-10
   Laws: OR Art. 41, OR Art. 42

2. **BGE 133 III 323** - Kausalzusammenhang
   Court: BGer, Date: 2007-05-15
   Laws: OR Art. 41, OR Art. 43"""

    decisions = parse_decision_list(text)
    assert len(decisions) >= 2
    assert decisions[0]["reference"] == "BGE 130 III 182"


def test_map_decisions_to_articles():
    decisions = [
        {
            "reference": "BGE 130 III 182",
            "articles": [
                {"law": "OR", "article": 41},
                {"law": "OR", "article": 42},
            ],
        },
        {
            "reference": "BGE 140 III 86",
            "articles": [
                {"law": "OR", "article": 41},
            ],
        },
    ]

    mapping = map_decisions_to_articles(decisions)

    # OR Art. 41 should have 2 decisions
    or_41 = [r for r in mapping if r.law == "OR" and r.article_number == 41]
    assert len(or_41) == 1
    assert len(or_41[0].decision_refs) == 2

    # OR Art. 42 should have 1 decision
    or_42 = [r for r in mapping if r.law == "OR" and r.article_number == 42]
    assert len(or_42) == 1
    assert len(or_42[0].decision_refs) == 1


def test_article_ref_dataclass():
    ref = ArticleRef(law="OR", article_number=41, article_suffix="", decision_refs=["BGE 130 III 182"])
    assert ref.law == "OR"
    assert ref.article_number == 41
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_coordinator.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write agents/coordinator.py**

```python
"""Coordinator — finds new decisions and maps them to articles.

The coordinator is pure Python orchestration (no LLM). It:
1. Queries opencaselaw for decisions since a given date
2. Parses the results to extract cited articles
3. Groups affected articles by law for parallel processing
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import httpx

from scripts.schema import LAWS


@dataclass
class ArticleRef:
    """An article affected by one or more new decisions."""

    law: str
    article_number: int
    article_suffix: str = ""
    decision_refs: list[str] = field(default_factory=list)


def parse_decision_list(text: str) -> list[dict]:
    """Parse opencaselaw search_decisions output into structured decision dicts.

    Each decision has: reference, articles (list of {law, article}).
    Parsing is best-effort — opencaselaw output format may vary.
    """
    decisions = []
    current = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Match decision reference (e.g., "**BGE 130 III 182**")
        ref_match = re.search(r"\*\*?(BGE\s+\d+\s+\w+\s+\d+)\*\*?", line)
        if ref_match:
            if current:
                decisions.append(current)
            current = {"reference": ref_match.group(1), "articles": []}
            continue

        # Match unpublished decision (e.g., "Urteil 4A_123/2024")
        urteil_match = re.search(r"(Urteil\s+\w+_\d+/\d+)", line)
        if urteil_match and not current:
            current = {"reference": urteil_match.group(1), "articles": []}
            continue

        # Match article references (e.g., "OR Art. 41")
        if current and ("Art." in line or "art." in line):
            for art_match in re.finditer(
                r"(\w+)\s+Art\.?\s*(\d+)([a-z]*)", line, re.IGNORECASE
            ):
                law_candidate = art_match.group(1).upper()
                # Normalize common abbreviations
                law_map = {l.upper(): l for l in LAWS}
                law_map["STGB"] = "StGB"
                law_map["STPO"] = "StPO"
                law_map["SCHKG"] = "SchKG"
                law_map["VWVG"] = "VwVG"
                law = law_map.get(law_candidate)
                if law:
                    current["articles"].append({
                        "law": law,
                        "article": int(art_match.group(2)),
                        "suffix": art_match.group(3),
                    })

    if current:
        decisions.append(current)

    return decisions


def map_decisions_to_articles(decisions: list[dict]) -> list[ArticleRef]:
    """Group decisions by article, returning a list of affected articles."""
    article_map: dict[str, ArticleRef] = {}

    for decision in decisions:
        ref = decision["reference"]
        for art in decision.get("articles", []):
            key = f"{art['law']}:{art['article']}:{art.get('suffix', '')}"
            if key not in article_map:
                article_map[key] = ArticleRef(
                    law=art["law"],
                    article_number=art["article"],
                    article_suffix=art.get("suffix", ""),
                )
            article_map[key].decision_refs.append(ref)

    return sorted(article_map.values(), key=lambda r: (r.law, r.article_number))


async def find_new_decisions(mcp_base: str, since_date: str) -> list[dict]:
    """Query opencaselaw for decisions published since the given date.

    Returns parsed decision list.
    """
    from agents.mcp_client import mcp_call

    text = await mcp_call(
        mcp_base, "search_decisions",
        {"query": f"Neue Entscheide seit {since_date}", "date_from": since_date},
    )
    return parse_decision_list(text)


def group_by_law(articles: list[ArticleRef]) -> dict[str, list[ArticleRef]]:
    """Group article references by law for parallel processing."""
    groups: dict[str, list[ArticleRef]] = {}
    for art in articles:
        groups.setdefault(art.law, []).append(art)
    return groups
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_coordinator.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add agents/coordinator.py tests/test_coordinator.py
git commit -m "feat: add coordinator for decision mapping and article grouping"
```

---

### Task 11: Pipeline CLI

**Files:**
- Create: `agents/pipeline.py`
- Create: `tests/test_pipeline.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_pipeline.py
"""Tests for the pipeline CLI."""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

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
        (art_dir / layer).write_text(f"# Placeholder\n")
    return AgentConfig(content_root=content_root)


def _mock_layer_result(success=True):
    from agents.generation import LayerResult
    from agents.evaluator import EvalResult
    return LayerResult(
        law="OR", article_number=41, article_suffix="",
        layer_type="summary", success=success, attempts=1,
        eval_result=EvalResult(verdict="publish", scores={"praezision": 0.96}),
        cost_usd=0.05, flagged_for_review=not success,
    )


def test_bootstrap_article(config):
    with patch(
        "agents.pipeline.process_article",
        new_callable=AsyncMock,
        return_value=[_mock_layer_result()],
    ):
        results = asyncio.run(bootstrap_article(config, "OR", 41, ""))
        assert len(results) >= 1


def test_daily_pipeline_no_new_decisions(config):
    with (
        patch(
            "agents.pipeline.find_new_decisions",
            new_callable=AsyncMock,
            return_value=[],
        ),
    ):
        stats = asyncio.run(daily_pipeline(config))
        assert stats["articles_processed"] == 0


def test_daily_pipeline_with_decisions(config):
    decisions = [
        {
            "reference": "BGE 150 III 100",
            "articles": [{"law": "OR", "article": 41, "suffix": ""}],
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_pipeline.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write agents/pipeline.py**

```python
"""Pipeline CLI — entry point for daily runs, bootstrap, and single-article generation.

Subcommands:
  daily       Run the daily pipeline (find new decisions, update affected articles)
  bootstrap   Generate all layers for all articles (initial one-time run)
  single      Generate layers for a single article
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
from datetime import date, timedelta
from pathlib import Path

from agents.config import AgentConfig
from agents.coordinator import (
    find_new_decisions,
    group_by_law,
    map_decisions_to_articles,
)
from agents.generation import LayerResult, process_article

logger = logging.getLogger(__name__)


async def bootstrap_article(
    config: AgentConfig,
    law: str,
    article_number: int,
    article_suffix: str,
) -> list[LayerResult]:
    """Generate all three layers for a single article (bootstrap mode)."""
    return await process_article(
        config, law, article_number, article_suffix,
        layer_types=["caselaw", "doctrine", "summary"],
    )


async def daily_pipeline(
    config: AgentConfig,
    since_date: str | None = None,
) -> dict:
    """Run the daily pipeline.

    1. Find new decisions since last run
    2. Map decisions to affected articles
    3. Update caselaw layer for each affected article
    4. Check if doctrine needs regeneration
    5. Return statistics
    """
    if since_date is None:
        since_date = (date.today() - timedelta(days=1)).isoformat()

    logger.info("Daily pipeline: searching for decisions since %s", since_date)

    decisions = await find_new_decisions(config.mcp_base_url, since_date)
    if not decisions:
        logger.info("No new decisions found.")
        return {"articles_processed": 0, "decisions_found": 0, "cost_usd": 0.0}

    articles = map_decisions_to_articles(decisions)
    by_law = group_by_law(articles)

    total_cost = 0.0
    all_results: list[LayerResult] = []

    # Process laws in parallel (each law's articles processed sequentially within)
    async def _process_law(law: str, law_articles: list) -> list[LayerResult]:
        results = []
        for art in law_articles:
            # 1. Update caselaw layer
            caselaw_results = await process_article(
                config, art.law, art.article_number, art.article_suffix,
                layer_types=["caselaw"],
            )
            results.extend(caselaw_results)

            # 2. Cascade: if caselaw passed, check if doctrine shift warrants regeneration
            # The evaluator feedback may indicate a doctrinal shift. If new leading cases
            # were added, regenerate doctrine → then summary.
            caselaw_passed = any(r.success for r in caselaw_results)
            if caselaw_passed and len(art.decision_refs) > 0:
                logger.info(
                    "New leading cases for Art. %d%s %s — cascading to doctrine+summary",
                    art.article_number, art.article_suffix, art.law,
                )
                cascade_results = await process_article(
                    config, art.law, art.article_number, art.article_suffix,
                    layer_types=["doctrine", "summary"],
                )
                results.extend(cascade_results)

        return results

    # Dispatch law agents in parallel (spec requirement)
    import asyncio as aio
    law_tasks = [
        _process_law(law, arts) for law, arts in by_law.items()
    ]
    law_results = await aio.gather(*law_tasks)
    for results in law_results:
        all_results.extend(results)
        total_cost += sum(r.cost_usd for r in results)

    stats = {
        "date": since_date,
        "decisions_found": len(decisions),
        "articles_processed": len(articles),
        "layers_generated": len(all_results),
        "layers_passed": sum(1 for r in all_results if r.success),
        "layers_failed": sum(1 for r in all_results if not r.success),
        "flagged_for_review": sum(1 for r in all_results if r.flagged_for_review),
        "cost_usd": total_cost,
    }
    logger.info("Daily pipeline complete: %s", json.dumps(stats, indent=2))
    return stats


async def bootstrap_law(config: AgentConfig, law: str) -> list[LayerResult]:
    """Bootstrap all articles for a single law."""
    import yaml

    law_dir = config.content_root / law.lower()
    if not law_dir.exists():
        logger.error("No content directory for %s at %s", law, law_dir)
        return []

    results = []
    for art_dir in sorted(law_dir.iterdir()):
        if not art_dir.is_dir() or not art_dir.name.startswith("art-"):
            continue

        meta_path = art_dir / "meta.yaml"
        if not meta_path.exists():
            continue

        meta = yaml.safe_load(meta_path.read_text()) or {}
        article_number = meta.get("article", 0)
        article_suffix = meta.get("article_suffix", "")

        if article_number <= 0:
            continue

        art_results = await bootstrap_article(
            config, law, article_number, article_suffix,
        )
        results.extend(art_results)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="openlegalcommentary agent pipeline",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # daily
    daily_parser = sub.add_parser("daily", help="Run daily update pipeline")
    daily_parser.add_argument("--since", help="Date to search from (YYYY-MM-DD)")

    # bootstrap
    boot_parser = sub.add_parser("bootstrap", help="Bootstrap all articles")
    boot_parser.add_argument("--law", help="Only bootstrap a specific law")

    # single
    single_parser = sub.add_parser("single", help="Generate layers for one article")
    single_parser.add_argument("law", help="Law abbreviation (e.g., OR)")
    single_parser.add_argument("article", type=int, help="Article number")
    single_parser.add_argument("--suffix", default="", help="Article suffix (e.g., a)")
    single_parser.add_argument(
        "--layers", nargs="+", default=["caselaw", "doctrine", "summary"],
        help="Layer types to generate",
    )

    # common
    parser.add_argument("--content-root", default="content", help="Content directory")
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config = AgentConfig(content_root=Path(args.content_root))

    if args.command == "daily":
        stats = asyncio.run(daily_pipeline(config, since_date=args.since))
        print(json.dumps(stats, indent=2))

    elif args.command == "bootstrap":
        from scripts.schema import LAWS
        laws = [args.law] if args.law else list(LAWS)
        for law in laws:
            logger.info("Bootstrapping %s...", law)
            results = asyncio.run(bootstrap_law(config, law))
            passed = sum(1 for r in results if r.success)
            logger.info("%s: %d/%d layers passed", law, passed, len(results))

    elif args.command == "single":
        results = asyncio.run(
            process_article(
                config, args.law, args.article, args.suffix, args.layers,
            )
        )
        for r in results:
            status = "✓" if r.success else "✗"
            print(f"{status} {r.layer_type}: {r.attempts} attempts, ${r.cost_usd:.2f}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_pipeline.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add agents/pipeline.py tests/test_pipeline.py
git commit -m "feat: add pipeline CLI with daily, bootstrap, and single-article modes"
```

---

### Task 12: Update CLAUDE.md, lint, test, commit

**Files:**
- Modify: `CLAUDE.md`
- Modify: `agents/__init__.py`

- [ ] **Step 1: Update agents/__init__.py with public API**

```python
"""Agent pipeline for openlegalcommentary.

Public API:
  - AgentConfig: Pipeline configuration
  - generate_layer: Run law agent for one article layer
  - evaluate_layer: Run evaluator agent
  - translate_layer: Run translator agent
  - process_article: Full generate → evaluate → retry → translate loop
  - daily_pipeline: Daily update pipeline
"""
from agents.config import AgentConfig

__all__ = ["AgentConfig"]
```

- [ ] **Step 2: Update CLAUDE.md with new commands**

Add to the Commands section:

```markdown
- `uv run python -m agents.pipeline daily` — run daily update pipeline
- `uv run python -m agents.pipeline bootstrap` — bootstrap all articles (initial run)
- `uv run python -m agents.pipeline single OR 41` — generate layers for one article
```

- [ ] **Step 3: Run ruff check and fix**

Run: `uv run ruff check . --fix`
Then manually fix any remaining line-length issues.

- [ ] **Step 4: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests pass (18 existing + ~40 new ≈ 58 tests)

- [ ] **Step 5: Commit**

```bash
git add agents/__init__.py CLAUDE.md
git commit -m "docs: update CLAUDE.md with pipeline commands, export agent public API"
```

- [ ] **Step 6: Push to GitHub**

```bash
git push origin main
```
