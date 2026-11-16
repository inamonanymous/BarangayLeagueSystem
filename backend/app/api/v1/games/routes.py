from flask import Blueprint, request
from marshmallow import ValidationError

from app.application.common.decorators.authorization import admin_required
from app.application.common.responses.api_response import error_response, success_response
from app.application.games.services import GameService, ScheduleConflictError
from app.schemas.game_schema import RescheduleGameSchema, ScheduleGameSchema


games_bp = Blueprint("games", __name__)
schedule_game_schema = ScheduleGameSchema()
reschedule_game_schema = RescheduleGameSchema()


@games_bp.get("/season-sport-divisions/<int:assignment_id>/games")
def list_games(assignment_id: int):
    try:
        games = GameService().list_for_division(assignment_id)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    return success_response("Games retrieved.", [game.to_dict() for game in games])


@games_bp.post("/season-sport-divisions/<int:assignment_id>/games")
@admin_required
def schedule_game(assignment_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)
    try:
        game = GameService().schedule_game(assignment_id, **schedule_game_schema.load(payload))
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except ScheduleConflictError as exc:
        return error_response(str(exc), status_code=409)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    return success_response("Game scheduled.", game.to_dict(), status_code=201)


@games_bp.put("/games/<int:game_id>/schedule")
@admin_required
def reschedule_game(game_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)
    try:
        game = GameService().reschedule_game(game_id, **reschedule_game_schema.load(payload))
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except ScheduleConflictError as exc:
        return error_response(str(exc), status_code=409)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    return success_response("Game rescheduled.", game.to_dict())
