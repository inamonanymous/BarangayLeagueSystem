from flask import Blueprint, request
from marshmallow import ValidationError

from app.application.catalogs.services import CatalogConflictError, CatalogService
from app.application.common.decorators.authorization import admin_required
from app.application.common.responses.api_response import error_response, success_response
from app.schemas.catalog_schema import (
    CreateDivisionSchema,
    CreateSportSchema,
    UpdateDivisionSchema,
    UpdateSportSchema,
)

catalogs_bp = Blueprint("catalogs", __name__, url_prefix="/catalogs")
create_sport_schema = CreateSportSchema()
create_division_schema = CreateDivisionSchema()
update_sport_schema = UpdateSportSchema()
update_division_schema = UpdateDivisionSchema()


@catalogs_bp.get("/sports")
def list_sports():
    sports = CatalogService().list_sports()
    return success_response("Sports retrieved.", [sport.to_dict() for sport in sports])


@catalogs_bp.post("/sports")
@admin_required
def create_sport():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)
    try:
        data = create_sport_schema.load(payload)
        sport = CatalogService().create_sport(**data)
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)
    except CatalogConflictError as exc:
        return error_response(str(exc), status_code=409)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    return success_response("Sport created.", sport.to_dict(), status_code=201)


@catalogs_bp.put("/sports/<int:sport_id>")
@admin_required
def update_sport(sport_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)
    try:
        sport = CatalogService().update_sport(sport_id, **update_sport_schema.load(payload))
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except CatalogConflictError as exc:
        return error_response(str(exc), status_code=409)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    return success_response("Sport updated.", sport.to_dict())


@catalogs_bp.delete("/sports/<int:sport_id>")
@admin_required
def delete_sport(sport_id: int):
    try:
        CatalogService().delete_sport(sport_id)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except CatalogConflictError as exc:
        return error_response(str(exc), status_code=409)
    return success_response("Sport deleted.")


@catalogs_bp.get("/divisions")
def list_divisions():
    divisions = CatalogService().list_divisions()
    return success_response("Divisions retrieved.", [division.to_dict() for division in divisions])


@catalogs_bp.post("/divisions")
@admin_required
def create_division():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)
    try:
        data = create_division_schema.load(payload)
        division = CatalogService().create_division(**data)
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)
    except CatalogConflictError as exc:
        return error_response(str(exc), status_code=409)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    return success_response("Division created.", division.to_dict(), status_code=201)


@catalogs_bp.put("/divisions/<int:division_id>")
@admin_required
def update_division(division_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)
    try:
        division = CatalogService().update_division(
            division_id,
            **update_division_schema.load(payload),
        )
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except CatalogConflictError as exc:
        return error_response(str(exc), status_code=409)
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    return success_response("Division updated.", division.to_dict())


@catalogs_bp.delete("/divisions/<int:division_id>")
@admin_required
def delete_division(division_id: int):
    try:
        CatalogService().delete_division(division_id)
    except LookupError as exc:
        return error_response(str(exc), status_code=404)
    except CatalogConflictError as exc:
        return error_response(str(exc), status_code=409)
    return success_response("Division deleted.")