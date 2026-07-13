"""
Composition root. Builds the repository and services once and exposes them as FastAPI
dependencies. Endpoints depend on these; they never construct services themselves.
"""
from __future__ import annotations

from functools import lru_cache

from app.config import settings
from app.data.repository import PlayerRepository
from app.services.comparison_service import ComparisonService
from app.services.competition_service import CompetitionService
from app.services.ranking_service import RankingService
from app.services.search_service import SearchService
from app.services.stats_service import StatsService
from app.services.team_service import TeamService


class Services:
    def __init__(self, csv_path: str):
        self.repo = PlayerRepository(csv_path)
        self.stats = StatsService(self.repo)
        self.ranking = RankingService(self.repo)
        self.search = SearchService(self.repo, self.ranking)
        self.comparison = ComparisonService(self.stats)
        self.team = TeamService(self.repo)
        self.competition = CompetitionService(self.repo)


@lru_cache(maxsize=1)
def get_services() -> Services:
    return Services(settings.csv_path)
