"""News for a player / team / competition (Google News RSS, no key, graceful)."""
from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.news_service import NewsService

router = APIRouter(tags=["news"])


class NewsArticle(BaseModel):
    title: str
    link: str
    source: str | None = None
    published: str | None = None


class NewsResponse(BaseModel):
    query: str
    articles: list[NewsArticle]


@lru_cache(maxsize=1)
def _news() -> NewsService:
    return NewsService()


@router.get("/news", response_model=NewsResponse)
def news(q: str = Query(..., min_length=1), limit: int = Query(6, ge=1, le=12)) -> NewsResponse:
    items = _news().search(q, limit=limit)
    return NewsResponse(query=q, articles=[NewsArticle(**vars(i)) for i in items])
