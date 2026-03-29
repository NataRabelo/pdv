from flask_jwt_extended import create_access_token, get_jwt

def gerar_token(usuario):
    return create_access_token(
        identity=str(usuario.id),
        additional_claims={
            "tenant_id": usuario.tenant_id,
            "usuario": usuario.usuario
        }
    )

def get_tenant_id():
    claims = get_jwt()
    tenant_id = claims.get('tenant_id')

    if not tenant_id:
        raise Exception("Tenant não encontrado no token")

    return tenant_id