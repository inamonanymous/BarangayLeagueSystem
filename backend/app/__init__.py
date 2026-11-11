from flask import Flask

from app.config import get_config
from app.extensions import init_extensions
from app.api.v1 import register_blueprints
from app.domain.models.roles import Role
from app.domain.models.divisions import Division
from app.domain.models.seasons import Season
from app.domain.models.season_sports import SeasonSport
from app.domain.models.season_sport_divisions import SeasonSportDivision
from app.domain.models.sports import Sport
from app.domain.models.users import User


def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    init_extensions(app)
    register_blueprints(app)

    return app
