"""Filtering + ranking over player-competition rows (View 1 search power + NLU ranking)."""
from __future__ import annotations

from dataclasses import dataclass

from app.data.repository import PlayerRepository, normalize
from app.metrics import METRICS
from app.models.domain import Player


@dataclass
class RankingFilters:
    competition: str | None = None    # e.g. "Premier League", "UEFA Champions League"
    country: str | None = None        # league country, e.g. "Italy"
    competition_type: str | None = None  # League / Domestic Cup / Continental / International
    confederation: str | None = None
    club: str | None = None
    position: str | None = None       # broad
    role: str | None = None           # detailed
    nation: str | None = None
    min_age: int | None = None
    max_age: int | None = None
    min_minutes: int | None = None

    def describe(self) -> str:
        parts = []
        if self.max_age is not None:
            parts.append(f"under {self.max_age + 1}")
        if self.min_age is not None:
            parts.append(f"over {self.min_age - 1}")
        if self.role:
            parts.append(self.role.lower() + "s")
        elif self.position:
            parts.append(self.position.lower() + "s")
        else:
            parts.append("players")
        if self.club:
            parts.append(f"at {self.club}")
        if self.nation:
            parts.append(f"from {self.nation}")
        if self.competition:
            parts.append(f"in the {self.competition}")
        elif self.country:
            parts.append(f"in {self.country}")
        elif self.competition_type:
            parts.append(f"in {self.competition_type.lower()} competitions")
        return " ".join(parts)


class RankingService:
    def __init__(self, repo: PlayerRepository):
        self._repo = repo

    def _match(self, p: Player, f: RankingFilters) -> bool:
        n = normalize
        if f.competition and n(p.competition) != n(f.competition):
            return False
        if f.country and n(p.country) != n(f.country):
            return False
        if f.competition_type and n(p.competition_type) != n(f.competition_type):
            return False
        if f.confederation and n(p.confederation or "") != n(f.confederation):
            return False
        if f.club and n(f.club) not in n(p.club):
            return False
        if f.role:
            if n(p.role) != n(f.role):
                return False
        elif f.position and n(p.position) != n(f.position):
            return False
        if f.nation and n(p.nation or "") != n(f.nation):
            return False
        if f.min_age is not None and (p.age is None or p.age < f.min_age):
            return False
        if f.max_age is not None and (p.age is None or p.age > f.max_age):
            return False
        if f.min_minutes is not None and (p.metric("minutes") or 0) < f.min_minutes:
            return False
        return True

    def filter(self, f: RankingFilters) -> list[Player]:
        return [p for p in self._repo.all() if self._match(p, f)]

    def rank(self, metric: str, filters: RankingFilters, limit: int = 5,
             ascending: bool | None = None) -> list[Player]:
        pool = self.filter(filters)
        meta = METRICS.get(metric)
        higher_is_better = meta.higher_is_better if meta else True
        reverse = higher_is_better if ascending is None else (not ascending)
        ranked = [p for p in pool if p.metric(metric) is not None]
        ranked.sort(key=lambda p: p.metric(metric), reverse=reverse)
        return ranked[:limit]
