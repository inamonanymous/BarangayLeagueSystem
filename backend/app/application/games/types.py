from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict


@dataclass(frozen=True)
class DivisionSnapshot:
    season_sport_id: int


@dataclass(frozen=True)
class SeasonSnapshot:
    season_status: str


@dataclass(frozen=True)
class TeamSnapshot:
    season_sport_division_id: int
    is_archived: bool


@dataclass(frozen=True)
class StandingTeam:
    id: int
    name: str
    is_archived: bool


@dataclass(frozen=True)
class GameSnapshot:
    id: int
    season_sport_division_id: int
    home_team_id: int
    away_team_id: int
    starts_at: datetime
    ends_at: datetime
    result_status: str
    home_score: int | None
    away_score: int | None
    finalized_at: datetime | None
    finalized_by: int | None


class GameData(TypedDict):
    id: int
    season_sport_division_id: int
    home_team_id: int
    away_team_id: int
    venue: str
    starts_at: str
    ends_at: str
    result_status: str
    home_score: int | None
    away_score: int | None
    finalized_at: str | None
    finalized_by: int | None


class StandingData(TypedDict):
    rank: int
    team_id: int
    team_name: str
    is_archived: bool
    wins: int
    losses: int
