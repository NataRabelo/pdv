from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from app.services.acesso_empresa_service import AcessoEmpresaService


def permission_required(permissao_codigo):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
                tenant_id = get_jwt().get("tenant_id")
                funcionario_id = int(get_jwt_identity())
                escopo = AcessoEmpresaService.obter_escopo(funcionario_id, tenant_id)

                if not AcessoEmpresaService.possui_permissao(escopo, permissao_codigo):
                    return jsonify({
                        "success": False,
                        "message": "Voce nao tem permissao para executar esta acao."
                    }), 403

                return fn(*args, **kwargs)
            except PermissionError as e:
                return jsonify({
                    "success": False,
                    "message": str(e)
                }), 403

        return wrapper

    return decorator
