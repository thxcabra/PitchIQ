"""
CSV access, abstracted.

The dataset is one row per (player, competition). Loaded once and exposed two ways: a
flat list of rows (for per-competition ranking) and grouped by person (for search /
profile / comparison). Also loads the clubs and competitions metadata tables.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from app.models.domain import METRIC_COLUMNS, Club, Competition, Player
from app.text import normalize  # re-exported: services import it from here

_LEAGUE = "League"


def _num(v: str) -> float | None:
    if v is None or v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _int(v: str) -> int | None:
    n = _num(v)
    return int(n) if n is not None else None


class PlayerRepository:
    def __init__(self, csv_path: str | Path):
        self._csv_path = Path(csv_path)
        self._rows: list[Player] = []
        self._by_row: dict[str, Player] = {}
        self._by_player: dict[str, list[Player]] = defaultdict(list)
        self._clubs: dict[int, Club] = {}
        self._competitions: dict[str, Competition] = {}
        self._load()
        self._load_clubs()
        self._load_competitions()

    def _load(self) -> None:
        if not self._csv_path.exists():
            raise FileNotFoundError(
                f"Dataset not found at {self._csv_path}. "
                f"Run: python backend/scripts/build_dataset.py"
            )
        with open(self._csv_path, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                p = Player(
                    row_id=row["row_id"],
                    player_id=row["player_id"],
                    name=row["name"],
                    photo=row.get("photo") or None,
                    club_id=_int(row.get("club_id", "")),
                    position=row["position"],
                    role=row.get("role") or row["position"],
                    age=_int(row.get("age", "")),
                    nation=row.get("nation") or None,
                    height_cm=_int(row.get("height_cm", "")),
                    foot=row.get("foot") or None,
                    club=row["club"],
                    competition=row["competition"],
                    competition_id=row["competition_id"],
                    competition_type=row["competition_type"],
                    country=row["country"],
                    confederation=row.get("confederation") or None,
                    market_value_eur=_num(row.get("market_value_eur", "")),
                    metrics={c: _num(row.get(c, "")) for c in METRIC_COLUMNS},
                )
                self._rows.append(p)
                self._by_row[p.row_id] = p
                self._by_player[p.player_id].append(p)

    def _load_clubs(self) -> None:
        path = self._csv_path.parent / "clubs.csv"
        if not path.exists():
            return
        with open(path, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                cid = _int(row["club_id"])
                if cid is None:
                    continue
                self._clubs[cid] = Club(
                    club_id=cid, name=row["name"], logo=row.get("logo") or None,
                    competition=row.get("competition") or None, country=row.get("country") or None,
                    squad_value=_num(row.get("squad_value", "")), squad_size=_int(row.get("squad_size", "")),
                    avg_age=_num(row.get("avg_age", "")), foreigners_number=_int(row.get("foreigners_number", "")),
                    stadium=row.get("stadium") or None, stadium_seats=_int(row.get("stadium_seats", "")),
                    coach=row.get("coach") or None,
                )

    def _load_competitions(self) -> None:
        path = self._csv_path.parent / "competitions.csv"
        if not path.exists():
            return
        with open(path, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                self._competitions[row["competition"]] = Competition(
                    competition_id=row["competition_id"], competition=row["competition"],
                    type=row["type"], country=row["country"],
                    confederation=row.get("confederation") or None, flag=row.get("flag") or None,
                )

    # --- rows (per-competition) -----------------------------------------------
    def all(self) -> list[Player]:
        return list(self._rows)

    def get_row(self, row_id: str) -> Player | None:
        return self._by_row.get(row_id)

    def cohort(self, position: str, competition: str) -> list[Player]:
        """Peer group for percentiles: same position within the same competition."""
        return [p for p in self._rows
                if p.position == position and p.competition == competition]

    # --- people (grouped) -----------------------------------------------------
    def player_rows(self, player_id: str) -> list[Player]:
        return list(self._by_player.get(player_id, []))

    def primary_row(self, player_id: str) -> Player | None:
        """A person's headline row: their main domestic league (most minutes), else most minutes."""
        rows = self._by_player.get(player_id)
        if not rows:
            return None
        leagues = [r for r in rows if r.competition_type == _LEAGUE]
        pool = leagues or rows
        return max(pool, key=lambda r: r.metric("minutes") or 0)

    def players(self) -> list[Player]:
        """One headline row per person."""
        return [self.primary_row(pid) for pid in self._by_player]  # type: ignore[misc]

    # --- vocabularies ---------------------------------------------------------
    def competitions(self) -> list[str]:
        return sorted({p.competition for p in self._rows})

    def competition_index(self) -> list[dict]:
        """Unique (competition, country, type) triples for building filter hierarchies."""
        seen: dict[str, dict] = {}
        for p in self._rows:
            if p.competition not in seen:
                seen[p.competition] = {
                    "competition": p.competition,
                    "country": p.country,
                    "competition_type": p.competition_type,
                }
        return sorted(seen.values(), key=lambda x: (x["country"], x["competition"]))

    def countries(self) -> list[str]:
        return sorted({p.country for p in self._rows})

    def clubs(self) -> list[str]:
        return sorted({p.club for p in self._rows if p.club and p.club != "—"})

    def positions(self) -> list[str]:
        return sorted({p.position for p in self._rows})

    def roles(self) -> list[str]:
        # ordered by broad position, then role, for a sensible dropdown
        order = {"Forward": 0, "Midfielder": 1, "Defender": 2, "Goalkeeper": 3}
        by_role: dict[str, str] = {}
        for p in self._rows:
            by_role.setdefault(p.role, p.position)
        return sorted(by_role, key=lambda r: (order.get(by_role[r], 4), r))

    def role_groups(self) -> list[dict]:
        """Detailed roles grouped under their broad position, for a hierarchical filter."""
        broad_order = ["Forward", "Midfielder", "Defender", "Goalkeeper"]
        # each role's broad position = the position it most often appears with
        counts: dict[str, dict[str, int]] = {}
        for p in self._rows:
            counts.setdefault(p.role, {}).setdefault(p.position, 0)
            counts[p.role][p.position] += 1
        role_pos = {r: max(pc, key=lambda k: pc[k]) for r, pc in counts.items()}

        groups = []
        for pos in broad_order:
            roles = sorted(r for r, bp in role_pos.items() if bp == pos and r != pos)
            groups.append({"position": pos, "roles": roles})
        return groups

    # --- clubs & competitions -------------------------------------------------
    def club(self, club_id: int) -> Club | None:
        return self._clubs.get(club_id)

    def clubs_meta(self) -> list[Club]:
        return list(self._clubs.values())

    def club_by_name(self, name: str) -> Club | None:
        target = normalize(name)
        for c in self._clubs.values():
            if normalize(c.name) == target:
                return c
        return None

    def competition_meta(self, name: str) -> Competition | None:
        return self._competitions.get(name)

    def competitions_meta(self) -> list[Competition]:
        return list(self._competitions.values())

    def rows_for_club(self, club_id: int) -> list[Player]:
        return [p for p in self._rows if p.club_id == club_id]

    def primary_club(self, player_id: str) -> int | None:
        """The club a player logged the most total minutes for (their 'real' club)."""
        mins: dict[int, float] = {}
        for r in self._by_player.get(player_id, []):
            if r.club_id is not None:
                mins[r.club_id] = mins.get(r.club_id, 0) + (r.metric("minutes") or 0)
        return max(mins, key=lambda k: mins[k]) if mins else None

    def rows_for_competition(self, competition: str) -> list[Player]:
        return [p for p in self._rows if p.competition == competition]
