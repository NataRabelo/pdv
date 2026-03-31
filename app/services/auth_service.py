from app.security.password import verify_password
from app.repositorys.funcionario_repository import FuncionarioRepository


class AuthService:

    @staticmethod
    def logar(data: dict):
        usuario = data.get("usuario")
        senha = data.get("senha")

        if not usuario or not senha:
            raise ValueError("Usuário e senha são necessários")

        funcionario = FuncionarioRepository.busca_funcionario_por_usuario(usuario)

        if not funcionario or not verify_password(senha, funcionario.senha_hash):
            raise ValueError("Credenciais inválidas")

        if not funcionario.ativo:
            raise ValueError("Usuário inativo")

        return funcionario