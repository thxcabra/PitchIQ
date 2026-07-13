"""Views 1 & 2: player search and individual profile."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import Services, get_services
from app.models.responses import (
    CompetitionLine, MetricContext, MetricHighlight, PlayerProfile, PlayerSummary,
    SearchResponse, SeasonTotal,
)
from app.services.ranking_service import RankingFilters

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/search", response_model=SearchResponse)
def search_players(
    q: str = Query("", description="Name query (optional if filters are given)"),
    position: str | None = Query(None),
    role: str | None = Query(None),
    competition: str | None = Query(None),
    country: str | None = Query(None),
    club: str | None = Query(None),
    limit: int = Query(60, ge=1, le=120),
    svc: Services = Depends(get_services),
) -> SearchResponse:
    filters = None
    if any([position, role, competition, country, club]):
        filters = RankingFilters(position=position, role=role, competition=competition,
                                 country=country, club=club)
    if not q and filters is None:
        return SearchResponse(query=q, count=0, total=0, results=[])
    results, total = svc.search.search(q, filters=filters, limit=limit)
    return SearchResponse(
        query=q, count=len(results), total=total,
        results=[PlayerSummary.of(p) for p in results],
    )


@router.get("/{player_id}", response_model=PlayerSummary)
def get_player(player_id: str, svc: Services = Depends(get_services)) -> PlayerSummary:
    player = svc.repo.primary_row(player_id)
    if player is None:
        raise HTTPException(status_code=404, detail=f"Player '{player_id}' not found")
    return PlayerSummary.of(player)


@router.get("/{player_id}/profile", response_model=PlayerProfile)
def get_profile(player_id: str, svc: Services = Depends(get_services)) -> PlayerProfile:
    player = svc.repo.primary_row(player_id)
    if player is None:
        raise HTTPException(status_code=404, detail=f"Player '{player_id}' not found")
    p = svc.stats.profile(player)
    return PlayerProfile(
        player=PlayerSummary.of(player),
        cohort_label=p["cohort_label"],
        cohort_size=p["cohort_size"],
        rating=p["rating"],
        strengths=[MetricHighlight(**s) for s in p["strengths"]],
        weaknesses=[MetricHighlight(**w) for w in p["weaknesses"]],
        totals=[SeasonTotal(**t) for t in p["totals"]],
        metrics=[MetricContext(**row) for row in p["metrics"]],
        breakdown=[CompetitionLine(**b) for b in p["breakdown"]],
        similar=[PlayerSummary.of(sp) for sp in p["similar"]],
    )
