from flask_jwt_extended import create_access_token

def gerar_token(usuario):
    additional_claims = {
        "tenant_id": usuario.tenant_id,
        "usuario": usuario.usuario,
    }

    return create_access_token(
        identity=str(usuario.id),
        additional_claims=additional_claims
    )