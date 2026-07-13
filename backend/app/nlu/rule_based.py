"""
Deterministic, dependency-free NLU.

This is both the zero-cost/offline path and the fallback whenever the LLM is disabled,
un-keyed, times out, or errors. It handles the three required intents plus graceful
ambiguity, so the app is fully functional with no API key at all.
"""
from __future__ import annotations

import re

from app.metrics import resolve_metric
from app.text import deaccent
from app.nlu.extractors import (
    find_age_bounds, find_competition, find_competition_type, find_country, find_limit,
    find_position, find_role, find_unsupported_region,
)
from app.nlu.query_models import QueryFilters, StructuredQuery

_COMPARE_TRIGGER = re.compile(r"\b(compare|comparison|comparar|comparacao|compara)\b", re.I)
_CONNECTORS = re.compile(r"\s+(?:vs\.?|versus|against|and|with|to|contra|e|ou)\s+", re.I)
_RANK_TRIGGER = re.compile(
    r"\b(top|best|most|highest|leading|lowest|worst|fewest|rank"
    r"|mais|melhor|melhores|maior|maiores|artilheiro|artilheiros|artilharia|ranking)\b", re.I)
_LOOKUP_TRIGGER = re.compile(
    r"\b(how (?:good|does)|compare[sd]? (?:to|with)|vs (?:the )?average|profile of|tell me about"
    r"|perfil de|me fale sobre|fale sobre|como (?:o|a|esta|e o))\b", re.I)

_FILLER = {"the", "a", "an", "average", "player", "players", "in", "la", "liga",
           "premier", "league", "serie", "bundesliga", "ligue", "striker", "strikers",
           "winger", "wingers", "midfielder", "defender", "goalkeeper", "forward",
           "o", "os", "as", "do", "da", "de", "media", "jogador", "jogadores"}


def _clean_name(raw: str) -> str:
    raw = re.sub(r"[?.!,]", " ", raw)
    # drop trailing "in la liga" / "under 23" style qualifiers. NB: we do NOT split on
    # "de/da/do" -- they are common inside names (De Bruyne, de Paul).
    raw = re.split(r"\b(in|from|under|over|by|who|with the|na|no)\b", raw, maxsplit=1)[0]
    return " ".join(raw.split()).strip()


def _looks_like_name(s: str) -> bool:
    words = [w for w in s.lower().split() if w not in _FILLER]
    return len(s) >= 3 and len(words) >= 1


def _base_filters(text: str) -> QueryFilters:
    min_age, max_age = find_age_bounds(text)
    competition = find_competition(text)
    return QueryFilters(
        competition=competition,
        country=None if competition else find_country(text),
        competition_type=None if competition else find_competition_type(text),
        position=find_position(text),
        role=find_role(text),
        min_age=min_age,
        max_age=max_age,
    )


def interpret(text: str) -> StructuredQuery:
    q = text.strip()
    low = deaccent(q.lower())   # accent-insensitive for EN + PT trigger matching

    # 1) Comparison ---------------------------------------------------------
    if _COMPARE_TRIGGER.search(low) or (" vs" in f" {low}") or " versus " in low:
        body = _COMPARE_TRIGGER.sub("", q, count=1).strip(" :")
        parts = [_clean_name(p) for p in _CONNECTORS.split(body) if _clean_name(p)]
        entities = [p for p in parts if _looks_like_name(p)][:2]
        if len(entities) >= 2:
            return StructuredQuery(intent="comparison", entities=entities, raw_query=q)

    # 1b) Out-of-coverage region named -> fail gracefully -------------------
    region = find_unsupported_region(q)
    if region and not find_competition(q):
        return StructuredQuery(
            intent="out_of_scope", raw_query=q,
            notes=f"{region} isn't in the dataset.",
        )

    # 2) Ranking / filtering ------------------------------------------------
    if _RANK_TRIGGER.search(low):
        metric = None
        if m := re.search(r"\bby ([a-z0-9 %/+.-]+)", low):
            metric = resolve_metric(m.group(1))
        metric = metric or resolve_metric(low)
        ascending = bool(re.search(r"\b(lowest|worst|fewest)\b", low))
        if metric:
            return StructuredQuery(
                intent="ranking", metric=metric, filters=_base_filters(q),
                limit=find_limit(q), ascending=ascending or None, raw_query=q,
            )
        # "best striker" with no metric -> genuinely ambiguous
        return StructuredQuery(
            intent="ambiguous", filters=_base_filters(q), raw_query=q,
            notes="A ranking was requested but no metric was specified (best at what?).",
        )

    # 3) Lookup / explanation ----------------------------------------------
    if _LOOKUP_TRIGGER.search(low):
        name = q
        name = re.split(_LOOKUP_TRIGGER, name, maxsplit=1)[-1]
        name = _clean_name(name)
        # 'how does Haaland compare to the average striker' -> name before 'compare'
        name = re.split(r"\bcompare|vs\b", name)[0].strip() or name
        if _looks_like_name(name):
            return StructuredQuery(
                intent="lookup", entities=[name], filters=_base_filters(q), raw_query=q,
            )

    # 4) bare "best player" -------------------------------------------------
    if re.search(r"\bbest player|greatest player|who is the best|melhor jogador|quem e o melhor\b", low):
        return StructuredQuery(intent="ambiguous", raw_query=q,
                               notes="'Best' is undefined without a metric.")

    return StructuredQuery(intent="out_of_scope", raw_query=q,
                           notes="Could not map the question to a supported intent.")
