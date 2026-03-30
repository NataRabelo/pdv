from flask import Blueprint, jsonify, request, render_template
from flask_jwt_extended import jwt_required, get_jwt

from app.services.categoria_service import CategoriaService

categoria_bp = Blueprint("categoria", __name__)


# =========================
# PAGE (HTML)
# =========================
@categoria_bp.route("/view", methods=["GET"])
@jwt_required()
def pagina():
    return render_template("categoria/categoria.html")


# =========================
# LISTAR
# =========================
@categoria_bp.route("/", methods=["GET"])
@jwt_required()
def listar():
    try:
        tenant_id = get_jwt().get("tenant_id")

        categorias = CategoriaService.listar(tenant_id)

        return jsonify({
            "success": True,
            "data": [
                {
                    "id": c.id,
                    "nome": c.nome,
                    "descricao": c.descricao
                } for c in categorias
            ]
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# =========================
# CRIAR
# =========================
@categoria_bp.route("/", methods=["POST"])
@jwt_required()
def criar():
    try:
        tenant_id = get_jwt().get("tenant_id")
        data = request.json

        categoria = CategoriaService.criar(data, tenant_id)

        return jsonify({
            "success": True,
            "data": {
                "id": categoria.id,
                "nome": categoria.nome,
                "descricao": categoria.descricao
            }
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


# =========================
# ATUALIZAR
# =========================
@categoria_bp.route("/<int:categoria_id>", methods=["PUT"])
@jwt_required()
def atualizar(categoria_id):
    try:
        tenant_id = get_jwt().get("tenant_id")
        data = request.json

        CategoriaService.atualizar(categoria_id, data, tenant_id)

        return jsonify({
            "success": True,
            "message": "Atualizado com sucesso"
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


# =========================
# DELETAR
# =========================
@categoria_bp.route("/<int:categoria_id>", methods=["DELETE"])
@jwt_required()
def deletar(categoria_id):
    try:
        tenant_id = get_jwt().get("tenant_id")

        CategoriaService.deletar(categoria_id, tenant_id)

        return jsonify({
            "success": True,
            "message": "Deletado com sucesso"
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400