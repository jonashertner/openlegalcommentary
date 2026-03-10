"""Bootstrap state tracker for resumable content generation.

Tracks per-article completion status in a JSON file, enabling
crash-safe resumption of the bootstrap pipeline.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
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
            "articles": [asdict(a) for a in self._articles.values()],
            "total_cost": self._total_cost,
        }
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def add_article(self, law: str, article_number: int, suffix: str) -> None:
        """Register an article for bootstrapping (idempotent)."""
        key = f"{law}:{article_number}:{suffix}"
        if key not in self._articles:
            self._articles[key] = ArticleStatus(
                law=law,
                article_number=article_number,
                article_suffix=suffix,
            )

    def mark_completed(self, law: str, article_number: int, suffix: str, cost: float) -> None:
        """Mark an article as successfully completed."""
        key = f"{law}:{article_number}:{suffix}"
        if key in self._articles:
            self._articles[key].status = "completed"
            self._articles[key].cost_usd = cost
            self._total_cost += cost

    def mark_failed(self, law: str, article_number: int, suffix: str, error: str = "") -> None:
        """Mark an article as failed."""
        key = f"{law}:{article_number}:{suffix}"
        if key in self._articles:
            self._articles[key].status = "failed"
            self._articles[key].error = error

    def get_pending(self) -> list[ArticleStatus]:
        """Return all articles that still need processing."""
        return [a for a in self._articles.values() if a.status == "pending"]

    def budget_exceeded(self, max_budget: float) -> bool:
        """Check if total cost exceeds budget."""
        return self._total_cost > max_budget

    @property
    def total(self) -> int:
        return len(self._articles)

    @property
    def completed(self) -> int:
        return sum(1 for a in self._articles.values() if a.status == "completed")

    @property
    def failed(self) -> int:
        return sum(1 for a in self._articles.values() if a.status == "failed")

    @property
    def pending(self) -> int:
        return sum(1 for a in self._articles.values() if a.status == "pending")

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
