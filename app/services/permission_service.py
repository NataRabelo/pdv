from app.models.db import Permission
from app.repositorys.permission_repository import PermissionRepository
from app.security.permissions import build_permission_groups


class PermissionService:

    @staticmethod
    def listar(tenant_id):
        return PermissionRepository.listar(tenant_id)

    @staticmethod
    def listar_agrupadas(tenant_id):
        permissions = PermissionRepository.listar(tenant_id)
        return build_permission_groups(permissions)

    @staticmethod
    def criar(data, tenant_id):
        try:
            nome = (data.get("nome") or "").strip()
            codigo = (data.get("codigo") or "").strip()
            descricao = (data.get("descricao") or "").strip() or None
            ativo = PermissionService._to_bool(data.get("ativo", True))

            if not nome:
                raise ValueError("Nome da permission e obrigatorio.")
            if not codigo:
                raise ValueError("Codigo da permission e obrigatorio.")

            if PermissionRepository.buscar_por_codigo(codigo, tenant_id):
                raise ValueError("Ja existe uma permission com esse codigo.")

            permission = Permission(
                tenant_id=tenant_id,
                nome=nome,
                codigo=codigo,
                descricao=descricao,
                ativo=ativo
            )
            PermissionRepository.adicionar(permission)
            PermissionRepository.salvar()
            return permission
        except Exception:
            PermissionRepository.rollback()
            raise

    @staticmethod
    def atualizar(permission_id, data, tenant_id):
        try:
            permission = PermissionRepository.buscar_por_id(permission_id, tenant_id)
            if not permission:
                raise ValueError("Permission nao encontrada.")

            nome = (data.get("nome") or "").strip()
            codigo = (data.get("codigo") or "").strip()
            descricao = (data.get("descricao") or "").strip() or None
            ativo = PermissionService._to_bool(data.get("ativo", True))

            if not nome:
                raise ValueError("Nome da permission e obrigatorio.")
            if not codigo:
                raise ValueError("Codigo da permission e obrigatorio.")

            if PermissionRepository.buscar_por_codigo(codigo, tenant_id, ignorar_permission_id=permission.id):
                raise ValueError("Ja existe uma permission com esse codigo.")

            permission.nome = nome
            permission.codigo = codigo
            permission.descricao = descricao
            permission.ativo = ativo

            PermissionRepository.salvar()
            return permission
        except Exception:
            PermissionRepository.rollback()
            raise

    @staticmethod
    def deletar(permission_id, tenant_id):
        try:
            permission = PermissionRepository.buscar_por_id(permission_id, tenant_id)
            if not permission:
                raise ValueError("Permission nao encontrada.")

            if PermissionRepository.contar_roles_por_permission(permission.id, tenant_id) > 0:
                raise ValueError("Nao e possivel excluir uma permission vinculada a roles.")

            PermissionRepository.deletar(permission)
            PermissionRepository.salvar()
        except Exception:
            PermissionRepository.rollback()
            raise

    @staticmethod
    def _to_bool(value, default=False):
        if value is None:
            return default

        if isinstance(value, bool):
            return value

        return str(value).strip().lower() in ["1", "true", "on", "sim", "yes"]
