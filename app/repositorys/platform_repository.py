from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.db import Empresa, Funcionario, FuncionarioEmpresa, PlatformOwner, Role, Tenant


class PlatformRepository:

    @staticmethod
    def buscar_owner_por_usuario(usuario):
        return PlatformOwner.query.filter(PlatformOwner.usuario == usuario).first()

    @staticmethod
    def buscar_owner_por_id(owner_id):
        return PlatformOwner.query.filter(PlatformOwner.id == owner_id).first()

    @staticmethod
    def listar_tenants():
        return (
            Tenant.query
            .options(
                joinedload(Tenant.empresas),
                joinedload(Tenant.funcionarios).joinedload(Funcionario.role)
            )
            .order_by(Tenant.id.desc())
            .all()
        )

    @staticmethod
    def buscar_tenant_por_id(tenant_id):
        return (
            Tenant.query
            .options(
                joinedload(Tenant.empresas),
                joinedload(Tenant.funcionarios).joinedload(Funcionario.role)
            )
            .filter(Tenant.id == tenant_id)
            .first()
        )

    @staticmethod
    def buscar_tenant_por_nome(nome):
        return Tenant.query.filter(Tenant.nome == nome).first()

    @staticmethod
    def buscar_empresa_por_id(empresa_id, tenant_id):
        return (
            Empresa.query
            .filter(
                Empresa.id == empresa_id,
                Empresa.tenant_id == tenant_id
            )
            .first()
        )

    @staticmethod
    def buscar_empresa_por_cnpj(cnpj, tenant_id):
        return (
            Empresa.query
            .filter(
                Empresa.cnpj == cnpj,
                Empresa.tenant_id == tenant_id
            )
            .first()
        )

    @staticmethod
    def buscar_funcionario_por_usuario(usuario, tenant_id):
        return (
            Funcionario.query
            .filter(
                Funcionario.usuario == usuario,
                Funcionario.tenant_id == tenant_id
            )
            .first()
        )

    @staticmethod
    def buscar_funcionario_por_cpf(cpf, tenant_id):
        return (
            Funcionario.query
            .filter(
                Funcionario.cpf == cpf,
                Funcionario.tenant_id == tenant_id
            )
            .first()
        )

    @staticmethod
    def buscar_role_por_codigo(codigo, tenant_id):
        return (
            Role.query
            .filter(
                Role.codigo == codigo,
                Role.tenant_id == tenant_id
            )
            .first()
        )

    @staticmethod
    def listar_empresas_por_tenant(tenant_id):
        return (
            Empresa.query
            .filter(Empresa.tenant_id == tenant_id)
            .order_by(Empresa.nome_fantasia.asc())
            .all()
        )

    @staticmethod
    def listar_admins_por_tenant(tenant_id):
        return (
            Funcionario.query
            .options(joinedload(Funcionario.role))
            .filter(Funcionario.tenant_id == tenant_id)
            .order_by(Funcionario.nome.asc())
            .all()
        )

    @staticmethod
    def buscar_vinculo_funcionario_empresa(tenant_id, funcionario_id, empresa_id):
        return (
            FuncionarioEmpresa.query
            .filter(
                FuncionarioEmpresa.tenant_id == tenant_id,
                FuncionarioEmpresa.funcionario_id == funcionario_id,
                FuncionarioEmpresa.empresa_id == empresa_id
            )
            .first()
        )

    @staticmethod
    def adicionar(obj):
        db.session.add(obj)

    @staticmethod
    def salvar():
        db.session.commit()

    @staticmethod
    def rollback():
        db.session.rollback()

    @staticmethod
    def flush():
        db.session.flush()
