"""PitchIQ API — FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.deps import get_services
from app.routes import chat, compare, competitions, meta, news, players, teams


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_services()  # load the dataset at startup; fail fast if it's missing
    yield


app = FastAPI(
    title="PitchIQ API",
    version="1.0.0",
    description="Conversational analytics over 2025-26 European football (14 leagues, cups, UEFA competitions).",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(players.router)
app.include_router(compare.router)
app.include_router(chat.router)
app.include_router(meta.router)
app.include_router(teams.router)
app.include_router(competitions.router)
app.include_router(news.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    svc = get_services()
    return {"status": "ok", "players": len(svc.repo.all()), "llm_enabled": settings.llm_enabled}
