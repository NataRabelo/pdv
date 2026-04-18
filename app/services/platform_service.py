from app.models.db import Empresa, Funcionario, FuncionarioEmpresa, ModoVisualEmpresa, Tenant, TipoEmpresa
from app.repositorys.platform_repository import PlatformRepository
from app.security.password import hash_password
from app.security.permissions import ADMIN_ROLE_CODE
from app.services.tenant_bootstrap_service import TenantBootstrapService
from app.services.time_service import TimeService


class PlatformService:

    @staticmethod
    def listar_tenants():
        try:
            tenants = PlatformRepository.listar_tenants()
            alterou = False

            for tenant in tenants:
                alterou = PlatformService._sincronizar_admins_do_tenant(tenant.id) or alterou

            if alterou:
                PlatformRepository.salvar()
                tenants = PlatformRepository.listar_tenants()

            return [PlatformService._serializar_tenant(tenant) for tenant in tenants]
        except Exception:
            PlatformRepository.rollback()
            raise

    @staticmethod
    def criar_tenant(data):
        try:
            tenant_nome = (data.get("tenant_nome") or "").strip()
            empresa = data.get("empresa") or {}
            admin = data.get("admin") or {}

            if not tenant_nome:
                raise ValueError("Nome do tenant e obrigatorio.")

            if PlatformRepository.buscar_tenant_por_nome(tenant_nome):
                raise ValueError("Ja existe um tenant com esse nome.")

            tenant = Tenant(nome=tenant_nome)
            PlatformRepository.adicionar(tenant)
            PlatformRepository.flush()

            roles_por_codigo = TenantBootstrapService.garantir_permissoes_e_roles(tenant.id)
            TenantBootstrapService.garantir_cadastros_operacionais(tenant.id)
            empresa_obj = PlatformService._criar_empresa_obj(tenant.id, empresa)
            PlatformRepository.adicionar(empresa_obj)
            PlatformRepository.flush()

            admin_obj = PlatformService._criar_admin_obj(
                tenant.id,
                admin,
                empresa_obj.id,
                roles_por_codigo[ADMIN_ROLE_CODE].id
            )
            PlatformRepository.adicionar(admin_obj)
            PlatformRepository.flush()

            PlatformService._sincronizar_admins_do_tenant(tenant.id)
            PlatformRepository.salvar()

            tenant = PlatformRepository.buscar_tenant_por_id(tenant.id)
            return PlatformService._serializar_tenant(tenant)
        except Exception:
            PlatformRepository.rollback()
            raise

    @staticmethod
    def criar_empresa(tenant_id, data):
        tenant = PlatformRepository.buscar_tenant_por_id(tenant_id)
        if not tenant:
            raise ValueError("Tenant nao encontrado.")

        try:
            empresa = PlatformService._criar_empresa_obj(tenant.id, data)
            PlatformRepository.adicionar(empresa)
            PlatformRepository.flush()
            PlatformService._sincronizar_admins_do_tenant(tenant.id)
            PlatformRepository.salvar()
            return PlatformService._serializar_empresa(empresa)
        except Exception:
            PlatformRepository.rollback()
            raise

    @staticmethod
    def atualizar_visual_empresa(tenant_id, empresa_id, data):
        tenant = PlatformRepository.buscar_tenant_por_id(tenant_id)
        if not tenant:
            raise ValueError("Tenant nao encontrado.")

        empresa = PlatformRepository.buscar_empresa_por_id(empresa_id, tenant.id)
        if not empresa:
            raise ValueError("Empresa nao encontrada para esse tenant.")

        try:
            empresa.visual_modo = PlatformService._to_visual_mode(data.get("visual_modo"))
            PlatformRepository.adicionar(empresa)
            PlatformRepository.salvar()
            return PlatformService._serializar_empresa(empresa)
        except Exception:
            PlatformRepository.rollback()
            raise

    @staticmethod
    def criar_admin(tenant_id, data):
        tenant = PlatformRepository.buscar_tenant_por_id(tenant_id)
        if not tenant:
            raise ValueError("Tenant nao encontrado.")

        empresa_id = PlatformService._to_int(data.get("empresa_id"), "Empresa")
        empresa = PlatformRepository.buscar_empresa_por_id(empresa_id, tenant.id)
        if not empresa:
            raise ValueError("Empresa nao encontrada para esse tenant.")

        role_admin = PlatformRepository.buscar_role_por_codigo(ADMIN_ROLE_CODE, tenant.id)
        if not role_admin:
            roles = TenantBootstrapService.garantir_permissoes_e_roles(tenant.id)
            role_admin = roles[ADMIN_ROLE_CODE]

        try:
            admin_obj = PlatformService._criar_admin_obj(
                tenant.id,
                data,
                empresa.id,
                role_admin.id
            )
            PlatformRepository.adicionar(admin_obj)
            PlatformRepository.flush()

            PlatformService._sincronizar_admins_do_tenant(tenant.id)
            PlatformRepository.salvar()

            return {
                "id": admin_obj.id,
                "nome": admin_obj.nome,
                "usuario": admin_obj.usuario,
                "cpf": admin_obj.cpf,
                "ativo": admin_obj.ativo,
                "empresa_nome": empresa.nome_fantasia,
            }
        except Exception:
            PlatformRepository.rollback()
            raise

    @staticmethod
    def _criar_empresa_obj(tenant_id, data):
        cnpj = PlatformService._normalizar_cnpj(data.get("cnpj"))
        razao_social = (data.get("razao_social") or "").strip()
        nome_fantasia = (data.get("nome_fantasia") or "").strip()
        tipo_empresa = PlatformService._to_tipo_empresa(data.get("tipo_empresa"))

        if not cnpj:
            raise ValueError("CNPJ da empresa e obrigatorio.")
        if not razao_social:
            raise ValueError("Razao social e obrigatoria.")
        if not nome_fantasia:
            raise ValueError("Nome fantasia e obrigatorio.")

        if PlatformRepository.buscar_empresa_por_cnpj(cnpj, tenant_id):
            raise ValueError("Ja existe empresa com esse CNPJ neste tenant.")

        return Empresa(
            tenant_id=tenant_id,
            cnpj=cnpj,
            razao_social=razao_social,
            nome_fantasia=nome_fantasia,
            tipo_empresa=tipo_empresa,
            visual_modo=PlatformService._to_visual_mode(data.get("visual_modo"), required=False),
            ativo=True,
        )

    @staticmethod
    def _criar_admin_obj(tenant_id, data, empresa_id, role_id):
        nome = (data.get("nome") or "").strip()
        usuario = (data.get("usuario") or "").strip()
        senha = (data.get("senha") or "").strip()
        cpf = PlatformService._normalizar_cpf(data.get("cpf"))

        if not nome:
            raise ValueError("Nome do admin e obrigatorio.")
        if not usuario:
            raise ValueError("Usuario do admin e obrigatorio.")
        if not senha:
            raise ValueError("Senha do admin e obrigatoria.")
        if not cpf:
            raise ValueError("CPF do admin e obrigatorio.")
        if not empresa_id:
            raise ValueError("Empresa do admin e obrigatoria.")

        if PlatformRepository.buscar_funcionario_por_usuario(usuario, tenant_id):
            raise ValueError("Ja existe funcionario com esse usuario neste tenant.")

        if PlatformRepository.buscar_funcionario_por_cpf(cpf, tenant_id):
            raise ValueError("Ja existe funcionario com esse CPF neste tenant.")

        return Funcionario(
            tenant_id=tenant_id,
            role_id=role_id,
            nome=nome,
            cpf=cpf,
            usuario=usuario,
            senha_hash=hash_password(senha),
            ativo=True,
        )

    @staticmethod
    def _serializar_tenant(tenant):
        empresas = sorted(tenant.empresas, key=lambda item: item.nome_fantasia.lower())
        admins = sorted(
            [
                funcionario for funcionario in tenant.funcionarios
                if funcionario.role and funcionario.role.codigo == ADMIN_ROLE_CODE
            ],
            key=lambda item: item.nome.lower()
        )

        return {
            "id": tenant.id,
            "nome": tenant.nome,
            "criado_em": TimeService.serialize_utc_iso(tenant.criado_em),
            "quantidade_empresas": len(empresas),
            "quantidade_admins": len(admins),
            "empresas": [PlatformService._serializar_empresa(empresa) for empresa in empresas],
            "admins": [
                {
                    "id": admin.id,
                    "nome": admin.nome,
                    "usuario": admin.usuario,
                    "cpf": admin.cpf,
                    "ativo": admin.ativo,
                }
                for admin in admins
            ],
        }

    @staticmethod
    def _serializar_empresa(empresa):
        return {
            "id": empresa.id,
            "nome_fantasia": empresa.nome_fantasia,
            "razao_social": empresa.razao_social,
            "cnpj": empresa.cnpj,
            "tipo_empresa": empresa.tipo_empresa.value,
            "visual_modo": (empresa.visual_modo or ModoVisualEmpresa.MODERNO).value,
            "ativo": empresa.ativo,
        }

    @staticmethod
    def _sincronizar_admins_do_tenant(tenant_id):
        alterou = False
        empresas = PlatformRepository.listar_empresas_por_tenant(tenant_id)
        admins = PlatformRepository.listar_admins_por_tenant(tenant_id)

        for admin in admins:
            if not admin.role or admin.role.codigo != ADMIN_ROLE_CODE:
                continue

            for empresa in empresas:
                alterou = PlatformService._garantir_vinculo_funcionario_empresa(
                    tenant_id=tenant_id,
                    funcionario_id=admin.id,
                    empresa_id=empresa.id
                ) or alterou

        return alterou

    @staticmethod
    def _garantir_vinculo_funcionario_empresa(tenant_id, funcionario_id, empresa_id):
        vinculo = PlatformRepository.buscar_vinculo_funcionario_empresa(
            tenant_id=tenant_id,
            funcionario_id=funcionario_id,
            empresa_id=empresa_id
        )

        if vinculo:
            if not vinculo.ativo:
                vinculo.ativo = True
                PlatformRepository.adicionar(vinculo)
                return True
            return False

        vinculo = FuncionarioEmpresa(
            tenant_id=tenant_id,
            funcionario_id=funcionario_id,
            empresa_id=empresa_id,
            ativo=True
        )
        PlatformRepository.adicionar(vinculo)
        return True

    @staticmethod
    def _to_tipo_empresa(value):
        try:
            return TipoEmpresa[(value or "").strip().upper()]
        except KeyError:
            raise ValueError("Tipo de empresa invalido.")

    @staticmethod
    def _to_visual_mode(value, required=True):
        raw_value = (value or "").strip().upper()
        if not raw_value:
            if required:
                raise ValueError("Modo visual e obrigatorio.")
            return ModoVisualEmpresa.MODERNO

        try:
            return ModoVisualEmpresa[raw_value]
        except KeyError:
            raise ValueError("Modo visual invalido.")

    @staticmethod
    def _to_int(value, field_name):
        if value in (None, ""):
            raise ValueError(f"{field_name} e obrigatoria.")

        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} invalida.")

    @staticmethod
    def _normalizar_cpf(value):
        return "".join(char for char in str(value or "") if char.isdigit())

    @staticmethod
    def _normalizar_cnpj(value):
        return "".join(char for char in str(value or "") if char.isdigit())
