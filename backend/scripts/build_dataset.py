"""
Build PitchIQ's player dataset (breadth-first) from the Transfermarkt player-scores
dataset (github.com/dcaribou/transfermarkt-datasets, CC0 — no scraping).

Coverage: every European competition Transfermarkt records player appearances for —
14 top-division leagues, their domestic cups, UEFA Champions/Europa/Conference League
(incl. qualifiers & super cups), plus the World Cup and Africa Cup of Nations.

Model: ONE ROW PER (player, competition). A player who featured in a league, a domestic
cup and the Champions League gets three rows. This is what makes per-competition queries
("top scorers in the Champions League", "best midfielders in Serie A") possible.

Stats: matches, minutes, goals, assists, cards (+ per-90s), bio, and market value. Big-5
LEAGUE rows are additionally enriched with xG/xA/shots/key passes from Understat.

Runs at BUILD TIME only; the runtime just reads the committed CSV.

Usage: python backend/scripts/build_dataset.py [--season 2025] [--min-league-minutes 450]
Season is the START year (2025 == the 2025-26 season).
"""
from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path

import pandas as pd

TM = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data"
FILES = {
    "appearances": f"{TM}/appearances.csv.gz",
    "games": f"{TM}/games.csv.gz",
    "competitions": f"{TM}/competitions.csv.gz",
    "clubs": f"{TM}/clubs.csv.gz",
    "players": f"{TM}/players.csv.gz",
    "valuations": f"{TM}/player_valuations.csv.gz",
}

CACHE = Path(__file__).resolve().parent / ".cache"
OUT = Path(__file__).resolve().parents[1] / "app" / "data" / "players.csv"

POS_MAP = {"Attack": "Forward", "Midfield": "Midfielder",
           "Defender": "Defender", "Goalkeeper": "Goalkeeper"}
ROLE_MAP = {
    "Goalkeeper": "Goalkeeper", "Centre-Back": "Centre-Back",
    "Left-Back": "Full-back", "Right-Back": "Full-back",
    "Defensive Midfield": "Defensive Midfield", "Central Midfield": "Central Midfield",
    "Attacking Midfield": "Attacking Midfield", "Left Midfield": "Wide Midfield",
    "Right Midfield": "Wide Midfield", "Left Winger": "Winger", "Right Winger": "Winger",
    "Second Striker": "Second Striker", "Centre-Forward": "Centre-Forward",
}
# competition_type -> a clean, query-friendly label
TYPE_LABEL = {
    "domestic_league": "League", "domestic_cup": "Domestic Cup",
    "international_cup": "Continental", "national_team_competition": "International",
    "other": "Other",
}

# curated display names by competition_id (the raw 'name' column is just the URL slug,
# and some slugs collide -- e.g. Russia & Ukraine both "premier-liga").
NAME_BY_ID = {
    "GB1": "Premier League", "ES1": "LaLiga", "IT1": "Serie A", "L1": "Bundesliga",
    "FR1": "Ligue 1", "PO1": "Liga Portugal", "NL1": "Eredivisie", "TR1": "Süper Lig",
    "BE1": "Jupiler Pro League", "SC1": "Scottish Premiership", "GR1": "Super League Greece",
    "DK1": "Danish Superliga", "RU1": "Russian Premier League", "UKR1": "Ukrainian Premier League",
    "CL": "UEFA Champions League", "EL": "UEFA Europa League", "USC": "UEFA Super Cup",
    "CLQ": "Champions League Qualifying", "ELQ": "Europa League Qualifying",
    "ECLQ": "Conference League Qualifying", "FIWC": "World Cup", "AFCN": "Africa Cup of Nations",
    "FAC": "FA Cup", "CDR": "Copa del Rey", "DFB": "DFB-Pokal", "CIT": "Coppa Italia",
    "NLP": "KNVB Beker", "SFA": "Scottish FA Cup", "DKP": "Danish Cup", "RUP": "Russian Cup",
    "UKRP": "Ukrainian Cup", "GRP": "Greek Cup",
}
_ACRONYMS = {"Uefa": "UEFA", "Fa": "FA", "Dfb": "DFB", "Knvb": "KNVB", "Afc": "AFC"}


def pretty_competition(cid: str, slug: str) -> str:
    if cid in NAME_BY_ID:
        return NAME_BY_ID[cid]
    words = [_ACRONYMS.get(w.capitalize(), w.capitalize()) for w in str(slug).split("-")]
    return " ".join(words)


def log(m: str) -> None:
    print(f"[build_dataset] {m}", flush=True)


