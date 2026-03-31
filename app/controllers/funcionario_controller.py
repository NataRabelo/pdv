from flask import Blueprint,jsonify, request, render_template
from flask_jwt_extended import jwt_required, get_jwt

from app.services.funcionario_service import FuncionarioService

funcionario_bp = Blueprint("funcionario", __name__)


# =========================
# PAGE (HTML)
# =========================
@funcionario_bp.route("/view", methods=["GET"])
@jwt_required()
def pagina():
    return render_template("modulos/funcionario/funcionario.html")


# =========================
# LISTAR
# =========================
@funcionario_bp.route('/', methods=["GET"])
@jwt_required()
def listar():
    try:
        tenant_id = get_jwt().get("tenant_id")
        funcionarios = FuncionarioService.listar(tenant_id)

        return jsonify({
            "success": True,
            "data": [
                {
                    "id": f.id,
                    "nome": f.nome,
                    "cpf": f.cpf
                } for f in funcionarios
            ]
        })
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    

# =========================
# CRIAR
# =========================
@funcionario_bp.route("/", methods=["POST"])
@jwt_required()
def criar():
    try:
        tenant_id = get_jwt().get("tenant_id")
        data = request.json

        funcionario = FuncionarioService.criar(data, tenant_id)

        return jsonify({
            "success": True,
            "data": {
                "id": funcionario.id,
                "nome": funcionario.nome,
                "cpf": funcionario.cpf
            }
        }), 201
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


# =========================
# ATUALIZAR
# =========================
@funcionario_bp.route("/<int:funcionario_id>", methods=["PUT"])
@jwt_required()
def atualizar(funcionario_id):
    try:
        tenant_id = get_jwt().get("tenant_id")
        data = request.json

        FuncionarioService.atualizar(funcionario_id, data, tenant_id)

        return jsonify({
            "success": True,
            "message": "Atualizado com sucesso"
        })
    
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400 
    

# =========================
# DELETAR
# =========================
@funcionario_bp.route("/<int:funcionario_id>", methods=["DELETE"])
@jwt_required()
def deletar(funcionario_id):
    try:
        tenant_id = get_jwt().get("tenant_id")

        FuncionarioService.deletar(funcionario_id, tenant_id)

        return jsonify({
            "success": True,
            "message": "Deletado com sucesso"
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400