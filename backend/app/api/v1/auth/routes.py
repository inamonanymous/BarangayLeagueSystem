from flask import Blueprint, request, session

from app.application.auth.services import AuthService
from app.application.common.responses.api_response import error_response, success_response

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")

    service = AuthService()
    try:
        user = service.login(username, password)
    except ValueError as exc:
        return error_response(str(exc), status_code=401)

    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role

    return success_response(message="Login successful.", data=user.to_dict())


@auth_bp.post("/logout")
def logout():
    session.clear()
    return success_response(message="Logout successful.")


@auth_bp.get("/me")
def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return error_response("Authentication required.", status_code=401)

    user = AuthService().get_current_user(user_id)
    if user is None:
        return error_response("Authentication required.", status_code=401)

    return success_response(message="User retrieved.", data=user.to_dict())
