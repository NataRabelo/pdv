from flask import Blueprint, jsonify
from sqlalchemy import text

from app.extensions import db

health_bp = Blueprint("health", __name__, url_prefix="/api")

@health_bp.route("/health", methods=["GET"])
def healthcheck():
    return jsonify({
        "status": "ok",
        "service": "OceanBlue API",
        "version": "1.0.0"
    }), 200


@health_bp.route("/ready", methods=["GET"])
def readiness():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({
            "status": "ready",
            "database": "ok",
            "service": "OceanBlue API",
        }), 200
    except Exception as exc:
        return jsonify({
            "status": "not_ready",
            "database": "error",
            "message": str(exc),
        }), 503
