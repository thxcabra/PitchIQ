"""Core business-logic tests: percentiles, cohort averages, filtering, ranking."""
from __future__ import annotations

from app.services.ranking_service import RankingFilters, RankingService
from app.services.stats_service import StatsService


def test_percentile_top_and_bottom(sample_repo):
    stats = StatsService(sample_repo)
    top = sample_repo.get_row("f4")     # goals_per90 = 0.5 (highest of 5)
    bottom = sample_repo.get_row("f0")  # goals_per90 = 0.1 (lowest of 5)
    assert stats.percentile(top, "goals_per90") == 100.0
    assert stats.percentile(bottom, "goals_per90") == 20.0  # 1 of 5 at-or-below


def test_percentile_is_cohort_scoped(sample_repo):
    # The lone midfielder has a huge goals_per90 but must NOT affect the forwards' cohort.
    stats = StatsService(sample_repo)
    mid = sample_repo.get_row("f2")     # goals_per90 = 0.3, 3rd of 5 forwards
    assert stats.percentile(mid, "goals_per90") == 60.0


def test_cohort_average(sample_repo):
    stats = StatsService(sample_repo)
    # forwards goals_per90 = 0.1..0.5 -> mean 0.3
    assert stats.cohort_average("Forward", "Test League", "goals_per90") == 0.3


def test_lower_is_better_metric_inverts_percentile(sample_repo, monkeypatch):
    # flip a metric to prove the inversion path works.
    from app import metrics
    stats = StatsService(sample_repo)
    monkeypatch.setitem(metrics.METRICS, "goals_per90",
                        metrics.Metric("goals_per90", "Goals /90", higher_is_better=False))
    top_scorer = sample_repo.get_row("f4")  # highest goals -> now WORST -> 0th percentile
    bottom_scorer = sample_repo.get_row("f0")  # lowest goals -> now BEST
    assert stats.percentile(top_scorer, "goals_per90") == 0.0
    assert stats.percentile(bottom_scorer, "goals_per90") == 80.0


def test_ranking_orders_and_filters(sample_repo):
    ranking = RankingService(sample_repo)
    top3 = ranking.rank("goals_per90", RankingFilters(position="Forward"), limit=3)
    assert [p.player_id for p in top3] == ["f4", "f3", "f2"]


def test_ranking_age_and_competition_filter(sample_repo):
    ranking = RankingService(sample_repo)
    # under 23 => age <= 22 => f0(20), f1(21), f2(22)
    res = ranking.rank("goals_per90", RankingFilters(competition="Test League", max_age=22), limit=10)
    assert {p.player_id for p in res} == {"f0", "f1", "f2"}
    assert res[0].player_id == "f2"  # highest goals among the under-23s


def test_ranking_ascending(sample_repo):
    ranking = RankingService(sample_repo)
    worst = ranking.rank("goals_per90", RankingFilters(position="Forward"), limit=1, ascending=True)
    assert worst[0].player_id == "f0"
