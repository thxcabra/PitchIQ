"""
Query execution: a StructuredQuery -> a ChatResponse.

Dispatches on intent and calls the same services the REST views use (search, ranking,
stats, comparison), packing their output into the discriminated-union response.
"""
from __future__ import annotations

from app.deps import Services
from app.metrics import METRICS, radar_metrics
from app.models.responses import (
    ChartResponse, ChartSeries, ClarificationOption, ClarificationResponse, Column,
    ComparisonResponse, ComparisonResult, ErrorResponse, PlayerSummary, QueryTrace,
    TableResponse, TextResponse,
)
from app.nlu.query_models import StructuredQuery
from app.services.ranking_service import RankingFilters

_EXAMPLES = [
    "Top 5 scorers in the Champions League",
    "Best young wingers in Serie A by goals per 90",
    "Compare Haaland and Mbappe",
]


class ChatExecutor:
    def __init__(self, services: Services):
        self._svc = services

    def execute(self, sq: StructuredQuery):
        trace = self._trace(sq)
        handler = {
            "ranking": self._ranking,
            "lookup": self._lookup,
            "comparison": self._comparison,
            "ambiguous": self._ambiguous,
            "out_of_scope": self._out_of_scope,
        }[sq.intent]
        return handler(sq, trace)

    # --- trace ----------------------------------------------------------------
    def _trace(self, sq: StructuredQuery) -> QueryTrace:
        filters = {k: v for k, v in sq.filters.model_dump().items() if v is not None}
        if sq.limit:
            filters["limit"] = sq.limit
        return QueryTrace(
            intent=sq.intent, provider=sq.provider, metric=sq.metric,
            entities=sq.entities, filters=filters, notes=sq.notes,
        )

    # --- intents --------------------------------------------------------------
    def _ranking(self, sq: StructuredQuery, trace: QueryTrace):
        metric = sq.metric or "goals_per90"
        f = sq.filters
        rf = RankingFilters(**f.model_dump())
        limit = sq.limit or 5
        players = self._svc.ranking.rank(metric, rf, limit=limit, ascending=sq.ascending)
        label = METRICS[metric].label if metric in METRICS else metric
        is_money = metric == "market_value_eur"

        if not players:
            return TextResponse(
                title="No matches", trace=trace,
                text=f"No players matched {rf.describe()}. Try loosening the filters.",
            )
        # show the competition column only when the query spans competitions
        single_comp = bool(f.competition)
        rows = [{
            "rank": i + 1, "player_id": p.player_id, "name": p.name, "club": p.club,
            "competition": p.competition, "age": p.age, "position": p.role,
            "matches": p.metric("matches"), "goals": p.metric("goals"),
            "value": p.metric(metric),
            "market_value_eur": p.market_value_eur,
        } for i, p in enumerate(players)]
        columns = [
            Column(key="rank", label="#", kind="number"),
            Column(key="name", label="Player"),
            Column(key="club", label="Club"),
        ]
        if not single_comp:
            columns.append(Column(key="competition", label="Competition"))
        columns += [
            Column(key="age", label="Age", kind="number"),
            Column(key="matches", label="Games", kind="number"),
            Column(key="value", label=label, kind="money" if is_money else "number"),
        ]
        if metric not in ("market_value_eur", "matches"):
            columns.append(Column(key="market_value_eur", label="Market value", kind="money"))
        order = "lowest" if sq.ascending else "top"
        return TableResponse(
            title=f"{order.capitalize()} {len(players)} by {label}",
            columns=columns, rows=rows, trace=trace,
            narrative=f"{order.capitalize()} {rf.describe()} ranked by {label}. "
                      f"Leader: {players[0].name} ({players[0].club}).",
        )

    def _lookup(self, sq: StructuredQuery, trace: QueryTrace):
        player = self._svc.search.resolve(sq.entities[0]) if sq.entities else None
        if player is None:
            name = sq.entities[0] if sq.entities else ""
            return ErrorResponse(
                message=f"I couldn't find a player called \"{name}\".",
                suggestions=self._svc.search.suggestions(name), trace=trace,
            )
        metrics = radar_metrics(player)
        cohort_label = f"{player.position}s in {player.competition}"
        profile = self._svc.stats.profile(player, metrics)
        categories = [r["label"] for r in profile["metrics"]]
        pct_series = [r["percentile"] for r in profile["metrics"]]
        standout = max(profile["metrics"], key=lambda r: (r["percentile"] or 0))
        return ChartResponse(
            chart_type="radar",
            title=f"{player.name} vs average {player.position.lower()} in {player.competition}",
            categories=categories,
            series=[ChartSeries(name=player.name, values=pct_series)],
            value_kind="percentile",
            narrative=(f"{player.name} ({player.club}) benchmarked against {profile['cohort_size']} "
                       f"{cohort_label}. Strongest area: {standout['label']} "
                       f"({_ordinal(standout['percentile'])} percentile)."),
            footnote="Percentile within position & league. 50 = league-average for the position.",
            trace=trace,
        )

    def _comparison(self, sq: StructuredQuery, trace: QueryTrace):
        if len(sq.entities) < 2:
            return self._ambiguous(sq, trace)
        a = self._svc.search.resolve(sq.entities[0])
        b = self._svc.search.resolve(sq.entities[1])
        missing = [sq.entities[i] for i, p in enumerate((a, b)) if p is None]
        if missing:
            sugg = []
            for m in missing:
                sugg += self._svc.search.suggestions(m)
            return ErrorResponse(
                message=f"I couldn't find: {', '.join(missing)}.",
                suggestions=list(dict.fromkeys(sugg)), trace=trace,
            )
        result = self._svc.comparison.compare(a, b)
        winner = {"a": a, "b": b}.get(result["overall_winner"])
        narrative = (
            f"{a.name} vs {b.name}: "
            + (f"{winner.name} leads on more metrics "
               f"({result['wins'][result['overall_winner']]} to "
               f"{result['wins']['b' if result['overall_winner'] == 'a' else 'a']})."
               if winner else "an even split across metrics.")
        )
        return ComparisonResponse(
            title=f"{a.name} vs {b.name}",
            data=ComparisonResult(
                player_a=PlayerSummary.of(a), player_b=PlayerSummary.of(b),
                metrics=result["metrics"], wins=result["wins"],
                overall_winner=result["overall_winner"], market_context=result["market_context"],
            ),
            narrative=narrative, trace=trace,
        )

    def _ambiguous(self, sq: StructuredQuery, trace: QueryTrace):
        f = sq.filters
        scope = ""
        if f.role:
            scope = f" {f.role.lower()}s"
        elif f.position:
            scope = f" {f.position.lower()}s"
        loc = f" in the {f.competition}" if f.competition else f" in {f.country}" if f.country else ""
        base = f"top 5{scope}{loc} by"
        options = [
            ClarificationOption(label="Goals", query=f"{base} goals"),
            ClarificationOption(label="Assists", query=f"{base} assists"),
            ClarificationOption(label="Goals + Assists", query=f"{base} goal contributions"),
            ClarificationOption(label="Market value", query=f"{base} market value"),
        ]
        msg = sq.notes or "That could mean a few things — best by which metric?"
        return ClarificationResponse(message=msg, options=options, trace=trace)

    def _out_of_scope(self, sq: StructuredQuery, trace: QueryTrace):
        bullets = "\n".join(f"• {e}" for e in _EXAMPLES)
        prefix = f"{sq.notes} " if sq.notes else ""
        return TextResponse(
            title="Outside my coverage",
            text=(prefix + "I answer questions about 2025-26 European football — 14 leagues, domestic "
                  "cups, the Champions/Europa League, the World Cup and AFCON — rankings, "
                  "player profiles, and head-to-head comparisons. Try:\n" + bullets),
            trace=trace,
        )


def _ordinal(n: float | None) -> str:
    if n is None:
        return "n/a"
    n = int(round(n))
    suffix = "th" if 11 <= n % 100 <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"
