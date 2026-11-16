from dataclasses import dataclass
from datetime import date
from typing import TypedDict


@dataclass(frozen=True)
class TeamSnapshot:
    id: int
    season_sport_division_id: int
    is_archived: bool


@dataclass(frozen=True)
class SeasonSnapshot:
    id: int
    season_status: str
    registration_start_date: date | None
    registration_end_date: date | None


@dataclass(frozen=True)
class DivisionSnapshot:
    maximum_roster_size: int


@dataclass(frozen=True)
class PlayerSnapshot:
    birthdate: date
    is_archived: bool


@dataclass(frozen=True)
class RosterSnapshot:
    id: int
    season_team_id: int


class PlayerData(TypedDict):
    id: int
    first_name: str
    middle_name: str | None
    last_name: str
    birthdate: str
    gender: str
    address: str
    is_archived: bool
    created_at: str | None
    updated_at: str | None


class RosterData(TypedDict):
    id: int
    season_team_id: int
    player_id: int
    jersey_number: str
    created_at: str | None
    updated_at: str | None


class RosterEntryData(RosterData):
    player: PlayerData
