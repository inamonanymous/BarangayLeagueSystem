from typing import TypedDict


class StatisticDefinitionInput(TypedDict):
    name: str
    abbreviation: str
    required: bool
    is_scoring: bool


class StatisticDefinition(StatisticDefinitionInput):
    id: int


class StatisticConfiguration(TypedDict):
    season_sport_id: int
    locked: bool
    allow_team_points: bool
    types: list[StatisticDefinition]


class ParticipantInput(TypedDict):
    player_id: int
    status: str | None
    values: dict[str, str]


class TeamStatisticsInput(TypedDict):
    team_id: int
    team_points: int | None
    players: list[ParticipantInput]


class ParticipantStatistics(ParticipantInput):
    name: str
    jersey_number: str


class TeamStatistics(TypedDict):
    team_id: int
    name: str
    team_points: int | None
    players: list[ParticipantStatistics]


class GameStatistics(TypedDict):
    configuration: StatisticConfiguration
    teams: list[TeamStatistics]