def download(url: str, dest: Path) -> Path:
    import urllib.request
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    log(f"downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "pitchiq-build/1.0"})
    with urllib.request.urlopen(req, timeout=180) as r, open(dest, "wb") as f:
        f.write(r.read())
    return dest


def load(name: str, **kw) -> pd.DataFrame:
    return pd.read_csv(download(FILES[name], CACHE / f"tm_{name}.csv.gz"), compression="gzip", **kw)


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", str(s)) if not unicodedata.combining(c))


def norm_name(s: str) -> str:
    return " ".join(strip_accents(s).lower().replace("-", " ").replace(".", " ").split())


UNDERSTAT_TO_TM = {
    "ENG-Premier League": "Premier League", "ESP-La Liga": "LaLiga",
    "ITA-Serie A": "Serie A", "GER-Bundesliga": "Bundesliga", "FRA-Ligue 1": "Ligue 1",
}
_ENRICH_COLS = ["shots", "key_passes", "xg", "xa"]
_ENRICH_PER90 = {"shots_per90": "shots", "key_passes_per90": "key_passes",
                 "xg_per90": "xg", "xa_per90": "xa"}


def enrich_understat(agg: pd.DataFrame, season: int) -> None:
    """
    HYBRID step: attach Understat's xG / shots / key passes to Big-5 LEAGUE rows
    (matched by normalized name). Rows in other competitions/leagues keep these empty.
    If Understat is unavailable, columns are left empty and the app degrades gracefully.
    """
    for c in (*_ENRICH_COLS, *_ENRICH_PER90):
        agg[c] = pd.NA

    code = f"{season % 100:02d}{(season + 1) % 100:02d}"
    try:
        import soccerdata as sd
        udf = sd.Understat(leagues=list(UNDERSTAT_TO_TM), seasons=code) \
            .read_player_season_stats().reset_index()
    except Exception as e:  # noqa: BLE001
        log(f"Understat enrichment skipped ({type(e).__name__}); Big-5 xG columns empty")
        return

    udf["comp"] = udf["league"].map(UNDERSTAT_TO_TM)
    udf["nkey"] = udf["player"].map(norm_name)
    udf = udf.sort_values("minutes", ascending=False).drop_duplicates(["nkey", "comp"], keep="first")
    lut = udf.set_index(["nkey", "comp"])[_ENRICH_COLS].to_dict("index")
    # per-competition token index for name-variation fallback ("Mbappe-Lottin" <-> "Mbappe")
    tok_index: dict[str, list] = {}
    for _, u in udf.iterrows():
        tok_index.setdefault(u["comp"], []).append((frozenset(u["nkey"].split()), u))

    big5 = set(UNDERSTAT_TO_TM.values())
    for idx, r in agg[agg["competition"].isin(big5)].iterrows():
        nkey = norm_name(r["name"])
        info = lut.get((nkey, r["competition"]))
        if not info:
            toks = frozenset(nkey.split())
            cands = [u for t, u in tok_index.get(r["competition"], [])
                     if len(t) >= 2 and (t <= toks or toks <= t)]
            info = cands[0] if len(cands) == 1 else None
        if info is not None:
            for c in _ENRICH_COLS:
                agg.at[idx, c] = info[c]

    for c in _ENRICH_COLS:
        agg[c] = pd.to_numeric(agg[c], errors="coerce")
    n90 = agg["nineties"]
    for out_col, src in _ENRICH_PER90.items():
        agg[out_col] = (agg[src] / n90).where(n90 > 0).round(3)
    log(f"Understat enrichment: {int(agg['xg'].notna().sum())} Big-5 league rows enriched "
        f"with xG/shots/key passes")


def build(season: int, min_league_minutes: int) -> None:
    label = f"{season}-{str(season + 1)[2:]}"
    log(f"season {label} (start year {season})")

    comps = load("competitions")
    comps = comps.set_index("competition_id")
    known = set(comps.index)

    games = load("games", usecols=["game_id", "season"])
    ap = load("appearances", usecols=["game_id", "player_id", "player_club_id",
                                       "competition_id", "minutes_played", "goals",
                                       "assists", "yellow_cards", "red_cards"])
    ap = ap.merge(games, on="game_id", how="left")
    ap = ap[(ap["season"] == season) & (ap["competition_id"].isin(known))].copy()
    log(f"appearances in season: {len(ap):,} across {ap['competition_id'].nunique()} competitions")

    # club a player represented in a competition = the club they logged most minutes for
    club_min = (ap.groupby(["player_id", "competition_id", "player_club_id"])["minutes_played"]
                .sum().reset_index())
    top_club = club_min.sort_values("minutes_played", ascending=False) \
        .drop_duplicates(["player_id", "competition_id"], keep="first") \
        .set_index(["player_id", "competition_id"])["player_club_id"]

    agg = ap.groupby(["player_id", "competition_id"]).agg(
        matches=("game_id", "nunique"),
        minutes=("minutes_played", "sum"),
        goals=("goals", "sum"),
        assists=("assists", "sum"),
        yellow_cards=("yellow_cards", "sum"),
        red_cards=("red_cards", "sum"),
    ).reset_index()
    agg["club_id"] = agg.set_index(["player_id", "competition_id"]).index.map(top_club)

    # per-competition-type minimum minutes (leagues need a fuller sample than cups)
    ctype = agg["competition_id"].map(lambda c: comps.loc[c, "type"])
    min_min = ctype.map(lambda t: min_league_minutes if t == "domestic_league" else 90)
    agg = agg[agg["minutes"] >= min_min].copy()
    log(f"player-competition rows after min-minutes: {len(agg):,}")

    # --- competition metadata -------------------------------------------------
    agg["competition"] = [pretty_competition(c, comps.loc[c, "name"]) for c in agg["competition_id"]]
    agg["competition_type"] = agg["competition_id"].map(comps["type"]).map(TYPE_LABEL).fillna("Other")
    agg["confederation"] = agg["competition_id"].map(comps["confederation"]).fillna("")
    country = agg["competition_id"].map(comps["country_name"])
    agg["country"] = country.where(country.notna() & (country != ""), "International")

    # --- club names (national-team competitions use the player's nation) -------
    clubs = load("clubs", usecols=["club_id", "name"]).set_index("club_id")["name"].to_dict()
    agg["club"] = agg["club_id"].map(clubs)

    # --- player bio -----------------------------------------------------------
    players = load("players", usecols=["player_id", "name", "position", "sub_position",
                                       "date_of_birth", "country_of_citizenship",
                                       "height_in_cm", "foot", "image_url",
                                       "market_value_in_eur", "highest_market_value_in_eur"])
    players["dob"] = pd.to_datetime(players["date_of_birth"], errors="coerce")
    pl = players.set_index("player_id")
    agg = agg[agg["player_id"].isin(pl.index)].copy()
    agg["name"] = agg["player_id"].map(pl["name"])
    agg["photo"] = agg["player_id"].map(pl["image_url"])
    agg["position"] = agg["player_id"].map(pl["position"]).map(POS_MAP).fillna("Midfielder")
    agg["role"] = agg["player_id"].map(pl["sub_position"]).map(ROLE_MAP)
    agg["role"] = agg["role"].fillna(agg["position"])
    agg["nation"] = agg["player_id"].map(pl["country_of_citizenship"])
    agg["height_cm"] = pd.to_numeric(agg["player_id"].map(pl["height_in_cm"]), errors="coerce")
    agg["foot"] = agg["player_id"].map(pl["foot"])
    # national-team competitions: the "club" is the country
    intl = agg["competition_type"] == "International"
    agg.loc[intl, "club"] = agg.loc[intl, "nation"]
    agg["club"] = agg["club"].fillna("—")

    ref = pd.Timestamp(f"{season + 1}-01-01")
    dob = agg["player_id"].map(pl["dob"])
    agg["age"] = ((ref - dob).dt.days // 365.25)
    agg["age"] = agg["age"].astype("Int64")

    # --- market value: historical (at season midpoint), then fall back to the
    #     player's current then peak value so notable players are never left blank
    vals = load("valuations", usecols=["player_id", "date", "market_value_in_eur"])
    vals["date"] = pd.to_datetime(vals["date"], errors="coerce")
    vals["dist"] = (vals["date"] - ref).abs()
    vals = vals.sort_values("dist").drop_duplicates("player_id", keep="first")
    era = agg["player_id"].map(vals.set_index("player_id")["market_value_in_eur"])
    cur = pd.to_numeric(agg["player_id"].map(pl["market_value_in_eur"]), errors="coerce")
    peak = pd.to_numeric(agg["player_id"].map(pl["highest_market_value_in_eur"]), errors="coerce")
    agg["market_value_eur"] = era.fillna(cur).fillna(peak)

    # --- per-90 (deterministic) ----------------------------------------------
    agg["nineties"] = agg["minutes"] / 90.0
    for out_col, src in {"goals_per90": "goals", "assists_per90": "assists"}.items():
        agg[out_col] = (agg[src] / agg["nineties"]).where(agg["nineties"] > 0).round(3)
    agg["goal_contributions"] = agg["goals"] + agg["assists"]
    agg["goal_contributions_per90"] = (agg["goal_contributions"] / agg["nineties"]) \
        .where(agg["nineties"] > 0).round(3)

    # --- HYBRID: enrich Big-5 league rows with Understat xG/shots/key passes ---
    enrich_understat(agg, season)

    # --- assemble -------------------------------------------------------------
    agg["player_id"] = "tm" + agg["player_id"].astype(str)
    agg["row_id"] = agg["player_id"] + "_" + agg["competition_id"].astype(str)
    cols = ["row_id", "player_id", "name", "photo", "position", "role", "age", "nation",
            "height_cm", "foot", "club", "club_id", "competition", "competition_id",
            "competition_type", "country", "confederation", "market_value_eur",
            "matches", "minutes", "nineties", "goals", "assists", "goal_contributions",
            "yellow_cards", "red_cards", "goals_per90", "assists_per90",
            "goal_contributions_per90",
            # Understat enrichment (Big-5 league rows only; null elsewhere)
            "shots", "key_passes", "xg", "xa",
            "shots_per90", "key_passes_per90", "xg_per90", "xa_per90"]
    out = agg[cols].copy()
    out["minutes"] = out["minutes"].round().astype("Int64")
    out["nineties"] = out["nineties"].round(1)
    out["height_cm"] = out["height_cm"].astype("Int64")
    out["club_id"] = pd.to_numeric(out["club_id"], errors="coerce").astype("Int64")
    for c in ("matches", "goals", "assists", "goal_contributions", "yellow_cards",
              "red_cards", "shots", "key_passes"):
        out[c] = out[c].round().astype("Int64")
    for c in ("xg", "xa"):
        out[c] = out[c].round(2)
    out = out.sort_values(["competition", "name"]).reset_index(drop=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False, encoding="utf-8")

    # --- slim clubs.csv (only clubs that appear) for Team profiles ------------
    present_clubs = set(pd.to_numeric(out["club_id"], errors="coerce").dropna().astype(int))
    cl = load("clubs", usecols=["club_id", "name", "domestic_competition_id", "total_market_value",
                                "squad_size", "average_age", "foreigners_number", "stadium_name",
                                "stadium_seats", "coach_name"])
    cl = cl[cl["club_id"].isin(present_clubs)].copy()
    cl["logo"] = "https://tmssl.akamaized.net/images/wappen/head/" + cl["club_id"].astype(str) + ".png"
    cl["competition"] = cl["domestic_competition_id"].map(
        lambda c: pretty_competition(c, comps.loc[c, "name"]) if c in comps.index else None)
    cl["country"] = cl["domestic_competition_id"].map(
        lambda c: comps.loc[c, "country_name"] if c in comps.index else None)
    cl = cl.rename(columns={"stadium_name": "stadium", "coach_name": "coach",
                            "average_age": "avg_age", "total_market_value": "squad_value"})
    cl[["club_id", "name", "logo", "competition", "country", "squad_value", "squad_size",
        "avg_age", "foreigners_number", "stadium", "stadium_seats", "coach"]].to_csv(
        OUT.parent / "clubs.csv", index=False, encoding="utf-8")

    # --- slim competitions.csv (only those present) for Competition profiles ---
    FLAG = {"England": "gb-eng", "Scotland": "gb-sct", "Spain": "es", "Italy": "it",
            "Germany": "de", "France": "fr", "Portugal": "pt", "Netherlands": "nl",
            "Türkiye": "tr", "Belgium": "be", "Greece": "gr", "Denmark": "dk",
            "Russia": "ru", "Ukraine": "ua"}
    present_comp_ids = set(out["competition_id"].unique())
    comp_rows = []
    for cid in present_comp_ids:
        m = comps.loc[cid]
        country = m["country_name"] if pd.notna(m["country_name"]) else "International"
        code = FLAG.get(country)
        comp_rows.append({
            "competition_id": cid,
            "competition": pretty_competition(cid, m["name"]),
            "type": TYPE_LABEL.get(m["type"], "Other"),
            "country": country,
            "confederation": m["confederation"] if pd.notna(m["confederation"]) else "",
            "flag": f"https://flagcdn.com/w160/{code}.png" if code else "",
        })
    pd.DataFrame(comp_rows).sort_values("competition").to_csv(
        OUT.parent / "competitions.csv", index=False, encoding="utf-8")
    log(f"wrote clubs.csv ({len(cl)}) and competitions.csv ({len(comp_rows)})")

    # --- coverage report ------------------------------------------------------
    players_n = out["player_id"].nunique()
    leagues = out[out["competition_type"] == "League"]["competition"].nunique()
    log("=" * 64)
    log(f"WROTE {OUT}")
    log(f"{len(out):,} rows · {players_n:,} unique players · {out['competition'].nunique()} competitions")
    log(f"leagues: {leagues} · countries: {out['country'].nunique()}")
    log(f"by type: {out['competition_type'].value_counts().to_dict()}")
    log(f"market value coverage: {out['market_value_eur'].notna().mean():.0%} · "
        f"age {out['age'].notna().mean():.0%}")
    log("=" * 64)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, default=2025, help="Start year (2025 = 2025-26)")
    ap.add_argument("--min-league-minutes", type=int, default=450)
    args = ap.parse_args()
    try:
        build(args.season, args.min_league_minutes)
    except Exception as e:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        log(f"FAILED: {e}")
        sys.exit(1)
