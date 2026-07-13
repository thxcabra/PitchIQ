"""Metadata for frontend filters and the chat 'about' panel."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.config import settings
from app.deps import Services, get_services
from app.metrics import METRICS

router = APIRouter(tags=["meta"])


@router.get("/meta")
def meta(svc: Services = Depends(get_services)) -> dict:
    rows = svc.repo.all()
    return {
        "player_count": len(svc.repo.players()),
        "row_count": len(rows),
        "season": "2025-26",
        "competitions": svc.repo.competitions(),
        "competition_index": svc.repo.competition_index(),
        "countries": svc.repo.countries(),
        "positions": svc.repo.positions(),
        "roles": svc.repo.roles(),
        "role_groups": svc.repo.role_groups(),
        "metrics": [{"key": m.key, "label": m.label, "unit": m.unit} for m in METRICS.values()],
        "nlu_provider": "gemini" if settings.llm_enabled else "rule_based",
    }
