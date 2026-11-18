from flask import Flask

from app.config import get_config
from app.extensions import init_extensions
from app.api.v1 import register_blueprints
from app.session_cleanup import cleanup_expired_sessions
from app.domain.models.roles import Role
from app.domain.models.games import Game, GameResultReopening, ScheduleLock
from app.domain.models.seasons import Season
from app.domain.models.season_sports import SeasonSport
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.season_teams import SeasonTeam
from app.domain.models.players import Player
from app.domain.models.rosters import Roster
from app.domain.models.season_player_eligibilities import SeasonPlayerEligibility
from app.domain.models.users import User
from app.domain.models.statistics import (
    SportStatisticConfiguration, StatisticType, GameParticipant, PlayerGameStatistic, GameTeamPoints,
)


def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    init_extensions(app)
    register_blueprints(app)
    app.cli.add_command(cleanup_expired_sessions)

    return app
