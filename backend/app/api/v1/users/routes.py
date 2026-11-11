from flask import Blueprint, request
from marshmallow import ValidationError

from app.application.common.decorators.authorization import admin_required
from app.application.common.responses.api_response import error_response, success_response
from app.application.users.services import UserService
from app.schemas.user_schema import CreateUserSchema

users_bp = Blueprint("users", __name__, url_prefix="/users")
create_user_schema = CreateUserSchema()


@users_bp.post("/")
@admin_required
def create_user():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("A JSON request body is required.", status_code=400)

    try:
        data = create_user_schema.load(payload)
    except ValidationError as exc:
        return error_response("Validation failed.", status_code=400, errors=exc.messages)

    try:
        user = UserService().create_user(
            username=data["username"],
            password=data["password"],
            role_name=data["role"],
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=409)

    return success_response(
        message="User created successfully.",
        data=user.to_dict(),
        status_code=201,
    )