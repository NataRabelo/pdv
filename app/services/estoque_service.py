from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.models.db import MotivoMovimentoEstoque, MovimentoEstoque, TipoMovimentoEstoque
from app.repositorys.estoque_repository import EstoqueRepository
from app.services.acesso_empresa_service import AcessoEmpresaService


class EstoqueService:
    MOTIVOS_MANUAIS = {
        TipoMovimentoEstoque.ENTRADA: (
            MotivoMovimentoEstoque.COMPRA,
            MotivoMovimentoEstoque.AJUSTE,
            MotivoMovimentoEstoque.DEVOLUCAO,
            MotivoMovimentoEstoque.TRANSFERENCIA,
        ),
        TipoMovimentoEstoque.SAIDA: (
            MotivoMovimentoEstoque.AJUSTE,
            MotivoMovimentoEstoque.PERDA,
            MotivoMovimentoEstoque.TRANSFERENCIA,
        ),
    }

    @staticmethod
    def listar_saldos(tenant_id, escopo, empresa_id=None):
        empresa_ids = AcessoEmpresaService.filtrar_empresa_ids(escopo)

        if empresa_id:
            AcessoEmpresaService.validar_empresa(empresa_id, escopo)

        return EstoqueRepository.listar_saldos(
            tenant_id,
            empresa_ids=empresa_ids,
            empresa_id=empresa_id,
        )

    @staticmethod
    def listar_movimentos(tenant_id, escopo, empresa_id=None, limite=50):
        empresa_ids = AcessoEmpresaService.filtrar_empresa_ids(escopo)

        if empresa_id:
            AcessoEmpresaService.validar_empresa(empresa_id, escopo)

        return EstoqueRepository.listar_movimentos(
            tenant_id,
            empresa_ids=empresa_ids,
            empresa_id=empresa_id,
            limite=limite,
        )

    @staticmethod
    def listar_auxiliares(tenant_id, escopo):
        empresa_ids = AcessoEmpresaService.filtrar_empresa_ids(escopo)
        empresas = EstoqueRepository.listar_empresas(tenant_id, empresa_ids=empresa_ids)
        produtos_empresa = EstoqueRepository.listar_produtos_empresa_disponiveis(tenant_id, empresa_ids=empresa_ids)

        return {
            "empresas": [
                {"id": empresa.id, "nome": empresa.nome_fantasia}
                for empresa in empresas
            ],
            "motivos": {
                "ENTRADA": [motivo.value for motivo in EstoqueService.MOTIVOS_MANUAIS[TipoMovimentoEstoque.ENTRADA]],
                "SAIDA": [motivo.value for motivo in EstoqueService.MOTIVOS_MANUAIS[TipoMovimentoEstoque.SAIDA]],
            },
            "produtos": [
                {
                    "id": item.id,
                    "produto_id": item.produto.id,
                    "empresa_id": item.empresa.id,
                    "empresa_nome": item.empresa.nome_fantasia,
                    "nome": item.produto.nome,
                    "categoria_nome": item.produto.categoria.nome if item.produto.categoria else "",
                    "codigo_barras": item.produto.codigo_barras,
                    "estoque_atual": int(item.estoque_atual),
                    "estoque_minimo": int(item.estoque_minimo),
                    "valor_compra": str(item.valor_compra),
                    "valor_venda": str(item.valor_venda),
                }
                for item in produtos_empresa
            ],
        }

    @staticmethod
    def registrar_movimentacao_manual(data, tenant_id, escopo, funcionario_id):
        empresa_ids = AcessoEmpresaService.filtrar_empresa_ids(escopo)
        produto_empresa_id = EstoqueService._to_int(data.get("produto_empresa_id"), "Produto")
        tipo = EstoqueService._to_tipo_movimento(data.get("tipo_movimento"))
        motivo = EstoqueService._to_motivo(data.get("motivo"))
        quantidade = EstoqueService._to_positive_int(data.get("quantidade"), "quantidade")
        valor_unitario = EstoqueService._to_optional_decimal(data.get("valor_unitario"), "valor unitario", casas=2)
        observacao = (data.get("observacao") or "").strip() or None

        produto_empresa = EstoqueRepository.buscar_produto_empresa_por_id(
            produto_empresa_id,
            tenant_id,
            empresa_ids=empresa_ids,
        )
        if not produto_empresa:
            raise ValueError("Produto nao encontrado para o estoque informado.")

        AcessoEmpresaService.validar_empresa(produto_empresa.empresa_id, escopo)
        EstoqueService._validar_motivo_manual(tipo, motivo)

        try:
            movimento = EstoqueService._registrar_movimento(
                tenant_id=tenant_id,
                produto_empresa=produto_empresa,
                tipo_movimento=tipo,
                motivo=motivo,
                quantidade=quantidade,
                funcionario_id=funcionario_id,
                valor_unitario=valor_unitario,
                observacao=observacao,
            )
            EstoqueRepository.salvar()
            return movimento
        except Exception:
            EstoqueRepository.rollback()
            raise

    @staticmethod
    def registrar_saida_por_venda(venda_id, empresa_id, itens, tenant_id, funcionario_id=None, escopo=None):
        if escopo is not None:
            AcessoEmpresaService.validar_empresa(empresa_id, escopo)

        movimentos = []

        try:
            for item in itens:
                produto_id = EstoqueService._to_int(item.get("produto_id"), "Produto")
                quantidade = EstoqueService._to_positive_int(item.get("quantidade"), "quantidade")
                valor_unitario = EstoqueService._to_optional_decimal(
                    item.get("valor_unitario"),
                    "valor unitario",
                    casas=2
                )

                produto_empresa = EstoqueRepository.buscar_produto_empresa(produto_id, empresa_id, tenant_id)
                if not produto_empresa:
                    raise ValueError("Produto da venda nao encontrado no estoque da empresa.")

                movimento = EstoqueService._registrar_movimento(
                    tenant_id=tenant_id,
                    produto_empresa=produto_empresa,
                    tipo_movimento=TipoMovimentoEstoque.SAIDA,
                    motivo=MotivoMovimentoEstoque.VENDA,
                    quantidade=quantidade,
                    funcionario_id=funcionario_id,
                    venda_id=venda_id,
                    valor_unitario=valor_unitario,
                    observacao="Baixa automatica por venda do PDV.",
                )
                movimentos.append(movimento)

            EstoqueRepository.salvar()
            return movimentos
        except Exception:
            EstoqueRepository.rollback()
            raise

    @staticmethod
    def _registrar_movimento(
        tenant_id,
        produto_empresa,
        tipo_movimento,
        motivo,
        quantidade,
        funcionario_id=None,
        venda_id=None,
        valor_unitario=None,
        observacao=None,
        data_movimento=None,
    ):
        if quantidade <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")

        estoque_atual = int(produto_empresa.estoque_atual)

        if tipo_movimento == TipoMovimentoEstoque.SAIDA and estoque_atual < quantidade:
            raise ValueError("Estoque insuficiente para realizar a saida.")

        if tipo_movimento == TipoMovimentoEstoque.ENTRADA:
            produto_empresa.estoque_atual = estoque_atual + quantidade
        else:
            produto_empresa.estoque_atual = estoque_atual - quantidade

        if valor_unitario is not None and motivo == MotivoMovimentoEstoque.COMPRA:
            produto_empresa.valor_compra = valor_unitario

        valor_total = None
        if valor_unitario is not None:
            valor_total = (valor_unitario * quantidade).quantize(Decimal("0.01"))

        movimento = MovimentoEstoque(
            tenant_id=tenant_id,
            empresa_id=produto_empresa.empresa_id,
            produto_id=produto_empresa.produto_id,
            funcionario_id=funcionario_id,
            venda_id=venda_id,
            tipo_movimento=tipo_movimento,
            motivo=motivo,
            quantidade=quantidade,
            valor_unitario=valor_unitario,
            valor_total=valor_total,
            observacao=observacao,
            data_movimento=data_movimento or datetime.utcnow(),
        )
        EstoqueRepository.adicionar(movimento)
        EstoqueRepository.adicionar(produto_empresa)

        return movimento

    @staticmethod
    def _validar_motivo_manual(tipo, motivo):
        if motivo == MotivoMovimentoEstoque.VENDA:
            raise ValueError("Use o fluxo do PDV para movimentos de venda.")

        if motivo not in EstoqueService.MOTIVOS_MANUAIS[tipo]:
            raise ValueError("Motivo invalido para o tipo de movimentacao informado.")

    @staticmethod
    def _to_tipo_movimento(value):
        try:
            return TipoMovimentoEstoque[(value or "").strip().upper()]
        except KeyError:
            raise ValueError("Tipo de movimentacao invalido.")

    @staticmethod
    def _to_motivo(value):
        try:
            return MotivoMovimentoEstoque[(value or "").strip().upper()]
        except KeyError:
            raise ValueError("Motivo de movimentacao invalido.")

    @staticmethod
    def _to_decimal(value, field_name, casas=2, obrigatorio=False):
        if value in (None, ""):
            if obrigatorio:
                raise ValueError(f"Informe {field_name}.")
            value = 0

        try:
            valor = Decimal(str(value).replace(",", "."))
        except (InvalidOperation, ValueError):
            raise ValueError(f"Valor invalido para {field_name}.")

        if valor <= 0 and obrigatorio:
            raise ValueError(f"{field_name.capitalize()} deve ser maior que zero.")

        quant = "0." + ("0" * (casas - 1)) + "1" if casas > 0 else "1"
        return valor.quantize(Decimal(quant))

    @staticmethod
    def _to_optional_decimal(value, field_name, casas=2):
        if value in (None, ""):
            return None

        valor = EstoqueService._to_decimal(value, field_name, casas=casas, obrigatorio=False)
        if valor < 0:
            raise ValueError(f"{field_name.capitalize()} nao pode ser negativo.")
        return valor

    @staticmethod
    def _to_positive_int(value, field_name):
        if value in (None, ""):
            raise ValueError(f"Informe {field_name}.")

        try:
            valor = int(str(value).strip().replace(".", "").replace(",", ""))
        except (TypeError, ValueError):
            raise ValueError(f"Valor invalido para {field_name}.")

        if valor <= 0:
            raise ValueError(f"{field_name.capitalize()} deve ser maior que zero.")

        return valor

    @staticmethod
    def _to_int(value, field_name):
        if value in (None, ""):
            raise ValueError(f"{field_name} e obrigatorio.")

        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} invalido.")
