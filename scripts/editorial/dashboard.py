"""Editorial dashboard — CLI tool for managing the editorial workflow.

Usage:
  uv run python -m scripts.editorial.dashboard status
  uv run python -m scripts.editorial.dashboard status --law BV
  uv run python -m scripts.editorial.dashboard queue
  uv run python -m scripts.editorial.dashboard queue --editor jonas
  uv run python -m scripts.editorial.dashboard assign BV jonas
  uv run python -m scripts.editorial.dashboard editors
"""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from scripts.editorial.assignments import EditorRegistry
from scripts.editorial.review_queue import print_queue, scan_review_queue
from scripts.schema import LAWS

CONTENT_ROOT = Path("content")


def cmd_status(args: argparse.Namespace) -> None:
    """Show overall editorial status."""
    laws = [args.law] if args.law else list(LAWS)

    total_articles = 0
    total_with_layers = 0
    status_counts: dict[str, int] = {}
    verified_count = 0
    unverified_count = 0

    for law in laws:
        law_dir = CONTENT_ROOT / law.lower()
        if not law_dir.exists():
            continue

        for art_dir in sorted(law_dir.iterdir()):
            if not art_dir.is_dir() or not art_dir.name.startswith("art-"):
                continue

            total_articles += 1
            meta_path = art_dir / "meta.yaml"
            if not meta_path.exists():
                continue

            meta = yaml.safe_load(meta_path.read_text()) or {}
            layers = meta.get("layers", {})
            if layers:
                total_with_layers += 1

            for layer_data in layers.values():
                if not isinstance(layer_data, dict):
                    continue
                status = layer_data.get("editorial_status", "draft")
                status_counts[status] = status_counts.get(status, 0) + 1
                if layer_data.get("verified"):
                    verified_count += 1
                elif layer_data.get("quality_score") is not None:
                    unverified_count += 1

    scope = args.law if args.law else "All laws"
    print(f"\nEditorial Status — {scope}")
    print(f"{'='*50}")
    print(f"Total articles:        {total_articles}")
    print(f"With generated layers: {total_with_layers}")
    print(f"Without content:       {total_articles - total_with_layers}")

    if status_counts:
        print("\nLayers by editorial status:")
        for status, count in sorted(status_counts.items()):
            print(f"  {status:20s} {count:>5}")

    print("\nCitation verification:")
    print(f"  Verified:    {verified_count}")
    print(f"  Unverified:  {unverified_count}")


def cmd_queue(args: argparse.Namespace) -> None:
    """Show the review queue."""
    items = scan_review_queue(
        law=args.law,
        editor=args.editor,
    )
    print_queue(items)


def cmd_assign(args: argparse.Namespace) -> None:
    """Assign an editor to a law."""
    registry = EditorRegistry.load()
    registry.assign(args.editor, args.law, role=args.role)
    registry.save()
    print(f"Assigned {args.editor} as {args.role} for {args.law}")


def cmd_editors(args: argparse.Namespace) -> None:
    """List all editors and their assignments."""
    registry = EditorRegistry.load()
    editors = registry.list_editors()
    if not editors:
        print("No editors registered. Use 'assign' to add editors.")
        return

    print("\nRegistered Editors")
    print(f"{'='*50}")
    for editor in editors:
        assignments = registry.get_assignments_for(editor)
        laws = ", ".join(
            f"{a.law} ({a.role})" for a in assignments
        )
        print(f"  {editor}: {laws}")


def main():
    parser = argparse.ArgumentParser(
        description="Editorial dashboard for openlegalcommentary",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # status
    status_p = sub.add_parser("status", help="Show editorial status")
    status_p.add_argument("--law", help="Filter by law")

    # queue
    queue_p = sub.add_parser("queue", help="Show review queue")
    queue_p.add_argument("--law", help="Filter by law")
    queue_p.add_argument("--editor", help="Filter by editor")

    # assign
    assign_p = sub.add_parser("assign", help="Assign editor to law")
    assign_p.add_argument("law", help="Law abbreviation")
    assign_p.add_argument("editor", help="Editor name")
    assign_p.add_argument(
        "--role", default="lead",
        choices=["lead", "reviewer", "contributor"],
    )

    # editors
    sub.add_parser("editors", help="List editors")

    args = parser.parse_args()

    commands = {
        "status": cmd_status,
        "queue": cmd_queue,
        "assign": cmd_assign,
        "editors": cmd_editors,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
