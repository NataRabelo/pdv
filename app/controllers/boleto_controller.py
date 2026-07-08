from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.security.decorators import permission_required
from app.services.acesso_empresa_service import AcessoEmpresaService
from app.services.boleto_service import BoletoService

boleto_bp = Blueprint("boleto", __name__)


@boleto_bp.route("/bancos-emissores", methods=["GET"])
@jwt_required()
@permission_required("visualizar_financeiro")
def listar_bancos_emissores():
    try:
        tenant_id = get_jwt().get("tenant_id")
        funcionario_id = int(get_jwt_identity())
        escopo = AcessoEmpresaService.obter_escopo(funcionario_id, tenant_id)
        empresa_id = request.args.get("empresa_id", type=int)
        ativo = request.args.get("ativo", default=None, type=lambda v: v.lower() == "true") if request.args.get("ativo") is not None else None
        dados = BoletoService.listar_bancos_emissores(tenant_id, escopo, empresa_id=empresa_id, ativo=ativo)
        return jsonify({"success": True, "data": dados})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@boleto_bp.route("/configuracoes-parcelamento", methods=["GET"])
@jwt_required()
@permission_required("visualizar_financeiro")
def listar_configuracoes_parcelamento():
    try:
        tenant_id = get_jwt().get("tenant_id")
        funcionario_id = int(get_jwt_identity())
        escopo = AcessoEmpresaService.obter_escopo(funcionario_id, tenant_id)
        empresa_id = request.args.get("empresa_id", type=int)
        ativo = request.args.get("ativo", default=None, type=lambda v: v.lower() == "true") if request.args.get("ativo") is not None else None
        dados = BoletoService.listar_configuracoes_parcelamento(tenant_id, escopo, empresa_id=empresa_id, ativo=ativo)
        return jsonify({"success": True, "data": dados})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@boleto_bp.route("/regras-juros-multa", methods=["GET"])
@jwt_required()
@permission_required("visualizar_financeiro")
def listar_regras_juros_multa():
    try:
        tenant_id = get_jwt().get("tenant_id")
        funcionario_id = int(get_jwt_identity())
        escopo = AcessoEmpresaService.obter_escopo(funcionario_id, tenant_id)
        empresa_id = request.args.get("empresa_id", type=int)
        dados = BoletoService.listar_regras_juros_multa(tenant_id, escopo, empresa_id=empresa_id)
        return jsonify({"success": True, "data": dados})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@boleto_bp.route("", methods=["GET"])
@jwt_required()
@permission_required("visualizar_financeiro")
def listar_boletos():
    try:
        tenant_id = get_jwt().get("tenant_id")
        funcionario_id = int(get_jwt_identity())
        escopo = AcessoEmpresaService.obter_escopo(funcionario_id, tenant_id)
        empresa_id = request.args.get("empresa_id", type=int)
        status = request.args.get("status", type=str)
        banco_emissor_id = request.args.get("banco_emissor_id", type=int)
        limite = request.args.get("limite", default=100, type=int)
        dados = BoletoService.listar_boletos(tenant_id, escopo, empresa_id=empresa_id, status=status, banco_emissor_id=banco_emissor_id, limite=limite)
        return jsonify({"success": True, "data": dados})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@boleto_bp.route("", methods=["POST"])
@jwt_required()
@permission_required("criar_lancamento_financeiro")
def criar_boleto():
    try:
        tenant_id = get_jwt().get("tenant_id")
        funcionario_id = int(get_jwt_identity())
        escopo = AcessoEmpresaService.obter_escopo(funcionario_id, tenant_id)
        data = request.get_json(silent=True) or {}
        boleto = BoletoService.criar_boleto(data, tenant_id, escopo, funcionario_id)
        return jsonify({"success": True, "message": "Boleto criado com sucesso.", "data": boleto}), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@boleto_bp.route("/<int:boleto_id>", methods=["GET"])
@jwt_required()
@permission_required("visualizar_financeiro")
def buscar_boleto(boleto_id):
    try:
        tenant_id = get_jwt().get("tenant_id")
        funcionario_id = int(get_jwt_identity())
        escopo = AcessoEmpresaService.obter_escopo(funcionario_id, tenant_id)
        empresa_id = request.args.get("empresa_id", type=int)
        boleto = BoletoService.buscar_boleto(tenant_id, escopo, boleto_id, empresa_id=empresa_id)
        return jsonify({"success": True, "data": boleto})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@boleto_bp.route("/<int:boleto_id>/baixar", methods=["POST"])
@jwt_required()
@permission_required("criar_lancamento_financeiro")
def baixar_boleto(boleto_id):
    try:
        tenant_id = get_jwt().get("tenant_id")
        funcionario_id = int(get_jwt_identity())
        escopo = AcessoEmpresaService.obter_escopo(funcionario_id, tenant_id)
        data = request.get_json(silent=True) or {}
        boleto = BoletoService.baixar_boleto(tenant_id, escopo, boleto_id, data, funcionario_id)
        return jsonify({"success": True, "message": "Baixa registrada.", "data": boleto})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@boleto_bp.route("/<int:boleto_id>/recalcular-juros", methods=["POST"])
@jwt_required()
@permission_required("criar_lancamento_financeiro")
def recalcular_juros(boleto_id):
    try:
        tenant_id = get_jwt().get("tenant_id")
        funcionario_id = int(get_jwt_identity())
        escopo = AcessoEmpresaService.obter_escopo(funcionario_id, tenant_id)
        data = request.get_json(silent=True) or {}
        boleto = BoletoService.recalcular_juros_multa(tenant_id, escopo, boleto_id, data_referencia=data.get("data_referencia"), funcionario_id=funcionario_id)
        return jsonify({"success": True, "message": "Juros e multa recalculados.", "data": boleto})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400
