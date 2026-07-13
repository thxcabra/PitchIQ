"""Team (club) profiles: club metadata + aggregated squad. Reuses the repository."""
from __future__ import annotations

import difflib

from app.data.repository import PlayerRepository, normalize
from app.models.domain import Club, Player


class TeamService:
    def __init__(self, repo: PlayerRepository):
        self._repo = repo

    def search(self, query: str, limit: int = 12) -> list[Club]:
        q = normalize(query)
        if not q:
            return []
        scored: list[tuple[float, Club]] = []
        for c in self._repo.clubs_meta():
            n = normalize(c.name)
            if q in n:
                scored.append((100 - n.index(q), c))
            else:
                ratio = difflib.SequenceMatcher(None, q, n).ratio()
                if ratio >= 0.6:
                    scored.append((ratio * 50, c))
        scored.sort(key=lambda x: (-x[0], x[1].name))
        return [c for _, c in scored[:limit]]

    def profile(self, club_id: int) -> dict | None:
        club = self._repo.club(club_id)
        rows = self._repo.rows_for_club(club_id)
        if not rows:
            return None
        if club is None:  # fall back to a minimal club built from the rows
            club = Club(club_id=club_id, name=rows[0].club)

        # keep only players whose PRIMARY club (most total minutes) is this one, so a
        # one-off cup cameo for another club doesn't put them in this squad.
        by_player: dict[str, list[Player]] = {}
        for r in rows:
            if self._repo.primary_club(r.player_id) == club_id:
                by_player.setdefault(r.player_id, []).append(r)
        if not by_player:  # fallback: everyone with a row here
            for r in rows:
                by_player.setdefault(r.player_id, []).append(r)

        squad = []
        for prs in by_player.values():
            primary = max(prs, key=lambda r: r.metric("minutes") or 0)
            squad.append({
                "player": primary,
                "goals": sum(r.metric("goals") or 0 for r in prs),
                "assists": sum(r.metric("assists") or 0 for r in prs),
                "minutes": sum(r.metric("minutes") or 0 for r in prs),
                "matches": sum(r.metric("matches") or 0 for r in prs),
            })
        squad.sort(key=lambda s: (s["player"].market_value_eur or 0, s["goals"]), reverse=True)

        competitions = sorted({r.competition for r in rows})
        total_goals = sum(s["goals"] for s in squad)
        top_scorer = max(squad, key=lambda s: s["goals"]) if squad else None
        return {
            "club": club,
            "squad_count": len(squad),
            "total_goals": total_goals,
            "top_scorer": top_scorer,
            "competitions": competitions,
            "squad": squad,
        }
