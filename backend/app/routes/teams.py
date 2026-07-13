"""Team (club) profiles."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import Services, get_services
from app.models.responses import (
    ClubInfo, ClubResult, PlayerSummary, SquadMember, TeamProfile,
)

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/search", response_model=list[ClubResult])
def search_teams(q: str = Query(..., min_length=1), svc: Services = Depends(get_services)):
    return [ClubResult(club_id=c.club_id, name=c.name, logo=c.logo,
                       competition=c.competition, country=c.country)
            for c in svc.team.search(q)]


@router.get("/{club_id}", response_model=TeamProfile)
def get_team(club_id: int, svc: Services = Depends(get_services)) -> TeamProfile:
    p = svc.team.profile(club_id)
    if p is None:
        raise HTTPException(status_code=404, detail=f"Club '{club_id}' not found")
    c = p["club"]

    def member(s: dict) -> SquadMember:
        return SquadMember(player=PlayerSummary.of(s["player"]), goals=s["goals"],
                           assists=s["assists"], minutes=s["minutes"], matches=s["matches"])

    return TeamProfile(
        club=ClubInfo(**c.model_dump()),
        squad_count=p["squad_count"], total_goals=p["total_goals"], competitions=p["competitions"],
        top_scorer=member(p["top_scorer"]) if p["top_scorer"] else None,
        squad=[member(s) for s in p["squad"]],
    )
