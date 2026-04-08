from app.models.db import CategoriaProduto
from app.repositorys.categoria_repository import CategoriaRepository
from app.services.acesso_empresa_service import AcessoEmpresaService
from app.services.time_service import TimeService


class CategoriaService:

    @staticmethod
    def listar(tenant_id, escopo):
        empresa_ids = AcessoEmpresaService.filtrar_empresa_ids(escopo)
        return CategoriaRepository.listar_por_tenant(tenant_id, empresa_ids)

    @staticmethod
    def criar(data, tenant_id):
        categoria = CategoriaProduto(
            nome=(data.get("nome") or "").strip(),
            descricao=(data.get("descricao") or "").strip() or None,
            ativo=True,
            criado_em=TimeService.now_utc_naive(),
            atualizado_em=TimeService.now_utc_naive(),
            tenant_id=tenant_id
        )
        return CategoriaRepository.criar(categoria)

    @staticmethod
    def atualizar(categoria_id, data, tenant_id):
        categoria = CategoriaRepository.buscar_por_id(categoria_id, tenant_id)
        if not categoria:
            raise ValueError("Categoria nao encontrada.")

        categoria.nome = (data.get("nome") or "").strip()
        categoria.descricao = (data.get("descricao") or "").strip() or None
        categoria.atualizado_em = TimeService.now_utc_naive()

        CategoriaRepository.atualizar()
        return categoria

    @staticmethod
    def deletar(categoria_id, tenant_id):
        categoria = CategoriaRepository.buscar_por_id(categoria_id, tenant_id)
        if not categoria:
            raise ValueError("Categoria nao encontrada.")

        CategoriaRepository.deletar(categoria)
