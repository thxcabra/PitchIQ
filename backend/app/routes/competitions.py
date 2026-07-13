"""Competition profiles."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.deps import Services, get_services
from app.models.responses import (
    CompetitionClub, CompetitionInfo, CompetitionProfile, PlayerSummary,
)

router = APIRouter(prefix="/competitions", tags=["competitions"])


@router.get("", response_model=list[CompetitionInfo])
def list_competitions(svc: Services = Depends(get_services)):
    return [CompetitionInfo(**c.model_dump()) for c in svc.competition.list()]


@router.get("/{name}", response_model=CompetitionProfile)
def get_competition(name: str, svc: Services = Depends(get_services)) -> CompetitionProfile:
    p = svc.competition.profile(name)
    if p is None:
        raise HTTPException(status_code=404, detail=f"Competition '{name}' not found")
    return CompetitionProfile(
        competition=CompetitionInfo(**p["competition"].model_dump()),
        player_count=p["player_count"], club_count=p["club_count"], total_goals=p["total_goals"],
        top_scorers=[PlayerSummary.of(r) for r in p["top_scorers"]],
        top_value=[PlayerSummary.of(r) for r in p["top_value"]],
        clubs=[CompetitionClub(**c) for c in p["clubs"]],
    )
