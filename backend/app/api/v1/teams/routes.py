from flask import Blueprint, request, session
from marshmallow import ValidationError

from app.application.common.decorators.authorization import admin_required
from app.application.common.responses.api_response import error_response, success_response
from app.application.teams.services import SeasonTeamConflictError, SeasonTeamService
from app.application.rosters.services import RosterConflictError, RosterService
from app.schemas.roster_schema import AddRosterPlayerSchema, UpdateRosterSchema
from app.schemas.season_team_schema import (
    ArchiveSeasonTeamSchema,
    RegisterSeasonTeamSchema,
    UpdateSeasonTeamSchema,
)

teams_bp = Blueprint("teams", __name__)
register_team_schema = RegisterSeasonTeamSchema()
update_team_schema = UpdateSeasonTeamSchema()
archive_team_schema = ArchiveSeasonTeamSchema()
add_roster_player_schema = AddRosterPlayerSchema()
update_roster_schema = UpdateRosterSchema()


@teams_bp.get("/season-sport-divisions/<int:assignment_id>/teams")
def list_teams(assignment_id: int):
    try:
        teams = SeasonTeamService().list_for_division(assignment_id)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    return success_response("Teams retrieved.", [team.to_dict() for team in teams])


@teams_bp.post("/season-sport-divisions/<int:assignment_id>/teams")
@admin_required
def register_team(assignment_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)

    try:
        data = register_team_schema.load(payload)
        team = SeasonTeamService().register_team(assignment_id, **data)
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except SeasonTeamConflictError as exc:
        return error_response(str(exc), status_code=409)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)

    return success_response("Team registered successfully.", team.to_dict(), status_code=201)


@teams_bp.put("/season-teams/<int:team_id>")
@admin_required
def update_team(team_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)
    try:
        team = SeasonTeamService().update_team(team_id, **update_team_schema.load(payload))
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except SeasonTeamConflictError as exc:
        return error_response(str(exc), status_code=409)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    return success_response("Team updated.", team.to_dict())


@teams_bp.delete("/season-teams/<int:team_id>")
@admin_required
def archive_team(team_id: int):
    try:
        team = SeasonTeamService().set_archived(team_id, True, session["user_id"])
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    return success_response("Team archived.", team.to_dict())


@teams_bp.patch("/season-teams/<int:team_id>/archive")
@admin_required
def set_team_archive_state(team_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)
    try:
        data = archive_team_schema.load(payload)
        team = SeasonTeamService().set_archived(
            team_id,
            data["is_archived"],
            session["user_id"],
        )
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    return success_response("Team archive state updated.", team.to_dict())


@teams_bp.get("/season-teams/<int:team_id>/roster")
def list_roster(team_id: int):
    try:
        entries = RosterService().list_for_team(team_id)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    return success_response("Roster retrieved.", entries)


@teams_bp.post("/season-teams/<int:team_id>/roster")
@admin_required
def add_roster_player(team_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)
    try:
        roster = RosterService().add_player(
            team_id,
            actor_id=session["user_id"],
            **add_roster_player_schema.load(payload),
        )
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except RosterConflictError as exc:
        return error_response(str(exc), status_code=409)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    return success_response("Player added to roster.", roster.to_dict(), status_code=201)


@teams_bp.put("/season-teams/<int:team_id>/roster/<int:roster_id>")
@admin_required
def update_roster_entry(team_id: int, roster_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)
    try:
        data = update_roster_schema.load(payload)
        roster = RosterService().update_jersey_number(
            team_id,
            roster_id,
            data["jersey_number"],
        )
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except RosterConflictError as exc:
        return error_response(str(exc), status_code=409)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    return success_response("Roster entry updated.", roster.to_dict())


@teams_bp.delete("/season-teams/<int:team_id>/roster/<int:roster_id>")
@admin_required
def remove_roster_player(team_id: int, roster_id: int):
    try:
        RosterService().remove_player(team_id, roster_id)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    return success_response("Player removed from roster.")
