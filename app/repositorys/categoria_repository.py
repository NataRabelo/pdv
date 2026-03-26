from app.models.db import CategoriaProduto
from app.extensions import db

class CategoriaRepository():

    @staticmethod
    def create(categoria: CategoriaProduto):
        db.session.add(categoria)
        db.session.commit()

        return categoria
    
    @staticmethod
    def update(categoria: CategoriaProduto):
        db.session.commit(categoria)
        
        return categoria
    
    @staticmethod
    def delete(categoria: CategoriaProduto):
        db.session.delete(categoria)
        db.session.commit()

    @staticmethod
    def list():
        return CategoriaProduto.query.all()

    @staticmethod
    def get_by_id(id: int):
        return CategoriaProduto.query.filter_by(id = id).first()
    
    @staticmethod
    def get_by_name(nome: str):
        return CategoriaProduto.query.filter_by(nome = nome).first()