from flask import Blueprint, request, session
from marshmallow import ValidationError

from app.application.common.decorators.authorization import admin_required
from app.application.common.responses.api_response import error_response, success_response
from app.application.players.services import PlayerConflictError, PlayerService
from app.schemas.player_schema import ArchivePlayerSchema, CreatePlayerSchema, UpdatePlayerSchema

players_bp = Blueprint("players", __name__, url_prefix="/players")
create_player_schema = CreatePlayerSchema()
update_player_schema = UpdatePlayerSchema()
archive_player_schema = ArchivePlayerSchema()


@players_bp.get("/")
@admin_required
def list_players():
    include_archived = request.args.get("include_archived", "false").lower() == "true"
    players = PlayerService().list_players(include_archived=include_archived)
    return success_response("Players retrieved.", [player.to_dict() for player in players])


@players_bp.get("/<int:player_id>")
@admin_required
def get_player(player_id: int):
    try:
        player = PlayerService().get_player(player_id)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    return success_response("Player retrieved.", player.to_dict())


@players_bp.post("/")
@admin_required
def create_player():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)
    try:
        player = PlayerService().create_player(**create_player_schema.load(payload))
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)
    except PlayerConflictError as exc:
        return error_response(str(exc), status_code=409)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    return success_response("Player created.", player.to_dict(), status_code=201)


@players_bp.put("/<int:player_id>")
@admin_required
def update_player(player_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)
    try:
        player = PlayerService().update_player(
            player_id,
            **update_player_schema.load(payload),
        )
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except PlayerConflictError as exc:
        return error_response(str(exc), status_code=409)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    return success_response("Player updated.", player.to_dict())


@players_bp.patch("/<int:player_id>/archive")
@admin_required
def set_player_archive_state(player_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)
    try:
        data = archive_player_schema.load(payload)
        player = PlayerService().set_archived(
            player_id,
            data["is_archived"],
            session["user_id"],
        )
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    return success_response("Player archive state updated.", player.to_dict())


@players_bp.delete("/<int:player_id>")
@admin_required
def archive_player(player_id: int):
    try:
        player = PlayerService().set_archived(player_id, True, session["user_id"])
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    return success_response("Player archived.", player.to_dict())
