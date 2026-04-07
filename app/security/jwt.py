from flask_jwt_extended import create_access_token, get_jwt


def gerar_token(usuario):
    role = usuario.role

    return create_access_token(
        identity=str(usuario.id),
        additional_claims={
            "tenant_id": usuario.tenant_id,
            "usuario": usuario.usuario,
            "role_codigo": role.codigo if role else None,
            "role_nome": role.nome if role else None,
        }
    )


def get_tenant_id():
    claims = get_jwt()
    tenant_id = claims.get("tenant_id")

    if not tenant_id:
        raise Exception("Tenant nao encontrado no token")

    return tenant_id
