"""
Central metric catalog: the closed set of metrics a query can name.

Totals and per-90s from Transfermarkt appearances, plus xG/xA/shots/key passes for
Big-5 league rows (Understat). `resolve_metric` maps free text (EN + PT) to a metric key.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from app.text import deaccent

if TYPE_CHECKING:
    from app.models.domain import Player


@dataclass(frozen=True)
class Metric:
    key: str
    label: str
    unit: str = ""
    higher_is_better: bool = True
    aliases: tuple[str, ...] = field(default_factory=tuple)


METRICS: dict[str, Metric] = {m.key: m for m in [
    # per-90 rates
    Metric("goals_per90", "Goals /90", "per 90",
           aliases=("goals per 90", "goals/90", "g/90", "scoring rate")),
    Metric("assists_per90", "Assists /90", "per 90",
           aliases=("assists per 90", "assists/90", "a/90", "assist rate")),
    Metric("goal_contributions_per90", "G+A /90", "per 90",
           aliases=("goal contributions per 90", "g+a per 90", "contributions per 90")),
    # Understat-enriched rates (Big-5 leagues only)
    Metric("xg_per90", "xG /90", "per 90", aliases=("xg per 90", "expected goals per 90")),
    Metric("xa_per90", "xA /90", "per 90", aliases=("xa per 90", "expected assists per 90")),
    Metric("shots_per90", "Shots /90", "per 90", aliases=("shots per 90", "shot volume")),
    Metric("key_passes_per90", "Key passes /90", "per 90",
           aliases=("key passes per 90", "chances created", "chance creation")),
    # season totals (base numbers, also rankable)
    Metric("goals", "Goals", "total",
           aliases=("goals", "goal", "scorer", "scorers", "goalscorer", "goalscorers",
                    "total goals", "most goals",
                    "gols", "gol", "artilheiro", "artilheiros", "artilharia", "goleador")),
    Metric("assists", "Assists", "total",
           aliases=("assists", "assist", "total assists", "most assists", "creator", "creators",
                    "assistencias", "assistencia", "garcom", "garcons")),
    Metric("goal_contributions", "Goals + Assists", "total",
           aliases=("goal contributions", "g+a", "goals and assists", "contributions",
                    "participacoes", "participacoes em gols", "gols e assistencias")),
    Metric("xg", "xG", "total", aliases=("xg", "expected goals")),
    Metric("shots", "Shots", "total", aliases=("shots", "total shots", "chutes", "finalizacoes")),
    Metric("key_passes", "Key passes", "total", aliases=("key passes", "passes decisivos")),
    Metric("matches", "Matches", "total",
           aliases=("matches", "games", "appearances", "most games", "jogos", "partidas")),
    Metric("minutes", "Minutes", "total",
           aliases=("minutes", "most minutes", "game time", "minutos")),
    Metric("yellow_cards", "Yellow cards", "total", higher_is_better=False,
           aliases=("yellow cards", "yellows", "bookings", "cartoes amarelos", "amarelos")),
    Metric("red_cards", "Red cards", "total", higher_is_better=False,
           aliases=("red cards", "reds", "sendings off", "cartoes vermelhos", "vermelhos")),
    # market
    Metric("market_value_eur", "Market value", "€",
           aliases=("market value", "value", "worth", "price", "cost", "expensive",
                    "valor de mercado", "valor", "mais caros", "mais valiosos")),
]}

# Rich radar for Big-5 league players (have Understat xG/shots/key passes).
RICH_RADAR = ["goals_per90", "xg_per90", "shots_per90", "assists_per90",
              "key_passes_per90", "goal_contributions_per90"]
# Thin radar for everyone else (cups, continental, non-Big-5 leagues).
THIN_RADAR = ["goals_per90", "assists_per90", "goal_contributions_per90", "minutes", "matches"]


def radar_metrics(player: "Player") -> list[str]:
    """Rich xG radar for Big-5 league rows (which carry Understat data), else the thin one."""
    return RICH_RADAR if player.metric("xg") is not None else THIN_RADAR


def resolve_metric(text: str) -> str | None:
    """Map a free-text phrase to a metric key (accent-insensitive, EN + PT)."""
    if not text:
        return None
    t = deaccent(text.strip().lower())
    if t in METRICS:
        return t
    for m in METRICS.values():
        if t == m.label.lower() or t in m.aliases:
            return m.key
    best: tuple[int, str] | None = None
    for m in METRICS.values():
        for alias in (m.label.lower(), *m.aliases):
            if alias in t and (best is None or len(alias) > best[0]):
                best = (len(alias), m.key)
    return best[1] if best else None
