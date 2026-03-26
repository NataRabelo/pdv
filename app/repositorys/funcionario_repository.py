from app.models.db import Funcionario

class FuncionarioRepository:

    @staticmethod
    def get_by_id(id: int):
        return Funcionario.query.filter_by(id=id).first()

    @staticmethod
    def get_by_usuario(usuario: str):
        return Funcionario.query.filter_by(usuario=usuario).first()