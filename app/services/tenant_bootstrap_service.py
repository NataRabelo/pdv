from app.extensions import db
from app.models.db import Permission, Role, RolePermission
from app.security.permissions import DEFAULT_PERMISSION_DEFINITIONS, DEFAULT_ROLE_DEFINITIONS


class TenantBootstrapService:

    @staticmethod
    def garantir_permissoes_e_roles(tenant_id):
        permissions_by_code = {}

        for definicao in DEFAULT_PERMISSION_DEFINITIONS:
            permission = Permission.query.filter_by(tenant_id=tenant_id, codigo=definicao["codigo"]).first()
            if not permission:
                permission = Permission(
                    tenant_id=tenant_id,
                    nome=definicao["nome"],
                    codigo=definicao["codigo"],
                    descricao=definicao.get("descricao"),
                    ativo=True
                )
                db.session.add(permission)
                db.session.flush()

            permissions_by_code[permission.codigo] = permission

        roles_por_codigo = {}

        for definicao in DEFAULT_ROLE_DEFINITIONS:
            role = Role.query.filter_by(tenant_id=tenant_id, codigo=definicao["codigo"]).first()
            if not role:
                role = Role(
                    tenant_id=tenant_id,
                    nome=definicao["nome"],
                    codigo=definicao["codigo"],
                    descricao=definicao.get("descricao"),
                    ativo=True
                )
                db.session.add(role)
                db.session.flush()

            roles_por_codigo[role.codigo] = role

            for permission_code in definicao["permissoes"]:
                permission = permissions_by_code[permission_code]
                vinculo = RolePermission.query.filter_by(
                    tenant_id=tenant_id,
                    role_id=role.id,
                    permission_id=permission.id
                ).first()

                if not vinculo:
                    db.session.add(RolePermission(
                        tenant_id=tenant_id,
                        role_id=role.id,
                        permission_id=permission.id
                    ))

        db.session.flush()
        return roles_por_codigo
