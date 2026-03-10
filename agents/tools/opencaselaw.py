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
