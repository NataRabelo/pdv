from app.repositorys.funcionario_repository import FuncionarioRepository
from app.repositorys.platform_repository import PlatformRepository
from app.security.password import verify_password
from app.services.tenant_bootstrap_service import TenantBootstrapService
from app.extensions import db


class AuthService:

    @staticmethod
    def logar(data: dict):
        usuario = (data.get("usuario") or "").strip()
        senha = data.get("senha")

        if not usuario or not senha:
            raise ValueError("Usuario e senha sao necessarios")

        owner = PlatformRepository.buscar_owner_por_usuario(usuario)
        if owner and verify_password(senha, owner.senha_hash):
            if not owner.ativo:
                raise ValueError("Usuario inativo")
            return {"scope": "platform", "user": owner}

        funcionario = FuncionarioRepository.busca_funcionario_por_usuario(usuario)
        if funcionario and verify_password(senha, funcionario.senha_hash):
            if not funcionario.ativo:
                raise ValueError("Usuario inativo")
            if not funcionario.role or not funcionario.role.ativo:
                raise ValueError("Perfil de acesso inativo ou nao configurado.")
            try:
                TenantBootstrapService.garantir_permissoes_e_roles(funcionario.tenant_id)
                TenantBootstrapService.garantir_cadastros_operacionais(funcionario.tenant_id)
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise
            return {"scope": "tenant", "user": funcionario}

        raise ValueError("Credenciais invalidas")
