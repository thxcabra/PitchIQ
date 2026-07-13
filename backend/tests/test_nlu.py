"""Query-understanding tests: rule-based interpreter + LLM-output validation/grounding."""
from __future__ import annotations

from app.nlu import rule_based
from app.nlu.interpreter import Interpreter


# --- rule-based (zero-key) path -------------------------------------------------
def test_ranking_query_full_extraction():
    q = "Top 5 wingers under 23 in the Premier League by assists per 90"
    sq = rule_based.interpret(q)
    assert sq.intent == "ranking"
    assert sq.metric == "assists_per90"
    assert sq.filters.role == "Winger"
    assert sq.filters.competition == "Premier League"
    assert sq.filters.max_age == 22
    assert sq.limit == 5


def test_comparison_query_extracts_two_entities():
    sq = rule_based.interpret("Compare Haaland and Mbappe")
    assert sq.intent == "comparison"
    assert sq.entities == ["Haaland", "Mbappe"]


def test_comparison_vs_syntax():
    sq = rule_based.interpret("Kevin De Bruyne vs Bruno Fernandes")
    assert sq.intent == "comparison"
    assert len(sq.entities) == 2


def test_lookup_query():
    sq = rule_based.interpret("How does Vinicius compare to the average striker in La Liga")
    assert sq.intent == "lookup"
    assert sq.entities and "vinicius" in sq.entities[0].lower()
    assert sq.filters.competition == "LaLiga"


def test_ambiguous_best_player():
    sq = rule_based.interpret("Who is the best player")
    assert sq.intent == "ambiguous"


def test_ranking_without_metric_is_ambiguous():
    sq = rule_based.interpret("best striker in Serie A")
    assert sq.intent == "ambiguous"


def test_out_of_scope():
    sq = rule_based.interpret("What is the capital of France")
    assert sq.intent == "out_of_scope"


# --- LLM path: validation + grounding against closed vocabularies ---------------
class _StubProvider:
    name = "gemini"

    def __init__(self, payload):
        self._payload = payload

    def extract(self, query):
        return self._payload


def test_llm_output_is_grounded_to_canonical_vocab():
    # LLM returns sloppy values: "EPL", "strikers", aliased metric -> must be normalised.
    stub = _StubProvider({
        "intent": "ranking",
        "metric": "assists per 90",     # phrase -> assists_per90 (explicit rate)
        "entities": [],
        "filters": {"competition": "EPL", "role": "strikers", "max_age": 22},
        "limit": 5,
    })
    sq = Interpreter(provider=stub).interpret("top young epl assist makers per 90")
    assert sq.provider == "gemini"
    assert sq.metric == "assists_per90"
    assert sq.filters.competition == "Premier League"
    assert sq.filters.role == "Centre-Forward"  # "strikers" alias resolves via role map


def test_llm_invalid_intent_falls_back_to_rules():
    stub = _StubProvider({"intent": "nonsense", "entities": []})
    sq = Interpreter(provider=stub).interpret("Compare Haaland and Mbappe")
    # invalid LLM output -> deterministic fallback still understands the question
    assert sq.provider == "rule_based"
    assert sq.intent == "comparison"


def test_llm_failure_falls_back():
    class _Dead:
        name = "gemini"

        def extract(self, query):
            return None

    sq = Interpreter(provider=_Dead()).interpret("Top 5 forwards by goals per 90")
    assert sq.provider == "rule_based"
    assert sq.intent == "ranking"
    assert sq.metric == "goals_per90"
