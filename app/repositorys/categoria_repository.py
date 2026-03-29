from app.models.db import CategoriaProduto
from app.extensions import db


class CategoriaRepository:

    @staticmethod
    def create(categoria: CategoriaProduto):
        db.session.add(categoria)
        db.session.commit()
        return categoria

    @staticmethod
    def update(categoria: CategoriaProduto):
        db.session.commit()
        return categoria

    @staticmethod
    def delete(categoria: CategoriaProduto):
        db.session.delete(categoria)
        db.session.commit()
        return True

    @staticmethod
    def list(tenant_id: int):
        return (
            db.session.query(CategoriaProduto)
            .filter(CategoriaProduto.tenant_id == tenant_id)
            .all()
        )

    @staticmethod
    def get_by_id(id: int, tenant_id: int):
        return (
            db.session.query(CategoriaProduto)
            .filter(
                CategoriaProduto.id == id,
                CategoriaProduto.tenant_id == tenant_id
            )
            .first()
        )

    @staticmethod
    def get_by_name(nome: str, tenant_id: int):
        return (
            db.session.query(CategoriaProduto)
            .filter(
                CategoriaProduto.nome == nome,
                CategoriaProduto.tenant_id == tenant_id
            )
            .first()
        )