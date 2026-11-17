from flask import Blueprint

from .auth.routes import auth_bp
from .health.routes import health_bp
from .games.routes import games_bp
from .players.routes import players_bp
from .seasons.routes import seasons_bp
from .teams.routes import teams_bp
from .users.routes import users_bp
from .statistics.routes import statistics_bp


def register_blueprints(app):
    api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")
    api_v1.register_blueprint(health_bp)
    api_v1.register_blueprint(games_bp)
    api_v1.register_blueprint(auth_bp)
    api_v1.register_blueprint(players_bp)
    api_v1.register_blueprint(seasons_bp)
    api_v1.register_blueprint(teams_bp)
    api_v1.register_blueprint(users_bp)
    api_v1.register_blueprint(statistics_bp)
    app.register_blueprint(api_v1)
