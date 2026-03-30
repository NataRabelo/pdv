from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__, url_prefix="/api")

@health_bp.route("/health", methods=["GET"])
def healthcheck():
    return jsonify({
        "status": "ok",
        "service": "OceanBlue API",
        "version": "1.0.0"
    }), 200