from flask import Blueprint, jsonify, render_template, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from app.services.produto_service import ProdutoService

produto_bp = Blueprint("produto", __name__)


# =========================
# PAGE
# =========================
@produto_bp.route("/view", methods=["GET"])
@jwt_required()
def pagina():
    return render_template("modulos/produto/produto.html")


# =========================
# LISTAR
# =========================
@produto_bp.route("/", methods=["GET"])
@jwt_required()
def listar():
    try:
        tenant_id = get_jwt().get("tenant_id")
        registros = ProdutoService.listar(tenant_id)

        return jsonify({
            "success": True,
            "data": [
                {
                    "id": item.id,
                    "produto_id": item.produto.id,
                    "empresa_id": item.empresa.id,
                    "empresa_nome": item.empresa.nome_fantasia,
                    "categoria_id": item.produto.categoria.id if item.produto.categoria else None,
                    "categoria_nome": item.produto.categoria.nome if item.produto.categoria else "",
                    "nome": item.produto.nome,
                    "descricao": item.produto.descricao,
                    "codigo_barras": item.produto.codigo_barras,
                    "possui_ncm": item.produto.possui_ncm,
                    "ncm": item.produto.ncm,
                    "estoque_atual": str(item.estoque_atual),
                    "estoque_minimo": str(item.estoque_minimo),
                    "valor_compra": str(item.valor_compra),
                    "valor_venda": str(item.valor_venda),
                    "ativo": item.ativo
                }
                for item in registros
            ]
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# =========================
# AUXILIARES FORM
# =========================
@produto_bp.route("/auxiliares", methods=["GET"])
@jwt_required()
def auxiliares():
    try:
        tenant_id = get_jwt().get("tenant_id")

        categorias = ProdutoService.listar_categorias(tenant_id)
        empresas = ProdutoService.listar_empresas(tenant_id)

        return jsonify({
            "success": True,
            "data": {
                "categorias": [
                    {"id": c.id, "nome": c.nome}
                    for c in categorias
                ],
                "empresas": [
                    {"id": e.id, "nome": e.nome_fantasia}
                    for e in empresas
                ]
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


# =========================
# CRIAR
# =========================
@produto_bp.route("/", methods=["POST"])
@jwt_required()
def criar():
    try:
        tenant_id = get_jwt().get("tenant_id")
        funcionario_id = get_jwt_identity()
        data = request.get_json()

        item = ProdutoService.criar(data, tenant_id, funcionario_id)

        return jsonify({
            "success": True,
            "data": {
                "id": item.id,
                "produto_id": item.produto.id,
                "empresa_id": item.empresa.id,
                "empresa_nome": item.empresa.nome_fantasia,
                "categoria_id": item.produto.categoria.id if item.produto.categoria else None,
                "categoria_nome": item.produto.categoria.nome if item.produto.categoria else "",
                "nome": item.produto.nome,
                "descricao": item.produto.descricao,
                "codigo_barras": item.produto.codigo_barras,
                "possui_ncm": item.produto.possui_ncm,
                "ncm": item.produto.ncm,
                "estoque_atual": str(item.estoque_atual),
                "estoque_minimo": str(item.estoque_minimo),
                "valor_compra": str(item.valor_compra),
                "valor_venda": str(item.valor_venda),
                "ativo": item.ativo
            }
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


# =========================
# ATUALIZAR
# =========================
@produto_bp.route("/<int:produto_empresa_id>", methods=["PUT"])
@jwt_required()
def atualizar(produto_empresa_id):
    try:
        tenant_id = get_jwt().get("tenant_id")
        data = request.get_json()

        item = ProdutoService.atualizar(produto_empresa_id, data, tenant_id)

        return jsonify({
            "success": True,
            "data": {
                "id": item.id,
                "produto_id": item.produto.id,
                "empresa_id": item.empresa.id,
                "empresa_nome": item.empresa.nome_fantasia,
                "categoria_id": item.produto.categoria.id if item.produto.categoria else None,
                "categoria_nome": item.produto.categoria.nome if item.produto.categoria else "",
                "nome": item.produto.nome,
                "descricao": item.produto.descricao,
                "codigo_barras": item.produto.codigo_barras,
                "possui_ncm": item.produto.possui_ncm,
                "ncm": item.produto.ncm,
                "estoque_atual": str(item.estoque_atual),
                "estoque_minimo": str(item.estoque_minimo),
                "valor_compra": str(item.valor_compra),
                "valor_venda": str(item.valor_venda),
                "ativo": item.ativo
            },
            "message": "Produto atualizado com sucesso."
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


# =========================
# DELETAR
# =========================
@produto_bp.route("/<int:produto_empresa_id>", methods=["DELETE"])
@jwt_required()
def deletar(produto_empresa_id):
    try:
        tenant_id = get_jwt().get("tenant_id")
        ProdutoService.deletar(produto_empresa_id, tenant_id)

        return jsonify({
            "success": True,
            "message": "Produto deletado com sucesso."
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400