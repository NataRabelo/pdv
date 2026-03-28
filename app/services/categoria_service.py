from app.repositorys.categoria_repository import CategoriaRepository
from app.security.jwt import get_tenant_id
from flask_jwt_extended import get_jwt_identity
from app.models.db import CategoriaProduto

class CategoriaService():

    @staticmethod
    def cadastrar(data: dict):
        nome        = data.get('nome')
        descricao   = data.get('descricao')
        tenant_id   = get_tenant_id()

        if not nome:
            raise ValueError('Categoria precisa de um nome')
        v_nome = CategoriaRepository.get_by_name(nome)
        if v_nome:
            raise ValueError('Categoria já cadastrada com o mesmo nome')
        
        categoria = CategoriaProduto(
            nome        = nome ,
            descricao   = descricao,
            tenant_id   = tenant_id
        )

        categoria = CategoriaRepository.create(categoria)
        
        return categoria 
    
    @staticmethod
    def atualizar(data: dict, id: int):
        categoria = CategoriaRepository.get_by_id(id)

        categoria.nome      = data.get("edit-nome", categoria.nome)
        categoria.descricao = data.get("edit-descricao", categoria.descricao)

        categoria = CategoriaRepository.update(categoria)

        return categoria
    
    @staticmethod
    def deletar(id: int):
        categoria = CategoriaRepository.get_by_id(id)

        if not categoria:
            raise ValueError("Categoria não encontrada")
        #todo: criar regra para somente excluir caterogias que não estão sendo usadas 
        return CategoriaRepository.delete(categoria)

    @staticmethod
    def listar():
        categorias = CategoriaRepository.list()

        return categorias