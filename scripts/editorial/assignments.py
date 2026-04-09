"""Editor assignment management for openlegalcommentary.

Manages which human editors are responsible for which laws/articles,
and tracks their agent editor pairings.

Assignment data is stored in scripts/editorial/editors.json.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

EDITORS_PATH = Path("scripts/editorial/editors.json")


@dataclass
class EditorAssignment:
    """An editor's assignment to a law or set of articles."""

    editor: str
    law: str
    articles: list[int] = field(default_factory=list)  # Empty = all articles
    role: str = "lead"  # lead, reviewer, contributor


@dataclass
class EditorRegistry:
    """Registry of all editor assignments."""

    assignments: list[EditorAssignment] = field(default_factory=list)

    def assign(
        self,
        editor: str,
        law: str,
        articles: list[int] | None = None,
        role: str = "lead",
    ) -> None:
        """Assign an editor to a law (or specific articles)."""
        # Remove existing assignment for this editor+law
        self.assignments = [
            a for a in self.assignments
            if not (a.editor == editor and a.law == law)
        ]
        self.assignments.append(EditorAssignment(
            editor=editor,
            law=law,
            articles=articles or [],
            role=role,
        ))

    def unassign(self, editor: str, law: str) -> None:
        """Remove an editor's assignment to a law."""
        self.assignments = [
            a for a in self.assignments
            if not (a.editor == editor and a.law == law)
        ]

    def get_editor_for(self, law: str, article: int | None = None) -> str:
        """Find the assigned editor for a law/article."""
        for a in self.assignments:
            if a.law != law:
                continue
            if not a.articles or (article and article in a.articles):
                return a.editor
        return ""

    def get_assignments_for(self, editor: str) -> list[EditorAssignment]:
        """Get all assignments for an editor."""
        return [a for a in self.assignments if a.editor == editor]

    def list_editors(self) -> list[str]:
        """List all registered editors."""
        return sorted({a.editor for a in self.assignments})

    def save(self, path: Path | None = None) -> None:
        """Save registry to JSON."""
        path = path or EDITORS_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {"assignments": [asdict(a) for a in self.assignments]}
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    @classmethod
    def load(cls, path: Path | None = None) -> EditorRegistry:
        """Load registry from JSON."""
        path = path or EDITORS_PATH
        registry = cls()
        if path.exists():
            data = json.loads(path.read_text())
            for item in data.get("assignments", []):
                registry.assignments.append(EditorAssignment(**item))
        return registry
