"""opencaselaw MCP wrapper tools for the agent pipeline.

Wraps HTTP calls to the opencaselaw MCP server, providing tools for:
- Fetching article text from LexFind/Fedlex
- Searching court decisions
- Finding leading cases (BGE)
- Getting full decision details and case briefs
"""
from __future__ import annotations

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
