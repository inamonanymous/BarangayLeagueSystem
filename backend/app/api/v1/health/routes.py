from flask import Blueprint

from app.application.common.responses.api_response import success_response

health_bp = Blueprint("health", __name__, url_prefix="/health")


@health_bp.get("/")
def health_check():
    return success_response(message="Backend is healthy.", data={"status": "ok"})
