"""
LLM provider abstraction: turn a free-text question into a raw structured-query dict.

A provider only extracts intent/entities/filters; it never computes a statistic. Gemini
is called over its REST API with a `responseSchema` (constrained JSON output). Add a
provider by writing a sibling class and a branch in `build_provider`. Keys come from env.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Protocol

from app.config import settings
from app.metrics import METRICS

_METRIC_KEYS = list(METRICS.keys())

_SYSTEM = f"""You are the query-understanding layer of a football analytics app.
The user may write in ANY language (English, Portuguese, Spanish...). Understand it and
extract the structured query; keep player-name entities exactly as written.
Convert the user's question into a structured query. You ONLY extract intent and
parameters -- you must NEVER compute, invent, or state any statistic, ranking, or number.

intent is one of:
- "ranking": a top-N / best / most / filtered list (e.g. "top 5 wingers under 23 by assists").
- "lookup": one player vs the average of a position in a league (e.g. "how does Kane compare to the average striker in La Liga").
- "comparison": two named players compared (e.g. "compare Haaland and Mbappe").
- "ambiguous": a superlative with no measurable metric (e.g. "who is the best player").
- "out_of_scope": not answerable from per-player football stats.

metric MUST be one of these exact keys or null: {_METRIC_KEYS}
The dataset covers 14 European leagues + domestic cups + UEFA Champions/Europa League +
World Cup + Africa Cup of Nations, for the 2025-26 season.
filters.competition: a specific competition, e.g. "Premier League", "LaLiga", "Serie A",
"Bundesliga", "Ligue 1", "UEFA Champions League", "UEFA Europa League", "World Cup",
"FA Cup", "Copa del Rey" (or null).
filters.country: a league's country, e.g. "England", "Spain", "Italy", "Germany",
"France", "Portugal", "Netherlands", "Scotland" (or null). Use country only when the user
names a country rather than a specific competition.
filters.competition_type: one of League, Domestic Cup, Continental, International (or null).
filters.club: a club name if the user names one (or null).
filters.position (broad) one of: Forward, Midfielder, Defender, Goalkeeper (or null).
filters.role (detailed) e.g. Winger, Centre-Forward, Centre-Back, Full-back,
Defensive Midfield, Attacking Midfield, Central Midfield (or null).
entities: the raw player name(s) exactly as written by the user (do not correct spelling).
For "under 23" set filters.max_age=22; for "over 30" set filters.min_age=31.
limit: the N in top-N (default null). ascending: true only for "lowest/worst"."""

_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": ["ranking", "lookup", "comparison", "ambiguous", "out_of_scope"]},
        "metric": {"type": "string", "nullable": True},
        "entities": {"type": "array", "items": {"type": "string"}},
        "filters": {
            "type": "object",
            "properties": {
                "competition": {"type": "string", "nullable": True},
                "country": {"type": "string", "nullable": True},
                "competition_type": {"type": "string", "nullable": True},
                "club": {"type": "string", "nullable": True},
                "position": {"type": "string", "nullable": True},
                "role": {"type": "string", "nullable": True},
                "nation": {"type": "string", "nullable": True},
                "min_age": {"type": "integer", "nullable": True},
                "max_age": {"type": "integer", "nullable": True},
                "min_minutes": {"type": "integer", "nullable": True},
            },
        },
        "limit": {"type": "integer", "nullable": True},
        "ascending": {"type": "boolean", "nullable": True},
        "notes": {"type": "string", "nullable": True},
    },
    "required": ["intent", "entities"],
}


class LLMProvider(Protocol):
    name: str

    def extract(self, query: str) -> dict | None:
        """Return a raw structured-query dict, or None on any failure."""
        ...


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str, timeout: float):
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    def extract(self, query: str) -> dict | None:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:generateContent?key={self._api_key}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": _SYSTEM}]},
            "contents": [{"parts": [{"text": query}]}],
            "generationConfig": {
                "temperature": 0,
                "responseMimeType": "application/json",
                "responseSchema": _RESPONSE_SCHEMA,
            },
        }
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except (urllib.error.URLError, KeyError, IndexError, ValueError, TimeoutError):
            return None


def build_provider() -> LLMProvider | None:
    """Factory -- returns the configured provider, or None to force rule-based NLU."""
    if settings.llm_provider.lower() == "gemini" and settings.gemini_api_key:
        return GeminiProvider(settings.gemini_api_key, settings.gemini_model, settings.llm_timeout_seconds)
    return None
