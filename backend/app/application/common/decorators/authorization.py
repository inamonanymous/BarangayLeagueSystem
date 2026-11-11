from functools import wraps

from flask import session

from app.application.auth.services import AuthService
from app.application.common.responses.api_response import error_response


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        service = AuthService()
        user = service.get_current_user(user_id) if user_id else None

        if user is None:
            return error_response("Authentication required.", status_code=401)

        if not service.has_role(user, "Administrator"):
            return error_response(
                "You do not have permission to perform this action.",
                status_code=403,
            )

        return func(*args, **kwargs)

    return wrapper

def encoder_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        service = AuthService()
        user = service.get_current_user(user_id) if user_id else None

        if user is None:
            return error_response("Authentication required.", status_code=401)

        if not service.has_role(user, "Encoder"):
            return error_response(
                "You do not have permission to perform this action.",
                status_code=403,
            )

        return func(*args, **kwargs)

    return wrapper