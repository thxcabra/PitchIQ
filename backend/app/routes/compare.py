"""View 3: two-player comparison."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import Services, get_services
from app.models.responses import ComparisonResult, PlayerSummary

router = APIRouter(tags=["comparison"])


@router.get("/compare", response_model=ComparisonResult)
def compare(
    a: str = Query(..., description="Player A id"),
    b: str = Query(..., description="Player B id"),
    svc: Services = Depends(get_services),
) -> ComparisonResult:
    pa, pb = svc.repo.primary_row(a), svc.repo.primary_row(b)
    missing = [pid for pid, p in ((a, pa), (b, pb)) if p is None]
    if missing:
        raise HTTPException(status_code=404, detail=f"Player(s) not found: {', '.join(missing)}")
    result = svc.comparison.compare(pa, pb)
    return ComparisonResult(
        player_a=PlayerSummary.of(pa), player_b=PlayerSummary.of(pb),
        metrics=result["metrics"], wins=result["wins"],
        overall_winner=result["overall_winner"], market_context=result["market_context"],
    )
