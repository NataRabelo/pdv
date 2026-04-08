from flask_jwt_extended import create_access_token, get_jwt

from app.models.db import PlatformOwner


def gerar_token(usuario, scope=None):
    auth_scope = scope or ("platform" if isinstance(usuario, PlatformOwner) else "tenant")

    if auth_scope == "platform":
        return create_access_token(
            identity=str(usuario.id),
            additional_claims={
                "auth_scope": "platform",
                "tenant_id": None,
                "usuario": usuario.usuario,
                "role_codigo": "platform_owner",
                "role_nome": "Dono da Plataforma",
                "nome": usuario.nome,
            }
        )

    role = usuario.role

    return create_access_token(
        identity=str(usuario.id),
        additional_claims={
            "auth_scope": "tenant",
            "tenant_id": usuario.tenant_id,
            "usuario": usuario.usuario,
            "role_codigo": role.codigo if role else None,
            "role_nome": role.nome if role else None,
            "nome": usuario.nome,
        }
    )


def get_auth_scope():
    claims = get_jwt()
    return claims.get("auth_scope") or "tenant"


def get_tenant_id(required=True):
    claims = get_jwt()
    tenant_id = claims.get("tenant_id")

    if required and not tenant_id:
        raise Exception("Tenant nao encontrado no token")

    return tenant_id
