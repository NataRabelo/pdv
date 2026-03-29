from app.repositorys.categoria_repository import CategoriaRepository
from app.security.jwt import get_tenant_id
from app.models.db import CategoriaProduto


class CategoriaService:

    @staticmethod
    def cadastrar(data: dict):
        nome = data.get('nome')
        descricao = data.get('descricao')
        tenant_id = get_tenant_id()

        if not nome:
            raise ValueError('Categoria precisa de um nome')

        # 🔒 valida por tenant
        existente = CategoriaRepository.get_by_name(nome, tenant_id)
        if existente:
            raise ValueError('Categoria já cadastrada com esse nome')

        categoria = CategoriaProduto(
            nome=nome,
            descricao=descricao,
            tenant_id=tenant_id
        )

        return CategoriaRepository.create(categoria)

    @staticmethod
    def atualizar(data: dict, id: int):
        tenant_id = get_tenant_id()

        categoria = CategoriaRepository.get_by_id(id, tenant_id)
        if not categoria:
            raise ValueError("Categoria não encontrada")

        nome = data.get("nome")
        descricao = data.get("descricao")

        # valida nome
        if nome:
            existente = CategoriaRepository.get_by_name(nome, tenant_id)
            if existente and existente.id != id:
                raise ValueError("Já existe outra categoria com esse nome")

            categoria.nome = nome

        if descricao is not None:
            categoria.descricao = descricao

        return CategoriaRepository.update(categoria)

    @staticmethod
    def deletar(id: int):
        tenant_id = get_tenant_id()

        categoria = CategoriaRepository.get_by_id(id, tenant_id)

        if not categoria:
            raise ValueError("Categoria não encontrada")

        # 🔒 regra futura
        # verificar se está sendo usada antes de deletar

        return CategoriaRepository.delete(categoria)

    @staticmethod
    def listar():
        tenant_id = get_tenant_id()

        return CategoriaRepository.list(tenant_id)