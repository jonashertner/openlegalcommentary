"""Pydantic schema for BSK/CR commentary reference data."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class Position(BaseModel):
    author: str
    n: str
    topic: str
    position: str


class Controversy(BaseModel):
    topic: str
    positions: dict[str, str] = Field(min_length=2)


class ArticleRef(BaseModel):
    authors: list[str] = Field(min_length=1)
    edition: str = Field(min_length=1)
    randziffern_map: dict[str, str] = Field(default_factory=dict)
    positions: list[Position] = Field(default_factory=list)
    controversies: list[Controversy] = Field(default_factory=list)
    cross_refs: list[str] = Field(default_factory=list)
    key_literature: list[str] = Field(default_factory=list)

    @field_validator("authors")
    @classmethod
    def authors_nonempty(cls, v):
        if not v:
            raise ValueError("authors must not be empty")
        return v
