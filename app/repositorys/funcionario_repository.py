from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.db import Funcionario, FuncionarioEmpresa

class FuncionarioRepository:

    @staticmethod
    def listar(tenant_id):
        return (
            FuncionarioEmpresa.query
            .options(
                joinedload(FuncionarioEmpresa.funcionario),
                joinedload(FuncionarioEmpresa.empresa)
            )
            .filter(FuncionarioEmpresa.tenant_id == tenant_id)
            .order_by(FuncionarioEmpresa.id.desc())
            .all()
        )
    
    @staticmethod
    def buscar_funcionario_empresa_por_id(funcionario_empresa_id, tenant_id):
        return (
            FuncionarioEmpresa.query
            .options(
                joinedload(FuncionarioEmpresa.funcionario),
                joinedload(FuncionarioEmpresa.empresa)
            )
            .filter(
                FuncionarioEmpresa.id == funcionario_empresa_id,
                FuncionarioEmpresa.tenant_id == tenant_id
            )
            .first()
        )
    
    @staticmethod
    def salvar():
        db.session.commit()

    @staticmethod
    def adicionar(obj):
        db.session.add(obj)

    @staticmethod
    def deletar(obj):
        db.session.delete(obj)

    @staticmethod
    def contar_cinculos_funcionario(funcionario_id, tenant_id):
        return (
            FuncionarioEmpresa.query
            .filter(
                FuncionarioEmpresa.funcionario_id == funcionario_id,
                FuncionarioEmpresa.tenant_id == tenant_id
            )
            .count()
        )

    @staticmethod
    def busca_funcionario_por_id(id: int):
        return Funcionario.query.filter_by(id=id).first()

    @staticmethod
    def busca_funcionario_por_usuario(usuario: str):
        return Funcionario.query.filter_by(usuario=usuario).first()