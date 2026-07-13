"""
Pydantic response models.

Two families:
  * View 1-3 models (PlayerSummary, PlayerProfile, ComparisonResult).
  * The chat discriminated union (ChatResponse) -- a `type`-tagged union so the frontend
    renders each shape dynamically instead of parsing one hardcoded output.
"""
from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from app.models.domain import Player

# --------------------------------------------------------------------------- #
# Shared / Views 1-3
# --------------------------------------------------------------------------- #


class PlayerSummary(BaseModel):
    player_id: str
    name: str
    photo: str | None = None
    position: str
    role: str
    age: int | None = None
    nation: str | None = None
    height_cm: int | None = None
    foot: str | None = None
    club: str
    club_id: int | None = None
    club_logo: str | None = None
    competition: str
    country: str
    market_value_eur: float | None = None

    @classmethod
    def of(cls, p: Player) -> "PlayerSummary":
        return cls(
            player_id=p.player_id, name=p.name, photo=p.photo, position=p.position, role=p.role,
            age=p.age, nation=p.nation, height_cm=p.height_cm, foot=p.foot,
            club=p.club, club_id=p.club_id, club_logo=p.club_logo,
            competition=p.competition, country=p.country,
            market_value_eur=p.market_value_eur,
        )


class MetricContext(BaseModel):
    metric: str
    label: str
    value: float | None
    cohort_average: float | None
    percentile: float | None


class SeasonTotal(BaseModel):
    key: str
    label: str
    value: float | None


class CompetitionLine(BaseModel):
    competition: str
    competition_type: str
    club: str
    matches: float | None
    minutes: float | None
    goals: float | None
    assists: float | None


class MetricHighlight(BaseModel):
    label: str
    percentile: float


class PlayerProfile(BaseModel):
    player: PlayerSummary
    cohort_label: str
    cohort_size: int
    rating: float | None = None                    # avg percentile vs cohort
    strengths: list[MetricHighlight] = Field(default_factory=list)
    weaknesses: list[MetricHighlight] = Field(default_factory=list)
    totals: list[SeasonTotal]
    metrics: list[MetricContext]
    breakdown: list[CompetitionLine]
    similar: list[PlayerSummary] = Field(default_factory=list)


class ComparisonMetric(BaseModel):
    metric: str
    label: str
    a_value: float | None
    b_value: float | None
    a_percentile: float | None
    b_percentile: float | None
    winner: Literal["a", "b"] | None


class MarketSide(BaseModel):
    market_value_eur: float | None
    value_percentile: float | None


class ComparisonResult(BaseModel):
    player_a: PlayerSummary
    player_b: PlayerSummary
    metrics: list[ComparisonMetric]
    wins: dict[str, int]
    overall_winner: Literal["a", "b", "tie"]
    market_context: dict[str, MarketSide]


class SearchResponse(BaseModel):
    query: str
    count: int          # results in this page
    total: int          # total matches before the page limit
    results: list[PlayerSummary]


# --------------------------------------------------------------------------- #
# Team & Competition profiles
# --------------------------------------------------------------------------- #


class ClubInfo(BaseModel):
    club_id: int
    name: str
    logo: str | None = None
    competition: str | None = None
    country: str | None = None
    squad_value: float | None = None
    squad_size: int | None = None
    avg_age: float | None = None
    stadium: str | None = None
    stadium_seats: int | None = None
    coach: str | None = None


class SquadMember(BaseModel):
    player: PlayerSummary
    goals: float
    assists: float
    minutes: float
    matches: float


class TeamProfile(BaseModel):
    club: ClubInfo
    squad_count: int
    total_goals: float
    competitions: list[str]
    top_scorer: SquadMember | None = None
    squad: list[SquadMember]


class ClubResult(BaseModel):
    club_id: int
    name: str
    logo: str | None = None
    competition: str | None = None
    country: str | None = None


class CompetitionInfo(BaseModel):
    competition_id: str
    competition: str
    type: str
    country: str
    confederation: str | None = None
    flag: str | None = None


class CompetitionClub(BaseModel):
    club_id: int
    name: str
    logo: str | None = None
    goals: float


class CompetitionProfile(BaseModel):
    competition: CompetitionInfo
    player_count: int
    club_count: int
    total_goals: float
    top_scorers: list[PlayerSummary]
    top_value: list[PlayerSummary]
    clubs: list[CompetitionClub]


# --------------------------------------------------------------------------- #
# Chat: the "explain trace" attached to every response
# --------------------------------------------------------------------------- #


class QueryTrace(BaseModel):
    """How the question was understood (intent, provider, resolved filters)."""
    intent: str
    provider: str                       # "gemini" | "rule_based"
    metric: str | None = None
    entities: list[str] = Field(default_factory=list)
    filters: dict = Field(default_factory=dict)
    notes: str | None = None


# --------------------------------------------------------------------------- #
# Chat: discriminated union of response shapes
# --------------------------------------------------------------------------- #


class TextResponse(BaseModel):
    type: Literal["text"] = "text"
    title: str | None = None
    text: str
    trace: QueryTrace


class Column(BaseModel):
    key: str
    label: str
    kind: Literal["text", "number", "money"] = "text"


class TableResponse(BaseModel):
    type: Literal["table"] = "table"
    title: str
    columns: list[Column]
    rows: list[dict]
    narrative: str | None = None
    trace: QueryTrace


class ChartSeries(BaseModel):
    name: str
    values: list[float | None]


class ChartResponse(BaseModel):
    type: Literal["chart"] = "chart"
    chart_type: Literal["radar", "bar"]
    title: str
    categories: list[str]
    series: list[ChartSeries]
    value_kind: Literal["percentile", "raw"] = "percentile"
    narrative: str | None = None
    footnote: str | None = None
    trace: QueryTrace


class ComparisonResponse(BaseModel):
    type: Literal["comparison"] = "comparison"
    title: str
    data: ComparisonResult
    narrative: str | None = None
    trace: QueryTrace


class ClarificationOption(BaseModel):
    label: str
    query: str      # the refined question sent back when the chip is clicked


class ClarificationResponse(BaseModel):
    type: Literal["clarification"] = "clarification"
    message: str
    options: list[ClarificationOption]
    trace: QueryTrace


class ErrorResponse(BaseModel):
    type: Literal["error"] = "error"
    message: str
    suggestions: list[str] = Field(default_factory=list)
    trace: QueryTrace


ChatResponse = Annotated[
    Union[
        TextResponse, TableResponse, ChartResponse,
        ComparisonResponse, ClarificationResponse, ErrorResponse,
    ],
    Field(discriminator="type"),
]
