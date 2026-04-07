from flask import Blueprint, jsonify, render_template, request
from flask_jwt_extended import get_jwt, jwt_required

from app.security.decorators import permission_required
from app.services.permission_service import PermissionService
from app.services.role_service import RoleService

role_bp = Blueprint("role", __name__)


@role_bp.route("/view", methods=["GET"])
@jwt_required()
def pagina():
    return render_template("modulos/role/role.html")


@role_bp.route("/", methods=["GET"])
@permission_required("visualizar_role")
def listar():
    try:
        tenant_id = get_jwt().get("tenant_id")
        roles = RoleService.listar(tenant_id)

        return jsonify({
            "success": True,
            "data": [
                {
                    "id": role.id,
                    "nome": role.nome,
                    "codigo": role.codigo,
                    "descricao": role.descricao,
                    "ativo": role.ativo,
                    "permission_ids": [link.permission.id for link in role.permissions_links if link.permission],
                    "permissions_text": " ".join(
                        [
                            f"{link.permission.nome or ''} {link.permission.codigo or ''}".strip()
                            for link in role.permissions_links if link.permission
                        ]
                    ),
                    "permissions": [
                        {
                            "id": link.permission.id,
                            "nome": link.permission.nome,
                            "codigo": link.permission.codigo,
                        }
                        for link in role.permissions_links if link.permission
                    ]
                }
                for role in roles
            ]
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@role_bp.route("/permissions-disponiveis", methods=["GET"])
@permission_required("visualizar_role")
def listar_permissions_disponiveis():
    try:
        tenant_id = get_jwt().get("tenant_id")
        permissions = PermissionService.listar(tenant_id)

        return jsonify({
            "success": True,
            "data": [
                {
                    "id": permission.id,
                    "nome": permission.nome,
                    "codigo": permission.codigo,
                    "descricao": permission.descricao,
                    "ativo": permission.ativo
                }
                for permission in permissions
            ]
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@role_bp.route("/", methods=["POST"])
@permission_required("criar_role")
def criar():
    try:
        tenant_id = get_jwt().get("tenant_id")
        data = request.get_json(silent=True) or {}
        role = RoleService.criar(data, tenant_id)

        return jsonify({
            "success": True,
            "data": {
                "id": role.id,
                "nome": role.nome,
                "codigo": role.codigo,
                "descricao": role.descricao,
                "ativo": role.ativo
            }
        }), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@role_bp.route("/<int:role_id>", methods=["PUT"])
@permission_required("editar_role")
def atualizar(role_id):
    try:
        tenant_id = get_jwt().get("tenant_id")
        data = request.get_json(silent=True) or {}
        role = RoleService.atualizar(role_id, data, tenant_id)

        return jsonify({
            "success": True,
            "data": {
                "id": role.id,
                "nome": role.nome,
                "codigo": role.codigo,
                "descricao": role.descricao,
                "ativo": role.ativo
            },
            "message": "Role atualizada com sucesso."
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@role_bp.route("/<int:role_id>", methods=["DELETE"])
@permission_required("excluir_role")
def deletar(role_id):
    try:
        tenant_id = get_jwt().get("tenant_id")
        RoleService.deletar(role_id, tenant_id)
        return jsonify({"success": True, "message": "Role excluida com sucesso."}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400
