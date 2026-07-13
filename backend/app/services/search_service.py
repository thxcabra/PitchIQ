"""Name search + filtering + entity resolution. Reused by View 1 and the NLU layer."""
from __future__ import annotations

import difflib

from app.data.repository import PlayerRepository, normalize
from app.models.domain import Player
from app.services.ranking_service import RankingFilters, RankingService


class SearchService:
    def __init__(self, repo: PlayerRepository, ranking: RankingService):
        self._repo = repo
        self._ranking = ranking
        # search operates over one headline row per person
        self._primaries = repo.players()
        self._index = [(normalize(p.name), p) for p in self._primaries]
        self._primary_by_player = {p.player_id: p for p in self._primaries}

    def _scored(self, query: str) -> list[tuple[float, bool, Player]]:
        q = normalize(query)
        if not q:
            return []
        out: list[tuple[float, bool, Player]] = []
        for norm, player in self._index:
            words = norm.split()
            if q == norm:
                out.append((115.0, True, player))
            elif q in words:
                out.append((95.0, True, player))
            elif q in norm:
                out.append((78.0 - norm.index(q) * 0.05, True, player))
            else:
                ratio = max([difflib.SequenceMatcher(None, q, norm).ratio()]
                            + [difflib.SequenceMatcher(None, q, w).ratio() for w in words])
                if ratio >= 0.6:
                    out.append((ratio * 60, False, player))

        def prominence(p: Player) -> tuple[float, float]:
            # tie-break same-name matches by market value, then minutes (Mbappe -> Kylian)
            return (p.market_value_eur or 0.0, p.metric("minutes") or 0.0)

        out.sort(key=lambda x: (-x[0], -prominence(x[2])[0], -prominence(x[2])[1], x[2].name))
        return out

    def search(self, query: str = "", filters: RankingFilters | None = None,
               limit: int = 30) -> tuple[list[Player], int]:
        """
        Name query and/or structured filters (position, competition, country, club...).
        Returns (page, total) so the UI can show "showing N of M".
        """
        allow: set[str] | None = None
        if filters is not None:
            allow = {r.player_id for r in self._ranking.filter(filters)}

        if query.strip():
            scored = self._scored(query)
            subs = [x for x in scored if x[1]]   # prefer substring matches over fuzzy
            chosen = subs if subs else scored
            results = [p for _, _, p in chosen if allow is None or p.player_id in allow]
        elif allow is not None:
            results = [self._primary_by_player[pid] for pid in allow]
            results.sort(key=lambda p: -(p.metric("minutes") or 0))
        else:
            results = sorted(self._primaries, key=lambda p: -(p.metric("minutes") or 0))
        return results[:limit], len(results)

    def resolve(self, name: str, min_score: float = 50.0) -> Player | None:
        """Best single person for a name the NLU extracted (typo-tolerant; None if absent)."""
        scored = self._scored(name)
        if scored and scored[0][0] >= min_score:
            return scored[0][2]
        return None

    def suggestions(self, name: str, limit: int = 3) -> list[str]:
        return [p.name for _, _, p in self._scored(name)[:limit]]
