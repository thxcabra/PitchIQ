"""The structured query -- the single contract between NLU and execution."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Intent = Literal["ranking", "lookup", "comparison", "ambiguous", "out_of_scope"]


class QueryFilters(BaseModel):
    competition: str | None = None    # e.g. "Premier League", "UEFA Champions League"
    country: str | None = None        # league country, e.g. "Italy"
    competition_type: str | None = None  # League / Domestic Cup / Continental / International
    club: str | None = None
    position: str | None = None       # broad: Forward/Midfielder/Defender/Goalkeeper
    role: str | None = None           # detailed: Winger, Centre-Forward, ...
    nation: str | None = None
    min_age: int | None = None
    max_age: int | None = None
    min_minutes: int | None = None


class StructuredQuery(BaseModel):
    intent: Intent
    metric: str | None = None                    # canonical metric key (validated)
    entities: list[str] = Field(default_factory=list)   # raw player-name texts
    filters: QueryFilters = Field(default_factory=QueryFilters)
    limit: int | None = None
    ascending: bool | None = None                # True -> "worst/lowest"
    provider: str = "rule_based"                 # who produced this
    notes: str | None = None                     # e.g. why it's ambiguous
    raw_query: str = ""
