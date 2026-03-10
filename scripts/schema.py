"""Content schema definitions for openlegalcommentary article metadata."""
from __future__ import annotations
from typing import Literal
import yaml
from pydantic import BaseModel, Field, field_validator

LAWS = ("BV", "ZGB", "OR", "ZPO", "StGB", "StPO", "SchKG", "VwVG")

SR_NUMBERS: dict[str, str] = {
    "BV": "101", "ZGB": "210", "OR": "220", "ZPO": "272",
    "StGB": "311.0", "StPO": "312.0", "SchKG": "281.1", "VwVG": "172.021",
}

LAW_ELI_PATHS: dict[str, str] = {
    "BV": "1999/404", "ZGB": "24/233_245_233", "OR": "27/317_321_377",
    "ZPO": "2010/262", "StGB": "54/757_781_799", "StPO": "2010/267",
    "SchKG": "11/529_488_529", "VwVG": "1969/737_757_755",
}

LayerName = Literal["summary", "doctrine", "caselaw"]


class LayerMeta(BaseModel):
    last_generated: str = Field(description="ISO date of last generation")
    version: int = Field(ge=1, description="Monotonically increasing version number")
    quality_score: float | None = Field(default=None, ge=0.0, le=1.0)
    trigger: str | None = Field(default=None)
    last_reviewed: str | None = Field(default=None)
    total_decisions: int | None = Field(default=None, ge=0)
    new_decisions_count: int | None = Field(default=None, ge=0)


class ArticleMeta(BaseModel):
    law: str
    article: int = Field(gt=0)
    article_suffix: str = Field(default="")
    title: str = Field(min_length=1)
    sr_number: str
    absatz_count: int = Field(ge=1)
    fedlex_url: str
    lexfind_id: int | None = Field(default=None)
    lexfind_url: str = Field(default="")
    in_force_since: str = Field(default="")
    layers: dict[str, LayerMeta] = Field(default_factory=dict)

    @field_validator("law")
    @classmethod
    def validate_law(cls, v):
        if v not in LAWS:
            raise ValueError(f"Unknown law: {v}. Must be one of {LAWS}")
        return v

    @field_validator("layers")
    @classmethod
    def validate_layer_names(cls, v):
        valid = {"summary", "doctrine", "caselaw"}
        for key in v:
            if key not in valid:
                raise ValueError(f"Unknown layer: {key}. Must be one of {valid}")
        return v

    def to_yaml(self) -> str:
        return yaml.dump(self.model_dump(exclude_none=True), default_flow_style=False, allow_unicode=True, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> ArticleMeta:
        return cls(**yaml.safe_load(yaml_str))
