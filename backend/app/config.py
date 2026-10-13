"""Application settings, loaded from environment variables (and optional .env files).

Lookup order, highest priority first: real environment variables, `backend/.env`, then the
repo-root `.env` (paths are relative to the working directory, i.e. `backend/` when running
uvicorn or pytest locally). Missing files are ignored.
"""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_CSV = Path(__file__).resolve().parent / "data" / "players.csv"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),  # later files win: backend/.env overrides the root one
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Data
    csv_path: str = str(_DEFAULT_CSV)

    # LLM / NLU.  LLM_PROVIDER = gemini | none  (none -> rule-based NLU only)
    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    llm_timeout_seconds: float = 12.0

    # Server
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_enabled(self) -> bool:
        return self.llm_provider.lower() == "gemini" and bool(self.gemini_api_key)


settings = Settings()
