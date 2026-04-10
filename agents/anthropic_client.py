"""Anthropic Messages API client with tool use loop.

Replaces the Claude Agent SDK with direct API calls, allowing the pipeline
to run without spawning a Claude Code subprocess.
"""
from __future__ import annotations

import logging

import anthropic

logger = logging.getLogger(__name__)

# Model mapping from short names to API model IDs
MODEL_MAP = {
    "opus": "claude-opus-4-6",
    "sonnet": "claude-sonnet-4-6",
}

# Tool schemas for content tools
CONTENT_TOOL_SCHEMAS = [
    {
        "name": "read_article_meta",
        "description": "Read meta.yaml for a commentary article",
        "input_schema": {
            "type": "object",
            "properties": {
                "law": {"type": "string"},
                "article_number": {"type": "integer"},
                "article_suffix": {"type": "string", "default": ""},
            },
            "required": ["law", "article_number"],
        },
    },
    {
        "name": "read_layer_content",
        "description": "Read a commentary layer markdown file (summary, doctrine, or caselaw)",
        "input_schema": {
            "type": "object",
            "properties": {
                "law": {"type": "string"},
                "article_number": {"type": "integer"},
                "article_suffix": {"type": "string", "default": ""},
                "layer": {"type": "string"},
            },
            "required": ["law", "article_number", "layer"],
        },
    },
    {
        "name": "write_layer_content",
        "description": "Write commentary content to a layer markdown file",
        "input_schema": {
            "type": "object",
            "properties": {
                "law": {"type": "string"},
                "article_number": {"type": "integer"},
                "article_suffix": {"type": "string", "default": ""},
                "layer": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["law", "article_number", "layer", "content"],
        },
    },
]

# Tool schemas for opencaselaw tools
OPENCASELAW_TOOL_SCHEMAS = [
    {
        "name": "search_decisions",
        "description": (
            "Search 930k+ Swiss court decisions. Supports keywords, "
            "phrases, Boolean operators, docket numbers, article refs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "law_abbreviation": {"type": "string", "default": ""},
                "limit": {"type": "integer", "default": 20},
            },
            "required": ["query"],
        },
    },
    {
        "name": "find_leading_cases",
        "description": (
            "Find most-cited decisions for a statute article. "
            "Ranked by citation authority from 7.85M citation edges."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "article": {"type": "string"},
                "law_abbreviation": {"type": "string"},
                "query": {"type": "string"},
            },
            "required": [],
        },
    },
    {
        "name": "get_decision",
        "description": "Get the full text and details of a court decision.",
        "input_schema": {
            "type": "object",
            "properties": {
                "decision_id": {"type": "string"},
            },
            "required": ["decision_id"],
        },
    },
    {
        "name": "get_case_brief",
        "description": (
            "Structured case brief: regeste, facts, key reasoning, "
            "holding, applicable statutes, citation authority."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "case": {
                    "type": "string",
                    "description": "BGE ref, decision_id, or docket number.",
                },
            },
            "required": ["case"],
        },
    },
    {
        "name": "get_doctrine",
        "description": (
            "Get leading cases and doctrine for a statute article or "
            "legal concept. Returns statute text, top BGEs, timeline."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "e.g. 'Art. 41 OR' or 'Tierhalterhaftung'",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_commentary",
        "description": (
            "Get scholarly commentary from OnlineKommentar.ch (CC-BY-4.0) "
            "for a Swiss law article."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "abbreviation": {"type": "string"},
                "article": {"type": "string"},
            },
            "required": ["abbreviation"],
        },
    },
]


async def run_agent(
    *,
    system_prompt: str,
    prompt: str,
    model: str,
    content_tools: dict,
    opencaselaw_tools: dict | None = None,
    allowed_tools: list[str],
    max_turns: int = 25,
) -> tuple[str, float]:
    """Run an agent loop with the Anthropic Messages API.

    Returns (final_text_response, estimated_cost_usd).
    """
    model_id = MODEL_MAP.get(model, model)
    client = anthropic.Anthropic()

    # Build tool list from allowed tools
    tool_schemas = []
    tool_funcs = {}
    for schema in CONTENT_TOOL_SCHEMAS:
        name = schema["name"]
        if name in allowed_tools or f"mcp__content__{name}" in allowed_tools:
            tool_schemas.append(schema)
            tool_funcs[name] = content_tools[name]
    if opencaselaw_tools:
        for schema in OPENCASELAW_TOOL_SCHEMAS:
            name = schema["name"]
            if name in allowed_tools or f"mcp__opencaselaw__{name}" in allowed_tools:
                tool_schemas.append(schema)
                tool_funcs[name] = opencaselaw_tools[name]

    messages = [{"role": "user", "content": prompt}]
    total_input_tokens = 0
    total_output_tokens = 0
    final_text = ""

    for turn in range(max_turns):
        response = client.messages.create(
            model=model_id,
            max_tokens=8192,
            system=system_prompt,
            tools=tool_schemas,
            messages=messages,
        )

        total_input_tokens += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens

        # Collect text and tool use blocks
        assistant_content = response.content
        messages.append({"role": "assistant", "content": assistant_content})

        # Extract text from response
        for block in assistant_content:
            if block.type == "text":
                final_text = block.text

        # If no tool use, we're done
        if response.stop_reason != "tool_use":
            break

        # Execute tool calls
        tool_results = []
        for block in assistant_content:
            if block.type != "tool_use":
                continue
            tool_name = block.name
            tool_input = block.input
            logger.debug("Tool call: %s(%s)", tool_name, tool_input)

            func = tool_funcs.get(tool_name)
            if not func:
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": f"Unknown tool: {tool_name}",
                    "is_error": True,
                })
                continue

            try:
                result = await func(tool_input)
                content_blocks = result.get("content", [])
                text_parts = [b["text"] for b in content_blocks if b.get("type") == "text"]
                is_error = result.get("is_error", False)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": "\n".join(text_parts),
                    "is_error": is_error,
                })
            except Exception as e:
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": f"Tool error: {e}",
                    "is_error": True,
                })

        messages.append({"role": "user", "content": tool_results})

    # Rough cost estimate (Sonnet pricing as baseline)
    cost = (total_input_tokens * 3 + total_output_tokens * 15) / 1_000_000
    if "opus" in model_id:
        cost = (total_input_tokens * 15 + total_output_tokens * 75) / 1_000_000

    return final_text, cost
