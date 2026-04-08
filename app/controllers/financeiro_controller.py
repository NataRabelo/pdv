from flask import Blueprint, jsonify, render_template, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.security.decorators import permission_required
from app.services.acesso_empresa_service import AcessoEmpresaService
from app.services.financeiro_service import FinanceiroService

financeiro_bp = Blueprint("financeiro", __name__)


@financeiro_bp.route("/view", methods=["GET"])
@jwt_required()
def pagina():
    return render_template("modulos/financeiro/financeiro.html")


@financeiro_bp.route("/auxiliares", methods=["GET"])
@permission_required("visualizar_financeiro")
def auxiliares():
    try:
        tenant_id = get_jwt().get("tenant_id")
        funcionario_id = int(get_jwt_identity())
        escopo = AcessoEmpresaService.obter_escopo(funcionario_id, tenant_id)
        dados = FinanceiroService.listar_auxiliares(tenant_id, escopo)
        return jsonify({"success": True, "data": dados})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@financeiro_bp.route("/dashboard", methods=["GET"])
@permission_required("visualizar_financeiro")
def dashboard():
    try:
        tenant_id = get_jwt().get("tenant_id")
        funcionario_id = int(get_jwt_identity())
        empresa_id = request.args.get("empresa_id", type=int)
        periodo_dias = request.args.get("periodo_dias", default=30, type=int)
        escopo = AcessoEmpresaService.obter_escopo(funcionario_id, tenant_id)
        dados = FinanceiroService.obter_dashboard(
            tenant_id=tenant_id,
            escopo=escopo,
            empresa_id=empresa_id,
            periodo_dias=periodo_dias,
        )
        return jsonify({"success": True, "data": dados})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@financeiro_bp.route("/lancamentos", methods=["GET"])
@permission_required("visualizar_financeiro")
def listar_lancamentos():
    try:
        tenant_id = get_jwt().get("tenant_id")
        funcionario_id = int(get_jwt_identity())
        empresa_id = request.args.get("empresa_id", type=int)
        tipo = request.args.get("tipo", type=str)
        data_inicio = request.args.get("data_inicio", type=str)
        data_fim = request.args.get("data_fim", type=str)
        limite = request.args.get("limite", default=100, type=int)
        escopo = AcessoEmpresaService.obter_escopo(funcionario_id, tenant_id)
        dados = FinanceiroService.listar_lancamentos(
            tenant_id=tenant_id,
            escopo=escopo,
            empresa_id=empresa_id,
            tipo=tipo,
            data_inicio=data_inicio,
            data_fim=data_fim,
            limite=limite,
        )
        return jsonify({"success": True, "data": dados})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@financeiro_bp.route("/lancamentos", methods=["POST"])
@permission_required("criar_lancamento_financeiro")
def criar_lancamento():
    try:
        tenant_id = get_jwt().get("tenant_id")
        funcionario_id = int(get_jwt_identity())
        escopo = AcessoEmpresaService.obter_escopo(funcionario_id, tenant_id)
        data = request.get_json(silent=True) or {}
        lancamento = FinanceiroService.criar_lancamento_manual(data, tenant_id, escopo, funcionario_id)

        return jsonify({
            "success": True,
            "message": "Lancamento financeiro registrado com sucesso.",
            "data": lancamento,
        }), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@financeiro_bp.route("/fechamentos", methods=["GET"])
@permission_required("visualizar_financeiro")
def listar_fechamentos():
    try:
        tenant_id = get_jwt().get("tenant_id")
        funcionario_id = int(get_jwt_identity())
        empresa_id = request.args.get("empresa_id", type=int)
        limite = request.args.get("limite", default=30, type=int)
        escopo = AcessoEmpresaService.obter_escopo(funcionario_id, tenant_id)
        dados = FinanceiroService.listar_fechamentos(
            tenant_id=tenant_id,
            escopo=escopo,
            empresa_id=empresa_id,
            limite=limite,
        )
        return jsonify({"success": True, "data": dados})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@financeiro_bp.route("/fechamentos", methods=["POST"])
@permission_required("fechar_caixa")
def criar_fechamento():
    try:
        tenant_id = get_jwt().get("tenant_id")
        funcionario_id = int(get_jwt_identity())
        escopo = AcessoEmpresaService.obter_escopo(funcionario_id, tenant_id)
        data = request.get_json(silent=True) or {}
        fechamento = FinanceiroService.criar_fechamento(data, tenant_id, escopo, funcionario_id)

        return jsonify({
            "success": True,
            "message": "Fechamento de caixa registrado com sucesso.",
            "data": fechamento,
        }), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400
