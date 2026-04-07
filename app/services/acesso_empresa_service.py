from app.repositorys.funcionario_repository import FuncionarioRepository
from app.security.permissions import ADMIN_ROLE_CODE, VISUALIZAR_TODAS_EMPRESAS


class AcessoEmpresaService:

    @staticmethod
    def obter_escopo(funcionario_id, tenant_id):
        funcionario = FuncionarioRepository.busca_funcionario_por_id(funcionario_id, tenant_id)
        if not funcionario:
            raise PermissionError("Funcionario autenticado nao encontrado.")

        empresa_ids = FuncionarioRepository.listar_ids_empresas_por_funcionario(funcionario_id, tenant_id)
        permissions = {
            link.permission.codigo
            for link in (funcionario.role.permissions_links if funcionario.role else [])
            if link.permission and link.permission.ativo
        }
        role_code = funcionario.role.codigo if funcionario.role else None

        return {
            "funcionario_id": funcionario.id,
            "tenant_id": tenant_id,
            "empresa_ids": empresa_ids,
            "role_code": role_code,
            "role_name": funcionario.role.nome if funcionario.role else None,
            "is_admin": role_code == ADMIN_ROLE_CODE,
            "permission_codes": permissions,
        }

    @staticmethod
    def filtrar_empresa_ids(escopo):
        if AcessoEmpresaService.possui_permissao(escopo, VISUALIZAR_TODAS_EMPRESAS):
            return None
        return escopo["empresa_ids"]

    @staticmethod
    def validar_empresa(empresa_id, escopo):
        if AcessoEmpresaService.possui_permissao(escopo, VISUALIZAR_TODAS_EMPRESAS):
            return

        if empresa_id not in escopo["empresa_ids"]:
            raise PermissionError("Voce nao tem permissao para acessar dados desta empresa.")

    @staticmethod
    def possui_permissao(escopo, permission_code):
        return permission_code in escopo["permission_codes"]

    @staticmethod
    def eh_admin(escopo):
        return bool(escopo.get("is_admin"))
