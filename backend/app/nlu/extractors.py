"""
Shared vocabulary + extraction helpers.

Used by the rule-based interpreter directly, and by the interpreter to *normalise and
validate* whatever the LLM returns (so an LLM saying "EPL" or "strikers" still maps to
the canonical league/role the data layer understands).
"""
from __future__ import annotations

import re

from app.text import deaccent

# competition name aliases -> canonical competition display name (matches the dataset)
COMPETITION_ALIASES: dict[str, str] = {
    "premier league": "Premier League", "epl": "Premier League", "english premier league": "Premier League",
    "laliga": "LaLiga", "la liga": "LaLiga",
    "serie a": "Serie A",
    "bundesliga": "Bundesliga",
    "ligue 1": "Ligue 1", "ligue1": "Ligue 1",
    "liga portugal": "Liga Portugal", "primeira liga": "Liga Portugal",
    "eredivisie": "Eredivisie",
    "super lig": "Süper Lig", "süper lig": "Süper Lig",
    "jupiler pro league": "Jupiler Pro League", "pro league": "Jupiler Pro League",
    "scottish premiership": "Scottish Premiership",
    "super league greece": "Super League Greece", "greek super league": "Super League Greece",
    "danish superliga": "Danish Superliga", "superliga": "Danish Superliga",
    "russian premier league": "Russian Premier League",
    "ukrainian premier league": "Ukrainian Premier League",
    "champions league": "UEFA Champions League", "ucl": "UEFA Champions League",
    "uefa champions league": "UEFA Champions League", "cl": "UEFA Champions League",
    "liga dos campeoes": "UEFA Champions League",
    "europa league": "UEFA Europa League", "uel": "UEFA Europa League",
    "liga europa": "UEFA Europa League",
    "world cup": "World Cup", "the world cup": "World Cup", "copa do mundo": "World Cup",
    "africa cup of nations": "Africa Cup of Nations", "afcon": "Africa Cup of Nations",
    "copa africana": "Africa Cup of Nations", "copa africana de nacoes": "Africa Cup of Nations",
    "fa cup": "FA Cup", "copa del rey": "Copa del Rey", "dfb pokal": "DFB-Pokal",
    "coppa italia": "Coppa Italia",
}

# country name / adjective -> canonical country (matches dataset country field).
# Includes PT-BR forms (accents are stripped before matching).
COUNTRY_ALIASES: dict[str, str] = {
    "england": "England", "english": "England", "inglaterra": "England",
    "ingles": "England", "inglesa": "England",
    "spain": "Spain", "spanish": "Spain", "espanha": "Spain", "espanhol": "Spain", "espanhola": "Spain",
    "italy": "Italy", "italian": "Italy", "italia": "Italy", "italiano": "Italy", "italiana": "Italy",
    "germany": "Germany", "german": "Germany", "alemanha": "Germany", "alemao": "Germany", "alema": "Germany",
    "france": "France", "french": "France", "franca": "France", "frances": "France", "francesa": "France",
    "portugal": "Portugal", "portuguese": "Portugal", "portugues": "Portugal", "portuguesa": "Portugal",
    "netherlands": "Netherlands", "holland": "Netherlands", "dutch": "Netherlands",
    "holanda": "Netherlands", "holandes": "Netherlands", "holandesa": "Netherlands",
    "turkey": "Türkiye", "turkiye": "Türkiye", "turkish": "Türkiye",
    "turquia": "Türkiye", "turco": "Türkiye", "turca": "Türkiye",
    "belgium": "Belgium", "belgian": "Belgium", "belgica": "Belgium", "belga": "Belgium",
    "scotland": "Scotland", "scottish": "Scotland", "escocia": "Scotland", "escoces": "Scotland", "escocesa": "Scotland",
    "greece": "Greece", "greek": "Greece", "grecia": "Greece", "grego": "Greece", "grega": "Greece",
    "denmark": "Denmark", "danish": "Denmark", "dinamarca": "Denmark", "dinamarques": "Denmark",
    "russia": "Russia", "russian": "Russia", "russo": "Russia", "russa": "Russia",
    "ukraine": "Ukraine", "ukrainian": "Ukraine", "ucrania": "Ukraine", "ucraniano": "Ukraine", "ucraniana": "Ukraine",
}

# multi-word only: bare "league"/"cup" collide with competition names
# ("Champions League", "FA Cup"), so we require explicit phrasing.
# regions the free dataset does NOT cover -> used to fail gracefully instead of
# silently returning global results.
UNSUPPORTED_REGION_ALIASES: dict[str, str] = {
    "brazil": "Brazil", "brazilian": "Brazil", "brasileirao": "Brazil", "brasileirão": "Brazil",
    "argentina": "Argentina", "argentine": "Argentina", "argentinian": "Argentina",
    "mls": "the USA (MLS)", "usa": "the USA", "united states": "the USA", "american": "the USA",
    "mexico": "Mexico", "liga mx": "Mexico", "mexican": "Mexico",
    "saudi": "Saudi Arabia", "saudi arabia": "Saudi Arabia", "saudi pro league": "Saudi Arabia",
    "japan": "Japan", "j league": "Japan", "j1": "Japan",
    "korea": "South Korea", "k league": "South Korea",
    "australia": "Australia", "a league": "Australia",
    "china": "China", "chinese": "China",
}

