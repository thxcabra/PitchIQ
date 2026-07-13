"""Test fixtures: build a PlayerRepository from a tiny in-memory dataset."""
from __future__ import annotations

import csv

import pytest

from app.data.repository import PlayerRepository
from app.models.domain import METRIC_COLUMNS

_IDENTITY = ["row_id", "player_id", "name", "position", "role", "age", "nation",
             "height_cm", "foot", "club", "competition", "competition_id",
             "competition_type", "country", "confederation", "market_value_eur"]
_HEADER = _IDENTITY + list(METRIC_COLUMNS)


def _row(**over) -> dict:
    base = {c: 0 for c in _HEADER}
    base.update({"nation": "", "height_cm": "", "foot": "", "market_value_eur": "",
                 "competition_type": "League", "country": "Testland", "confederation": "test"})
    base.update(over)
    return base


def build_repo(rows: list[dict], tmp_path) -> PlayerRepository:
    path = tmp_path / "players.csv"
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=_HEADER)
        w.writeheader()
        for r in rows:
            w.writerow(_row(**r))
    return PlayerRepository(path)


@pytest.fixture
def sample_repo(tmp_path) -> PlayerRepository:
    # Five forwards in one competition with a clean goals_per90 gradient, for percentile math.
    rows = [
        {"row_id": f"f{i}", "player_id": f"f{i}", "name": f"Fwd {i}", "position": "Forward",
         "role": "Centre-Forward", "age": 20 + i, "club": f"Club {i}",
         "competition": "Test League", "competition_id": "TL", "country": "Testland",
         "market_value_eur": (i + 1) * 10_000_000, "minutes": 2000, "matches": 25,
         "goals_per90": round(0.1 * (i + 1), 3), "assists_per90": round(0.05 * (5 - i), 3)}
        for i in range(5)
    ]
    # a different competition / position, to make sure cohorts don't leak
    rows.append({"row_id": "m1", "player_id": "m1", "name": "Mid 1", "position": "Midfielder",
                 "role": "Central Midfield", "age": 25, "club": "Other",
                 "competition": "Other League", "competition_id": "OL", "country": "Otherland",
                 "minutes": 2000, "matches": 25, "goals_per90": 5.0})
    return build_repo(rows, tmp_path)
