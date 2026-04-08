from app.repositorys.funcionario_repository import FuncionarioRepository
from app.repositorys.platform_repository import PlatformRepository
from app.security.password import verify_password


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
            return {"scope": "tenant", "user": funcionario}

        raise ValueError("Credenciais invalidas")
