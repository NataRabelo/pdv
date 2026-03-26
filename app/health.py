from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)

# HEALTHCHECK ENDPOINT
@health_bp.route("/health", methods=["GET"])
def healthcheck():
    return jsonify(
        status="ok",
        service="BlueOcean API",
        version="1.0.0"
        ), 200