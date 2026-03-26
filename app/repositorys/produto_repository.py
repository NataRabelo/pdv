from app.models.db import Produto
from app.extensions import db

class ProdutoRepository():

    @staticmethod
    def create(produto: Produto):
        db.session.add(produto)
        db.session.commit()

        return produto 
    
    @staticmethod
    def get_by_nome(nome: str):
        return Produto.query.filter_by(nome = nome).first()
    
    @staticmethod
    def get_by_ncm(ncm: str):
        return Produto.query.filter_by(ncm = ncm).first()