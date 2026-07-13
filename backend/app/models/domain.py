"""
Core domain model.

The unit of the dataset is a player-in-a-competition (one row per player per
competition). `row_id` identifies the row; `player_id` identifies the person and is
shared across all of that player's competition rows.
"""
from __future__ import annotations

from pydantic import BaseModel

# Numeric metric columns present in players.csv (rank/compare/percentile on these).
# The xg/shots/key_passes block is present only for Big-5 league rows (Understat enrichment).
METRIC_COLUMNS: tuple[str, ...] = (
    "matches", "minutes", "nineties", "goals", "assists", "goal_contributions",
    "yellow_cards", "red_cards",
    "goals_per90", "assists_per90", "goal_contributions_per90",
    "shots", "key_passes", "xg", "xa",
    "shots_per90", "key_passes_per90", "xg_per90", "xa_per90",
)

# Raw season totals surfaced on the profile ("base numbers"), in display order.
# xG/Shots show only for Big-5 league players (null -> "—" elsewhere).
SEASON_TOTALS: tuple[tuple[str, str], ...] = (
    ("matches", "Matches"), ("minutes", "Minutes"), ("goals", "Goals"),
    ("assists", "Assists"), ("goal_contributions", "G+A"),
    ("xg", "xG"), ("shots", "Shots"), ("key_passes", "Key passes"),
)


def club_logo(club_id: int | str | None) -> str | None:
    """Transfermarkt club crest URL from a club id."""
    if club_id in (None, "", "nan"):
        return None
    try:
        return f"https://tmssl.akamaized.net/images/wappen/head/{int(float(club_id))}.png"
    except (ValueError, TypeError):
        return None


class Player(BaseModel):
    """A player's line in one competition."""
    row_id: str
    player_id: str
    name: str
    photo: str | None = None
    position: str            # broad: Forward / Midfielder / Defender / Goalkeeper
    role: str                # detailed: Winger, Centre-Forward, Full-back, ...
    age: int | None = None
    nation: str | None = None
    height_cm: int | None = None
    foot: str | None = None
    club: str
    club_id: int | None = None
    competition: str         # e.g. "Premier League", "UEFA Champions League"
    competition_id: str
    competition_type: str    # League / Domestic Cup / Continental / International / Other
    country: str             # league country, or "International"
    confederation: str | None = None
    market_value_eur: float | None = None
    metrics: dict[str, float | None] = {}

    def metric(self, key: str) -> float | None:
        if key == "market_value_eur":
            return self.market_value_eur
        return self.metrics.get(key)

    @property
    def club_logo(self) -> str | None:
        return club_logo(self.club_id)


class Club(BaseModel):
    club_id: int
    name: str
    logo: str | None = None
    competition: str | None = None
    country: str | None = None
    squad_value: float | None = None
    squad_size: int | None = None
    avg_age: float | None = None
    foreigners_number: int | None = None
    stadium: str | None = None
    stadium_seats: int | None = None
    coach: str | None = None


class Competition(BaseModel):
    competition_id: str
    competition: str
    type: str
    country: str
    confederation: str | None = None
    flag: str | None = None
