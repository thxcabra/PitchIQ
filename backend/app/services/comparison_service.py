"""Two-player comparison: per-metric values, percentiles, winners, and market context."""
from __future__ import annotations

from app.metrics import METRICS, radar_metrics
from app.models.domain import Player
from app.services.stats_service import StatsService


class ComparisonService:
    def __init__(self, stats: StatsService):
        self._stats = stats

    def compare(self, a: Player, b: Player, metrics: list[str] | None = None) -> dict:
        # union of both players' role-appropriate radar metrics keeps it fair across positions
        if metrics is None:
            metrics = list(dict.fromkeys(radar_metrics(a) + radar_metrics(b)))

        rows = []
        wins = {"a": 0, "b": 0}
        for m in metrics:
            va, vb = a.metric(m), b.metric(m)
            pa = self._stats.percentile(a, m)
            pb = self._stats.percentile(b, m)
            higher_better = METRICS[m].higher_is_better if m in METRICS else True
            winner = None
            if va is not None and vb is not None and va != vb:
                a_better = va > vb if higher_better else va < vb
                winner = "a" if a_better else "b"
                wins["a" if a_better else "b"] += 1
            rows.append({
                "metric": m,
                "label": METRICS[m].label if m in METRICS else m,
                "a_value": va, "b_value": vb,
                "a_percentile": pa, "b_percentile": pb,
                "winner": winner,
            })

        overall = "a" if wins["a"] > wins["b"] else "b" if wins["b"] > wins["a"] else "tie"
        return {
            "player_a": a,
            "player_b": b,
            "metrics": rows,
            "wins": wins,
            "overall_winner": overall,
            "market_context": {
                "a": {"market_value_eur": a.market_value_eur,
                      "value_percentile": self._stats.percentile(a, "market_value_eur")},
                "b": {"market_value_eur": b.market_value_eur,
                      "value_percentile": self._stats.percentile(b, "market_value_eur")},
            },
        }