COMPETITION_TYPE_ALIASES: dict[str, str] = {
    "domestic league": "League", "domestic leagues": "League",
    "first division": "League", "top division": "League",
    "primeira divisao": "League", "primeira liga": "League", "liga nacional": "League",
    "domestic cup": "Domestic Cup", "domestic cups": "Domestic Cup",
    "cup competition": "Domestic Cup", "cup competitions": "Domestic Cup",
    "copa nacional": "Domestic Cup",
    "continental": "Continental", "international competition": "International",
}

# broad position
POSITION_ALIASES: dict[str, str] = {
    "forward": "Forward", "forwards": "Forward", "attacker": "Forward", "attackers": "Forward",
    "striker": "Forward", "strikers": "Forward", "winger": "Forward", "wingers": "Forward",
    "atacante": "Forward", "atacantes": "Forward", "ponta": "Forward", "pontas": "Forward",
    "centroavante": "Forward",
    "midfielder": "Midfielder", "midfielders": "Midfielder", "midfield": "Midfielder",
    "meia": "Midfielder", "meias": "Midfielder", "meio-campista": "Midfielder", "meio campo": "Midfielder",
    "volante": "Midfielder", "volantes": "Midfielder",
    "defender": "Defender", "defenders": "Defender", "defence": "Defender", "defense": "Defender",
    "zagueiro": "Defender", "zagueiros": "Defender", "defensor": "Defender", "lateral": "Defender", "laterais": "Defender",
    "goalkeeper": "Goalkeeper", "goalkeepers": "Goalkeeper", "keeper": "Goalkeeper", "gk": "Goalkeeper",
    "goleiro": "Goalkeeper", "goleiros": "Goalkeeper",
}

# detailed role (for precise ranking filters like "top 5 wingers")
ROLE_ALIASES: dict[str, str] = {
    "winger": "Winger", "wingers": "Winger", "ponta": "Winger", "pontas": "Winger",
    "striker": "Centre-Forward", "strikers": "Centre-Forward", "centroavante": "Centre-Forward",
    "centre-forward": "Centre-Forward", "center forward": "Centre-Forward", "cf": "Centre-Forward",
    "centre-back": "Centre-Back", "center back": "Centre-Back", "centre back": "Centre-Back",
    "cb": "Centre-Back", "centre-backs": "Centre-Back", "zagueiro": "Centre-Back", "zagueiros": "Centre-Back",
    "full-back": "Full-back", "fullback": "Full-back", "full back": "Full-back",
    "right-back": "Full-back", "left-back": "Full-back", "wing-back": "Full-back",
    "lateral": "Full-back", "laterais": "Full-back",
    "defensive midfielder": "Defensive Midfield", "cdm": "Defensive Midfield", "holding midfielder": "Defensive Midfield",
    "volante": "Defensive Midfield", "volantes": "Defensive Midfield",
    "attacking midfielder": "Attacking Midfield", "cam": "Attacking Midfield", "playmaker": "Attacking Midfield",
    "meia atacante": "Attacking Midfield",
    "central midfielder": "Central Midfield", "cm": "Central Midfield",
}


def _match_alias(text: str, aliases: dict[str, str]) -> str | None:
    t = f" {deaccent(text.lower())} "
    for alias, canon in sorted(aliases.items(), key=lambda kv: -len(kv[0])):
        if re.search(rf"(?<![a-z]){re.escape(deaccent(alias))}(?![a-z])", t):
            return canon
    return None


def find_competition(text: str) -> str | None:
    return _match_alias(text, COMPETITION_ALIASES)


def find_country(text: str) -> str | None:
    return _match_alias(text, COUNTRY_ALIASES)


def find_competition_type(text: str) -> str | None:
    return _match_alias(text, COMPETITION_TYPE_ALIASES)


def find_unsupported_region(text: str) -> str | None:
    return _match_alias(text, UNSUPPORTED_REGION_ALIASES)


def find_position(text: str) -> str | None:
    return _match_alias(text, POSITION_ALIASES)


CANON_ROLES: set[str] = set(ROLE_ALIASES.values()) | {
    "Wide Midfield", "Second Striker", "Defender", "Midfielder", "Forward", "Goalkeeper",
}


def find_role(text: str) -> str | None:
    return _match_alias(text, ROLE_ALIASES)


def normalize_role(value: str | None) -> str | None:
    """Accept an already-canonical role as-is, else map free text through the alias table."""
    if not value:
        return None
    if value in CANON_ROLES:
        return value
    return find_role(str(value))


def find_age_bounds(text: str) -> tuple[int | None, int | None]:
    t = deaccent(text.lower())
    min_age = max_age = None
    if m := re.search(r"\bu-?(\d{2})\b", t):                    # u23 / u-21 / sub-21
        max_age = int(m.group(1)) - 1
    if m := re.search(r"(?:under|younger than|abaixo de|menos de|menores de|ate) (\d{2})", t):
        max_age = int(m.group(1)) - 1
    if m := re.search(r"(?:over|older than|acima de|mais de|maiores de) (\d{2})", t):
        min_age = int(m.group(1)) + 1
    if m := re.search(r"(?:aged?|idade) (\d{2})\s*(?:to|-|a|e)\s*(\d{2})", t):
        min_age, max_age = int(m.group(1)), int(m.group(2))
    return min_age, max_age


def find_limit(text: str, default: int = 5) -> int:
    t = deaccent(text.lower())
    if m := re.search(r"(?:top|melhores|maiores|primeiros) (\d{1,2})", t):
        return int(m.group(1))
    if m := re.search(r"(\d{1,2}) (?:best|top|melhores|maiores)\b", t):
        return int(m.group(1))
    return default
