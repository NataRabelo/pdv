from app.extensions import db
from app.models.db import Permission, RolePermission


class PermissionRepository:

    @staticmethod
    def listar(tenant_id):
        return (
            Permission.query
            .filter(Permission.tenant_id == tenant_id)
            .order_by(Permission.nome.asc())
            .all()
        )

    @staticmethod
    def buscar_por_id(permission_id, tenant_id):
        return (
            Permission.query
            .filter(
                Permission.id == permission_id,
                Permission.tenant_id == tenant_id
            )
            .first()
        )

    @staticmethod
    def buscar_por_codigo(codigo, tenant_id, ignorar_permission_id=None):
        query = Permission.query.filter(
            Permission.codigo == codigo,
            Permission.tenant_id == tenant_id
        )

        if ignorar_permission_id is not None:
            query = query.filter(Permission.id != ignorar_permission_id)

        return query.first()

    @staticmethod
    def contar_roles_por_permission(permission_id, tenant_id):
        return (
            RolePermission.query
            .filter(
                RolePermission.permission_id == permission_id,
                RolePermission.tenant_id == tenant_id
            )
            .count()
        )

    @staticmethod
    def adicionar(obj):
        db.session.add(obj)

    @staticmethod
    def deletar(obj):
        db.session.delete(obj)

    @staticmethod
    def salvar():
        db.session.commit()

    @staticmethod
    def rollback():
        db.session.rollback()
