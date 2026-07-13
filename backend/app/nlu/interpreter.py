"""
The NLU orchestrator: free text -> validated StructuredQuery.

Strategy: try the LLM (if configured) for its superior entity/intent extraction, then
*normalise and validate every field it returns against our closed vocabularies* -- the
LLM never gets to invent a metric key or an unknown league. On any LLM failure it falls
back to the deterministic rule-based interpreter, so /chat always returns something sane.
"""
from __future__ import annotations

from app.metrics import resolve_metric
from app.nlu import rule_based
from app.nlu.extractors import (
    find_competition, find_competition_type, find_country, find_position, find_unsupported_region,
    normalize_role,
)
from app.nlu.llm_provider import LLMProvider, build_provider
from app.nlu.query_models import QueryFilters, StructuredQuery

_VALID_POSITIONS = {"Forward", "Midfielder", "Defender", "Goalkeeper"}
_VALID_INTENTS = {"ranking", "lookup", "comparison", "ambiguous", "out_of_scope"}


class Interpreter:
    def __init__(self, provider: LLMProvider | None = None):
        self._provider = provider if provider is not None else build_provider()

    def interpret(self, text: str) -> StructuredQuery:
        if self._provider is not None:
            raw = self._provider.extract(text)
            validated = self._validate(raw, text) if raw else None
            if validated is not None:
                validated.provider = self._provider.name
                return validated
        # fallback: deterministic
        return rule_based.interpret(text)

    # --- normalise/validate LLM output against closed vocabularies -------------
    def _validate(self, raw: dict, text: str) -> StructuredQuery | None:
        intent = raw.get("intent")
        if intent not in _VALID_INTENTS:
            return None

        # metric: only accept a canonical key (map fuzzy/aliased values, else drop)
        metric = raw.get("metric")
        if metric:
            metric = resolve_metric(str(metric))

        f = raw.get("filters") or {}
        # competition: resolve only against the known vocabulary (never trust a raw LLM string)
        competition = find_competition(str(f.get("competition") or "")) or find_competition(text)
        country = f.get("country")
        country = find_country(str(country)) if country else None
        comp_type = find_competition_type(str(f.get("competition_type") or ""))
        position = f.get("position")
        position = position if position in _VALID_POSITIONS else find_position(str(position or ""))
        role = normalize_role(f.get("role"))

        def _int(v):
            try:
                return int(v) if v is not None else None
            except (TypeError, ValueError):
                return None

        filters = QueryFilters(
            competition=competition, country=None if competition else country,
            competition_type=None if competition else comp_type, club=(f.get("club") or None),
            position=position, role=role, nation=(f.get("nation") or None),
            min_age=_int(f.get("min_age")), max_age=_int(f.get("max_age")),
            min_minutes=_int(f.get("min_minutes")),
        )

        entities = [str(e).strip() for e in (raw.get("entities") or []) if str(e).strip()]

        # sanity: comparison needs 2 names, lookup needs 1
        if intent == "comparison" and len(entities) < 2:
            return None
        if intent == "lookup" and not entities:
            return None
        # a ranking/lookup naming an out-of-coverage region -> fail gracefully
        if intent in ("ranking", "lookup") and competition is None:
            region = find_unsupported_region(text)
            if region:
                return StructuredQuery(intent="out_of_scope", raw_query=text,
                                       notes=f"{region} isn't in the dataset.")

        if intent == "ranking" and not metric:
            # ranking without a resolvable metric is ambiguous, not an error
            return StructuredQuery(intent="ambiguous", filters=filters, entities=entities,
                                   raw_query=text, notes="Ranking requested without a clear metric.")

        return StructuredQuery(
            intent=intent, metric=metric, entities=entities, filters=filters,
            limit=_int(raw.get("limit")), ascending=raw.get("ascending"),
            notes=raw.get("notes"), raw_query=text,
        )
