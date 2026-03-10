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
