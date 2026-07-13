"""Percentiles, cohort averages, and the player profile (radar, strengths, similar players)."""
from __future__ import annotations

from statistics import mean, pstdev

from app.data.repository import PlayerRepository
from app.metrics import METRICS, radar_metrics
from app.models.domain import SEASON_TOTALS, Player


class StatsService:
    def __init__(self, repo: PlayerRepository):
        self._repo = repo

    def percentile(self, row: Player, metric: str, cohort: list[Player] | None = None) -> float | None:
        """
        Percentile rank (0-100) of a player-competition row for `metric`, within its
        position+competition cohort. Lower-is-better metrics invert.
        """
        cohort = cohort if cohort is not None else self._repo.cohort(row.position, row.competition)
        values = [p.metric(metric) for p in cohort]
        values = [v for v in values if v is not None]
        target = row.metric(metric)
        if target is None or len(values) < 2:
            return None
        pct = 100.0 * sum(1 for v in values if v <= target) / len(values)
        meta = METRICS.get(metric)
        if meta and not meta.higher_is_better:
            pct = 100.0 - pct
        return round(pct, 1)

    def cohort_average(self, position: str, competition: str, metric: str) -> float | None:
        values = [p.metric(metric) for p in self._repo.cohort(position, competition)]
        values = [v for v in values if v is not None]
        return round(mean(values), 3) if values else None

    def profile(self, primary: Player, metrics: list[str] | None = None) -> dict:
        """
        View 2: contextualised radar for the player's main competition, PLUS season totals
        aggregated across every competition they played, PLUS a per-competition breakdown.
        """
        metrics = metrics or radar_metrics(primary)
        cohort = self._repo.cohort(primary.position, primary.competition)
        rows = [{
            "metric": m,
            "label": METRICS[m].label if m in METRICS else m,
            "value": primary.metric(m),
            "cohort_average": self.cohort_average(primary.position, primary.competition, m),
            "percentile": self.percentile(primary, m, cohort),
        } for m in metrics]

        all_rows = self._repo.player_rows(primary.player_id)
        totals = []
        for key, label in SEASON_TOTALS:
            vals = [r.metric(key) for r in all_rows if r.metric(key) is not None]
            totals.append({"key": key, "label": label, "value": sum(vals) if vals else None})

        breakdown = [{
            "competition": r.competition,
            "competition_type": r.competition_type,
            "club": r.club,
            "matches": r.metric("matches"),
            "minutes": r.metric("minutes"),
            "goals": r.metric("goals"),
            "assists": r.metric("assists"),
        } for r in sorted(all_rows, key=lambda r: -(r.metric("minutes") or 0))]

        # --- flavour: rating, strengths/weaknesses, similar players ------------
        pcts = [r["percentile"] for r in rows if r["percentile"] is not None]
        rating = round(mean(pcts)) if pcts else None
        strengths = sorted([r for r in rows if (r["percentile"] or 0) >= 70],
                           key=lambda r: -r["percentile"])[:3]
        weaknesses = sorted([r for r in rows if r["percentile"] is not None and r["percentile"] <= 35],
                            key=lambda r: r["percentile"])[:3]
        similar = self.similar_players(primary, cohort, metrics)

        return {
            "player": primary,
            "cohort_size": len(cohort),
            "cohort_label": f"{primary.position}s in {primary.competition}",
            "rating": rating,
            "strengths": [{"label": s["label"], "percentile": s["percentile"]} for s in strengths],
            "weaknesses": [{"label": w["label"], "percentile": w["percentile"]} for w in weaknesses],
            "totals": totals,
            "metrics": rows,
            "breakdown": breakdown,
            "similar": similar,
        }

    def similar_players(self, target: Player, cohort: list[Player],
                        metrics: list[str], k: int = 4) -> list[Player]:
        """Nearest players in the same cohort by z-normalised metric profile."""
        pool = [p for p in cohort if p.player_id != target.player_id]
        if len(pool) < 2:
            return []
        stats: dict[str, tuple[float, float]] = {}
        for m in metrics:
            vals = [p.metric(m) for p in cohort if p.metric(m) is not None]
            if len(vals) >= 2:
                sd = pstdev(vals)
                stats[m] = (mean(vals), sd if sd else 1.0)

        def vec(p: Player) -> list[float]:
            return [((p.metric(m) or mu) - mu) / sd for m, (mu, sd) in stats.items()]

        tv = vec(target)
        scored = [(sum((a - b) ** 2 for a, b in zip(tv, vec(p))), p) for p in pool]
        scored.sort(key=lambda x: x[0])
        return [p for _, p in scored[:k]]
