from flask import Blueprint, jsonify, render_template, request

from app.security.decorators import platform_owner_required
from app.services.platform_service import PlatformService

platform_bp = Blueprint("platform", __name__)


@platform_bp.route("/platform/home", methods=["GET"])
@platform_owner_required()
def home():
    return render_template("pages/platform_home.html")


@platform_bp.route("/api/platform/tenants", methods=["GET"])
@platform_owner_required(api=True)
def listar_tenants():
    try:
        tenants = PlatformService.listar_tenants()
        return jsonify({"success": True, "data": tenants})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@platform_bp.route("/api/platform/tenants", methods=["POST"])
@platform_owner_required(api=True)
def criar_tenant():
    try:
        data = request.get_json(silent=True) or {}
        tenant = PlatformService.criar_tenant(data)
        return jsonify({"success": True, "data": tenant}), 201
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@platform_bp.route("/api/platform/tenants/<int:tenant_id>/empresas", methods=["POST"])
@platform_owner_required(api=True)
def criar_empresa(tenant_id):
    try:
        data = request.get_json(silent=True) or {}
        empresa = PlatformService.criar_empresa(tenant_id, data)
        return jsonify({"success": True, "data": empresa}), 201
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@platform_bp.route("/api/platform/tenants/<int:tenant_id>/admins", methods=["POST"])
@platform_owner_required(api=True)
def criar_admin(tenant_id):
    try:
        data = request.get_json(silent=True) or {}
        admin = PlatformService.criar_admin(tenant_id, data)
        return jsonify({"success": True, "data": admin}), 201
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
