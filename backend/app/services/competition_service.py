"""Competition profiles: metadata + top players + participating clubs. Reuses the repository."""
from __future__ import annotations

from app.data.repository import PlayerRepository
from app.models.domain import Competition, club_logo


class CompetitionService:
    def __init__(self, repo: PlayerRepository):
        self._repo = repo

    def list(self) -> list[Competition]:
        return sorted(self._repo.competitions_meta(),
                      key=lambda c: (c.type != "League", c.competition))

    def profile(self, competition: str, top: int = 8) -> dict | None:
        rows = self._repo.rows_for_competition(competition)
        if not rows:
            return None
        meta = self._repo.competition_meta(competition) or Competition(
            competition_id="", competition=competition, type=rows[0].competition_type,
            country=rows[0].country)

        top_scorers = sorted(rows, key=lambda r: r.metric("goals") or 0, reverse=True)[:top]
        top_value = sorted(rows, key=lambda r: r.market_value_eur or 0, reverse=True)[:top]

        clubs: dict[int, dict] = {}
        for r in rows:
            if r.club_id is None:
                continue
            c = clubs.setdefault(r.club_id, {"club_id": r.club_id, "name": r.club,
                                             "logo": club_logo(r.club_id), "goals": 0})
            c["goals"] += r.metric("goals") or 0
        club_list = sorted(clubs.values(), key=lambda c: c["goals"], reverse=True)

        return {
            "competition": meta,
            "player_count": len({r.player_id for r in rows}),
            "club_count": len(clubs),
            "total_goals": sum(r.metric("goals") or 0 for r in rows),
            "top_scorers": top_scorers,
            "top_value": top_value,
            "clubs": club_list,
        }
