from flask import Blueprint, request
from marshmallow import ValidationError

from app.application.common.decorators.authorization import admin_required
from app.application.common.responses.api_response import error_response, success_response
from app.application.season.policies import SeasonConflictError
from app.application.season.services import SeasonService
from app.application.catalogs.services import CatalogConflictError, CatalogService
from app.schemas.catalog_schema import AddDivisionToSeasonSportSchema, AddSportToSeasonSchema
from app.schemas.season_schema import CreateSeasonSchema, TransitionSeasonSchema

seasons_bp = Blueprint("seasons", __name__, url_prefix="/seasons")
create_season_schema = CreateSeasonSchema()
transition_season_schema = TransitionSeasonSchema()
add_sport_schema = AddSportToSeasonSchema()
add_division_schema = AddDivisionToSeasonSportSchema()


@seasons_bp.get("/")
def list_seasons():
    seasons = SeasonService().list_seasons()
    return success_response(
        message="Seasons retrieved.",
        data=[season.to_dict() for season in seasons],
    )


@seasons_bp.post("/")
@admin_required
def create_season():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)

    try:
        data = create_season_schema.load(payload)
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)

    try:
        season = SeasonService().create_season(**data)
    except SeasonConflictError as exc:
        return error_response(str(exc), status_code=409)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)

    return success_response(
        message="Season created successfully.",
        data=season.to_dict(),
        status_code=201,
    )


@seasons_bp.patch("/<int:season_id>/status")
@admin_required
def transition_season(season_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)

    try:
        data = transition_season_schema.load(payload)
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)

    try:
        season = SeasonService().transition_season(
            season_id,
            data["season_status"],
        )
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except SeasonConflictError as exc:
        return error_response(str(exc), status_code=409)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)

    return success_response(
        message="Season status updated.",
        data=season.to_dict(),
    )


@seasons_bp.get("/<int:season_id>/configuration")
def get_season_configuration(season_id: int):
    try:
        configuration = CatalogService().get_season_configuration(season_id)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    return success_response("Season configuration retrieved.", configuration)


@seasons_bp.post("/<int:season_id>/sports")
@admin_required
def add_sport_to_season(season_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)
    try:
        data = add_sport_schema.load(payload)
        association = CatalogService().add_sport_to_season(season_id, data["sport_id"])
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except CatalogConflictError as exc:
        return error_response(str(exc), status_code=409)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    return success_response("Sport added to season.", association.to_dict(), status_code=201)


@seasons_bp.post("/sports/<int:season_sport_id>/divisions")
@admin_required
def add_division_to_season_sport(season_sport_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)
    try:
        data = add_division_schema.load(payload)
        association = CatalogService().add_division_to_season_sport(
            season_sport_id,
            data["division_id"],
        )
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except CatalogConflictError as exc:
        return error_response(str(exc), status_code=409)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    return success_response("Division added to season sport.", association.to_dict(), status_code=201)


@seasons_bp.delete("/<int:season_id>/sports/<int:season_sport_id>")
@admin_required
def remove_sport_from_season(season_id: int, season_sport_id: int):
    try:
        CatalogService().remove_sport_from_season(season_id, season_sport_id)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    return success_response("Sport removed from season.")


@seasons_bp.delete("/sports/<int:season_sport_id>/divisions/<int:assignment_id>")
@admin_required
def remove_division_from_season_sport(season_sport_id: int, assignment_id: int):
    try:
        CatalogService().remove_division_from_season_sport(
            season_sport_id,
            assignment_id,
        )
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    return success_response("Division removed from season sport.")