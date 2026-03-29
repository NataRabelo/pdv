from flask import Blueprint, request, jsonify
from app.services.categoria_service import CategoriaService
from flask_jwt_extended import jwt_required

categoria_bp = Blueprint("categoria", __name__)


# LISTAR
@categoria_bp.route("/api/categorias", methods=["GET"])
@jwt_required()
def listar():
    try:
        categorias = CategoriaService.listar()

        return jsonify({
            "success": True,
            "data": [
                {
                    "id": c.id,
                    "nome": c.nome,
                    "descricao": c.descricao
                } for c in categorias
            ]
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


# CRIAR
@categoria_bp.route("/api/categorias", methods=["POST"])
@jwt_required()
def cadastrar():
    try:
        data = request.get_json()

        categoria = CategoriaService.cadastrar(data)

        return jsonify({
            "success": True,
            "data": {
                "id": categoria.id,
                "nome": categoria.nome,
                "descricao": categoria.descricao
            },
            "message": "Categoria criada com sucesso"
        }), 201

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400


# ATUALIZAR
@categoria_bp.route("/api/categorias/<int:id>", methods=["PUT"])
@jwt_required()
def editar(id):
    try:
        data = request.get_json()

        categoria = CategoriaService.atualizar(data, id)

        return jsonify({
            "success": True,
            "data": {
                "id": categoria.id,
                "nome": categoria.nome,
                "descricao": categoria.descricao
            },
            "message": "Categoria atualizada"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400


# DELETAR
@categoria_bp.route("/api/categorias/<int:id>", methods=["DELETE"])
@jwt_required()
def deletar(id):
    try:
        CategoriaService.deletar(id)

        return jsonify({
            "success": True,
            "message": "Categoria deletada"
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 400