from flask import jsonify


def success_response(message: str = "Operation completed successfully.", data=None, status_code: int = 200):
    payload = {"message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status_code


def error_response(message: str = "An unexpected error occurred.", status_code: int = 500, errors=None):
    payload = {"message": message}
    if errors is not None:
        payload["errors"] = errors
    return jsonify(payload), status_code
