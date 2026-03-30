from datetime import datetime

from app.models.db import CategoriaProduto
from app.repositorys.categoria_repository import CategoriaRepository


class CategoriaService:

    @staticmethod
    def listar(tenant_id):
        return CategoriaRepository.listar_por_tenant(tenant_id)

    @staticmethod
    def criar(data, tenant_id):
        categoria = CategoriaProduto(
            nome=data.get("nome"),
            descricao=data.get("descricao"),
            ativo=True,
            criado_em=datetime.utcnow(),
            atualizado_em=datetime.utcnow(),
            tenant_id=tenant_id
        )

        return CategoriaRepository.criar(categoria)

    @staticmethod
    def atualizar(categoria_id, data, tenant_id):
        categoria = CategoriaRepository.buscar_por_id(categoria_id, tenant_id)

        if not categoria:
            raise Exception("Categoria não encontrada")

        categoria.nome = data.get("nome")
        categoria.descricao = data.get("descricao")
        categoria.atualizado_em = datetime.utcnow()

        CategoriaRepository.atualizar()
        return categoria

    @staticmethod
    def deletar(categoria_id, tenant_id):
        categoria = CategoriaRepository.buscar_por_id(categoria_id, tenant_id)

        if not categoria:
            raise Exception("Categoria não encontrada")

        CategoriaRepository.deletar(categoria)