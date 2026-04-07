from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.db import Empresa, MovimentoEstoque, Produto, ProdutoEmpresa


class EstoqueRepository:

    @staticmethod
    def listar_saldos(tenant_id, empresa_ids=None, empresa_id=None):
        query = (
            ProdutoEmpresa.query
            .options(
                joinedload(ProdutoEmpresa.produto).joinedload(Produto.categoria),
                joinedload(ProdutoEmpresa.empresa)
            )
            .filter(ProdutoEmpresa.tenant_id == tenant_id)
            .order_by(ProdutoEmpresa.estoque_atual.asc(), ProdutoEmpresa.id.desc())
        )

        if empresa_ids is not None:
            query = query.filter(ProdutoEmpresa.empresa_id.in_(empresa_ids))

        if empresa_id is not None:
            query = query.filter(ProdutoEmpresa.empresa_id == empresa_id)

        return query.all()

    @staticmethod
    def listar_movimentos(tenant_id, empresa_ids=None, empresa_id=None, limite=50):
        query = (
            MovimentoEstoque.query
            .options(
                joinedload(MovimentoEstoque.empresa),
                joinedload(MovimentoEstoque.produto),
                joinedload(MovimentoEstoque.funcionario)
            )
            .filter(MovimentoEstoque.tenant_id == tenant_id)
            .order_by(MovimentoEstoque.data_movimento.desc(), MovimentoEstoque.id.desc())
        )

        if empresa_ids is not None:
            query = query.filter(MovimentoEstoque.empresa_id.in_(empresa_ids))

        if empresa_id is not None:
            query = query.filter(MovimentoEstoque.empresa_id == empresa_id)

        return query.limit(max(limite, 1)).all()

    @staticmethod
    def listar_empresas(tenant_id, empresa_ids=None):
        query = (
            Empresa.query
            .filter(
                Empresa.tenant_id == tenant_id,
                Empresa.ativo.is_(True)
            )
            .order_by(Empresa.nome_fantasia.asc())
        )

        if empresa_ids is not None:
            query = query.filter(Empresa.id.in_(empresa_ids))

        return query.all()

    @staticmethod
    def listar_produtos_empresa_disponiveis(tenant_id, empresa_ids=None, empresa_id=None):
        query = (
            ProdutoEmpresa.query
            .options(
                joinedload(ProdutoEmpresa.produto),
                joinedload(ProdutoEmpresa.empresa)
            )
            .join(Produto, Produto.id == ProdutoEmpresa.produto_id)
            .filter(
                ProdutoEmpresa.tenant_id == tenant_id,
                ProdutoEmpresa.ativo.is_(True),
                Produto.ativo.is_(True)
            )
            .order_by(ProdutoEmpresa.empresa_id.asc(), Produto.nome.asc())
        )

        if empresa_ids is not None:
            query = query.filter(ProdutoEmpresa.empresa_id.in_(empresa_ids))

        if empresa_id is not None:
            query = query.filter(ProdutoEmpresa.empresa_id == empresa_id)

        return query.all()

    @staticmethod
    def buscar_produto_empresa_por_id(produto_empresa_id, tenant_id, empresa_ids=None):
        query = (
            ProdutoEmpresa.query
            .options(
                joinedload(ProdutoEmpresa.produto),
                joinedload(ProdutoEmpresa.empresa)
            )
            .filter(
                ProdutoEmpresa.id == produto_empresa_id,
                ProdutoEmpresa.tenant_id == tenant_id
            )
        )

        if empresa_ids is not None:
            query = query.filter(ProdutoEmpresa.empresa_id.in_(empresa_ids))

        return query.first()

    @staticmethod
    def buscar_produto_empresa(produto_id, empresa_id, tenant_id):
        return (
            ProdutoEmpresa.query
            .options(
                joinedload(ProdutoEmpresa.produto),
                joinedload(ProdutoEmpresa.empresa)
            )
            .filter(
                ProdutoEmpresa.produto_id == produto_id,
                ProdutoEmpresa.empresa_id == empresa_id,
                ProdutoEmpresa.tenant_id == tenant_id
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
