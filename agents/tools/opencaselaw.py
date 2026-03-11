"""opencaselaw MCP wrapper tools for the agent pipeline.

Wraps HTTP calls to the opencaselaw MCP server (Streamable HTTP transport),
providing tools for:
- Searching court decisions (930k+ decisions)
- Finding leading cases by citation authority
- Getting full decision details and structured case briefs
- Getting doctrine and commentary for statute articles
- Finding citation chains
"""
from __future__ import annotations

from agents.mcp_client import mcp_call


def create_opencaselaw_tools(mcp_base: str) -> dict:
    """Create opencaselaw tool functions bound to an MCP base URL.

    Returns a dict of tool_name -> async callable.
    """

    async def search_decisions(args):
        try:
            params = {"query": args.get("query", "")}
            if args.get("law_abbreviation"):
                params["court"] = args["law_abbreviation"]
            if args.get("limit"):
                params["limit"] = args["limit"]
            text = await mcp_call(mcp_base, "search_decisions", params)
            return {"content": [{"type": "text", "text": text}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": str(e)}], "is_error": True}

    async def find_leading_cases(args):
        try:
            params = {}
            if args.get("article"):
                params["article"] = args["article"]
            if args.get("law_abbreviation"):
                params["law_code"] = args["law_abbreviation"]
            if args.get("query"):
                params["query"] = args["query"]
            text = await mcp_call(mcp_base, "find_leading_cases", params)
            return {"content": [{"type": "text", "text": text}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": str(e)}], "is_error": True}

    async def get_decision(args):
        try:
            text = await mcp_call(mcp_base, "get_decision", {
                "decision_id": args["decision_id"],
            })
            return {"content": [{"type": "text", "text": text}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": str(e)}], "is_error": True}

    async def get_case_brief(args):
        try:
            text = await mcp_call(mcp_base, "get_case_brief", {
                "case": args.get("case", args.get("decision_id", "")),
            })
            return {"content": [{"type": "text", "text": text}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": str(e)}], "is_error": True}

    async def get_doctrine(args):
        try:
            text = await mcp_call(mcp_base, "get_doctrine", {
                "query": args["query"],
            })
            return {"content": [{"type": "text", "text": text}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": str(e)}], "is_error": True}

    async def get_commentary(args):
        try:
            params = {"abbreviation": args["abbreviation"]}
            if args.get("article"):
                params["article"] = args["article"]
            text = await mcp_call(mcp_base, "get_commentary", params)
            return {"content": [{"type": "text", "text": text}]}
        except Exception as e:
            return {"content": [{"type": "text", "text": str(e)}], "is_error": True}

    return {
        "search_decisions": search_decisions,
        "find_leading_cases": find_leading_cases,
        "get_decision": get_decision,
        "get_case_brief": get_case_brief,
        "get_doctrine": get_doctrine,
        "get_commentary": get_commentary,
    }
