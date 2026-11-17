from flask import Blueprint, request
from marshmallow import ValidationError

from app.application.common.decorators.authorization import admin_or_encoder_required, admin_required
from app.application.common.responses.api_response import error_response, success_response
from app.application.statistics.services import StatisticsService
from app.schemas.statistics_schema import GameStatisticsSchema, StatisticConfigurationSchema


statistics_bp = Blueprint("statistics", __name__)


@statistics_bp.get("/season-sports/<int:sport_id>/statistics-configuration")
def configuration(sport_id: int):
    try:
        data = StatisticsService().configuration(sport_id)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    return success_response("Statistics configuration retrieved.", data)


@statistics_bp.put("/season-sports/<int:sport_id>/statistics-configuration")
@admin_required
def update_configuration(sport_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)
    try:
        data = StatisticConfigurationSchema().load(payload)
        result = StatisticsService().update_configuration(sport_id, data["types"], data["allow_team_points"])
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    return success_response("Statistics configuration saved.", result)


@statistics_bp.get("/games/<int:game_id>/statistics")
def game_statistics(game_id: int):
    try:
        result = StatisticsService().game_statistics(game_id)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    return success_response("Game statistics retrieved.", result)


@statistics_bp.put("/games/<int:game_id>/statistics")
@admin_or_encoder_required
def save_game_statistics(game_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)
    try:
        data = GameStatisticsSchema().load(payload)
        result = StatisticsService().save_game_statistics(game_id, data["teams"])
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    return success_response("Game statistics saved.", result)
