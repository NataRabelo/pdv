from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from app.models.db import ItemVenda, PagamentoVenda, StatusVenda, TipoDesconto, Venda
from app.repositorys.pdv_repository import PdvRepository
from app.services.acesso_empresa_service import AcessoEmpresaService
from app.services.estoque_service import EstoqueService
from app.services.financeiro_service import FinanceiroService
from app.services.tenant_bootstrap_service import TenantBootstrapService
from app.services.time_service import TimeService


class PdvService:

    @staticmethod
    def listar_auxiliares(tenant_id, escopo):
        PdvService._garantir_base_operacional(tenant_id)

        empresa_ids = AcessoEmpresaService.filtrar_empresa_ids(escopo)
        empresas = PdvRepository.listar_empresas(tenant_id, empresa_ids=empresa_ids)
        formas_pagamento = PdvRepository.listar_formas_pagamento(tenant_id)
        cupons = PdvRepository.listar_cupons_ativos(tenant_id, data_referencia=date.today())

        return {
            "empresas": [
                {"id": empresa.id, "nome": empresa.nome_fantasia}
                for empresa in empresas
            ],
            "formas_pagamento": [
                {"id": forma.id, "nome": forma.nome}
                for forma in formas_pagamento
            ],
            "cupons": [
                {
                    "id": cupom.id,
                    "nome": cupom.nome,
                    "codigo": cupom.codigo,
                    "data_validade": cupom.data_validade.isoformat(),
                    "tipo_desconto": cupom.tipo_desconto.value,
                    "valor_desconto": str(PdvService._to_decimal_value(cupom.valor_desconto)),
                }
                for cupom in cupons
            ],
        }

    @staticmethod
    def listar_produtos(tenant_id, escopo, empresa_id, busca=None):
        AcessoEmpresaService.validar_empresa(empresa_id, escopo)
        produtos = PdvRepository.listar_produtos_para_pdv(tenant_id, empresa_id)
        termo = (busca or "").strip().lower()

        if termo:
            produtos = [
                item for item in produtos
                if any(
                    termo in str(valor or "").lower()
                    for valor in (
                        item.produto.nome,
                        item.produto.descricao,
                        item.produto.codigo_barras,
                        item.produto.categoria.nome if item.produto.categoria else "",
                    )
                )
            ]

        return [PdvService.serializar_produto(item) for item in produtos]

    @staticmethod
    def buscar_produto_por_codigo_barras(tenant_id, escopo, empresa_id, codigo_barras):
        AcessoEmpresaService.validar_empresa(empresa_id, escopo)

        codigo_normalizado = "".join(char for char in str(codigo_barras or "").strip() if not char.isspace())
        if not codigo_normalizado:
            raise ValueError("Informe o codigo de barras para localizar o produto.")

        produto_empresa = PdvRepository.buscar_produto_empresa_por_codigo_barras(
            codigo_barras=codigo_normalizado,
            empresa_id=empresa_id,
            tenant_id=tenant_id,
        )
        if not produto_empresa:
            raise ValueError("Produto nao encontrado para o codigo de barras informado.")

        return PdvService.serializar_produto(produto_empresa)

    @staticmethod
    def listar_vendas(tenant_id, escopo, empresa_id=None, status=None, limite=30):
        empresa_ids = AcessoEmpresaService.filtrar_empresa_ids(escopo)

        if empresa_id:
            AcessoEmpresaService.validar_empresa(empresa_id, escopo)

        status_enum = PdvService._to_optional_status(status)
        vendas = PdvRepository.listar_vendas(
            tenant_id=tenant_id,
            empresa_ids=empresa_ids,
            empresa_id=empresa_id,
            status=status_enum,
            limite=limite,
        )
        return [PdvService.serializar_venda(item) for item in vendas]

    @staticmethod
    def criar_venda(data, tenant_id, escopo, funcionario_id):
        try:
            PdvService._garantir_base_operacional(tenant_id)

            empresa_id = PdvService._to_int(data.get("empresa_id"), "Empresa")
            desconto_manual = PdvService._to_optional_decimal(data.get("desconto_manual"), "desconto manual")
            observacao = (data.get("observacao") or "").strip() or None
            cupom_codigo = (data.get("cupom_codigo") or "").strip() or None
            itens_payload = data.get("itens") or []
            pagamentos_payload = data.get("pagamentos") or []

            if not itens_payload:
                raise ValueError("Adicione ao menos um item ao carrinho.")

            if not pagamentos_payload:
                raise ValueError("Informe ao menos uma forma de pagamento.")

            AcessoEmpresaService.validar_empresa(empresa_id, escopo)

            tipo_operacao = PdvRepository.buscar_tipo_operacao_por_codigo("VENDA_PADRAO", tenant_id)
            if not tipo_operacao:
                raise ValueError("Tipo de operacao padrao de venda nao encontrado.")

            itens_compilados = []
            subtotal = Decimal("0.00")

            for item_data in itens_payload:
                produto_id = PdvService._to_int(item_data.get("produto_id"), "Produto")
                quantidade = PdvService._to_positive_int(item_data.get("quantidade"), "quantidade")

                produto_empresa = PdvRepository.buscar_produto_empresa(produto_id, empresa_id, tenant_id)
                if not produto_empresa or not produto_empresa.ativo or not produto_empresa.produto.ativo:
                    raise ValueError("Um dos produtos informados nao esta disponivel para venda.")

                valor_unitario = PdvService._to_optional_decimal(item_data.get("valor_unitario"), "valor unitario")
                if valor_unitario is None:
                    valor_unitario = PdvService._to_decimal_value(produto_empresa.valor_venda)

                if valor_unitario < 0:
                    raise ValueError("Valor unitario invalido para um dos itens.")

                valor_total = (valor_unitario * quantidade).quantize(Decimal("0.01"))
                subtotal += valor_total

                itens_compilados.append({
                    "produto_id": produto_empresa.produto_id,
                    "quantidade": quantidade,
                    "valor_unitario": valor_unitario,
                    "valor_total": valor_total,
                })

            cupom = PdvService._validar_cupom(cupom_codigo, tenant_id)
            desconto_cupom = PdvService._calcular_desconto_cupom(cupom, subtotal)
            desconto_total = (desconto_manual + desconto_cupom).quantize(Decimal("0.01"))

            if desconto_total > subtotal:
                raise ValueError("O desconto total nao pode ser maior que o subtotal.")

            total = (subtotal - desconto_total).quantize(Decimal("0.01"))

            pagamentos_compilados = PdvService._validar_pagamentos(
                pagamentos_payload=pagamentos_payload,
                tenant_id=tenant_id,
                total_esperado=total,
            )

            venda = Venda(
                tenant_id=tenant_id,
                empresa_id=empresa_id,
                funcionario_id=funcionario_id,
                tipo_operacao_id=tipo_operacao.id,
                cupom_id=cupom.id if cupom else None,
                numero_unico=PdvService._gerar_numero_unico(empresa_id),
                status=StatusVenda.FINALIZADA,
                subtotal=subtotal,
                desconto=desconto_total,
                total=total,
                data_venda=TimeService.now_utc_naive(),
                observacao=observacao,
            )
            PdvRepository.adicionar(venda)
            PdvRepository.flush()

            for item in itens_compilados:
                PdvRepository.adicionar(
                    ItemVenda(
                        tenant_id=tenant_id,
                        venda_id=venda.id,
                        produto_id=item["produto_id"],
                        quantidade=item["quantidade"],
                        valor_unitario=item["valor_unitario"],
                        valor_total=item["valor_total"],
                    )
                )

            pagamentos_registrados = []
            for pagamento in pagamentos_compilados:
                pagamento_obj = PagamentoVenda(
                    tenant_id=tenant_id,
                    venda_id=venda.id,
                    forma_pagamento_id=pagamento["forma_pagamento"].id,
                    valor=pagamento["valor"],
                    comprovante=pagamento["comprovante"],
                )
                pagamento_obj.forma_pagamento = pagamento["forma_pagamento"]
                PdvRepository.adicionar(pagamento_obj)
                pagamentos_registrados.append(pagamento_obj)

            PdvRepository.flush()

            EstoqueService.registrar_saida_por_venda(
                venda_id=venda.id,
                empresa_id=empresa_id,
                itens=[
                    {
                        "produto_id": item["produto_id"],
                        "quantidade": item["quantidade"],
                        "valor_unitario": item["valor_unitario"],
                    }
                    for item in itens_compilados
                ],
                tenant_id=tenant_id,
                funcionario_id=funcionario_id,
                escopo=escopo,
                persistir=False,
            )
            FinanceiroService.registrar_entradas_da_venda(
                venda=venda,
                pagamentos=pagamentos_registrados,
                tenant_id=tenant_id,
                funcionario_id=funcionario_id,
                persistir=False,
            )

            PdvRepository.salvar()

            empresa_ids = AcessoEmpresaService.filtrar_empresa_ids(escopo)
            venda = PdvRepository.buscar_venda_por_id(venda.id, tenant_id, empresa_ids=empresa_ids)
            return PdvService.serializar_venda(venda)
        except Exception:
            PdvRepository.rollback()
            raise

    @staticmethod
    def cancelar_venda(venda_id, data, tenant_id, escopo, funcionario_id):
        try:
            empresa_ids = AcessoEmpresaService.filtrar_empresa_ids(escopo)
            venda = PdvRepository.buscar_venda_por_id(venda_id, tenant_id, empresa_ids=empresa_ids)
            if not venda:
                raise ValueError("Venda nao encontrada.")

            if venda.status != StatusVenda.FINALIZADA:
                raise ValueError("Somente vendas finalizadas podem ser canceladas.")

            motivo = (data.get("motivo") or "").strip() or "Cancelamento manual realizado pelo operador."
            venda.status = StatusVenda.CANCELADA
            venda.observacao = PdvService._mesclar_observacao(venda.observacao, motivo)

            EstoqueService.registrar_entrada_por_cancelamento_venda(
                venda_id=venda.id,
                empresa_id=venda.empresa_id,
                itens=[
                    {
                        "produto_id": item.produto_id,
                        "quantidade": item.quantidade,
                        "valor_unitario": item.valor_unitario,
                    }
                    for item in venda.itens
                ],
                tenant_id=tenant_id,
                funcionario_id=funcionario_id,
                escopo=escopo,
                persistir=False,
            )
            FinanceiroService.registrar_estorno_da_venda(
                venda=venda,
                tenant_id=tenant_id,
                funcionario_id=funcionario_id,
                persistir=False,
            )

            PdvRepository.salvar()

            venda = PdvRepository.buscar_venda_por_id(venda.id, tenant_id, empresa_ids=empresa_ids)
            return PdvService.serializar_venda(venda)
        except Exception:
            PdvRepository.rollback()
            raise

    @staticmethod
    def serializar_produto(item):
        return {
            "id": item.produto.id,
            "produto_empresa_id": item.id,
            "empresa_id": item.empresa_id,
            "empresa_nome": item.empresa.nome_fantasia if item.empresa else None,
            "categoria_nome": item.produto.categoria.nome if item.produto.categoria else None,
            "nome": item.produto.nome,
            "descricao": item.produto.descricao,
            "codigo_barras": item.produto.codigo_barras,
            "estoque_atual": int(item.estoque_atual),
            "estoque_minimo": int(item.estoque_minimo),
            "valor_venda": str(PdvService._to_decimal_value(item.valor_venda)),
            "valor_compra": str(PdvService._to_decimal_value(item.valor_compra)),
            "ativo": item.ativo,
        }

    @staticmethod
    def serializar_venda(venda):
        return {
            "id": venda.id,
            "empresa_id": venda.empresa_id,
            "empresa_nome": venda.empresa.nome_fantasia if venda.empresa else None,
            "funcionario_nome": venda.funcionario.nome if venda.funcionario else None,
            "numero_unico": venda.numero_unico,
            "status": venda.status.value,
            "subtotal": str(PdvService._to_decimal_value(venda.subtotal)),
            "desconto": str(PdvService._to_decimal_value(venda.desconto)),
            "total": str(PdvService._to_decimal_value(venda.total)),
            "data_venda": TimeService.serialize_utc_iso(venda.data_venda),
            "observacao": venda.observacao,
            "cupom_codigo": venda.cupom.codigo if venda.cupom else None,
            "itens_quantidade": sum(int(item.quantidade) for item in venda.itens),
            "itens": [
                {
                    "id": item.id,
                    "produto_id": item.produto_id,
                    "produto_nome": item.produto.nome if item.produto else None,
                    "quantidade": int(item.quantidade),
                    "valor_unitario": str(PdvService._to_decimal_value(item.valor_unitario)),
                    "valor_total": str(PdvService._to_decimal_value(item.valor_total)),
                }
                for item in venda.itens
            ],
            "pagamentos": [
                {
                    "id": pagamento.id,
                    "forma_pagamento_id": pagamento.forma_pagamento_id,
                    "forma_pagamento_nome": pagamento.forma_pagamento.nome if pagamento.forma_pagamento else None,
                    "valor": str(PdvService._to_decimal_value(pagamento.valor)),
                    "comprovante": pagamento.comprovante,
                }
                for pagamento in venda.pagamentos
            ],
            "permite_cancelamento": venda.status == StatusVenda.FINALIZADA,
        }

    @staticmethod
    def _garantir_base_operacional(tenant_id):
        try:
            TenantBootstrapService.garantir_cadastros_operacionais(tenant_id)
            PdvRepository.salvar()
        except Exception:
            PdvRepository.rollback()
            raise

    @staticmethod
    def _validar_cupom(codigo, tenant_id):
        if not codigo:
            return None

        cupom = PdvRepository.buscar_cupom_por_codigo(codigo, tenant_id)
        if not cupom or not cupom.ativo:
            raise ValueError("Cupom nao encontrado.")

        if cupom.data_validade < date.today():
            raise ValueError("Cupom expirado.")

        return cupom

    @staticmethod
    def _calcular_desconto_cupom(cupom, subtotal):
        if not cupom:
            return Decimal("0.00")

        valor_desconto = PdvService._to_decimal_value(cupom.valor_desconto)
        if cupom.tipo_desconto == TipoDesconto.PERCENTUAL:
            return ((subtotal * valor_desconto) / Decimal("100")).quantize(Decimal("0.01"))

        return min(valor_desconto, subtotal).quantize(Decimal("0.01"))

    @staticmethod
    def _validar_pagamentos(pagamentos_payload, tenant_id, total_esperado):
        formas_ids = [
            PdvService._to_int(item.get("forma_pagamento_id"), "Forma de pagamento")
            for item in pagamentos_payload
        ]
        formas = {
            forma.id: forma
            for forma in PdvRepository.buscar_formas_pagamento_por_ids(formas_ids, tenant_id)
        }

        if len(formas) != len(set(formas_ids)):
            raise ValueError("Uma ou mais formas de pagamento nao foram encontradas.")

        pagamentos_compilados = []
        total_pagamentos = Decimal("0.00")

        for pagamento in pagamentos_payload:
            forma_pagamento_id = PdvService._to_int(pagamento.get("forma_pagamento_id"), "Forma de pagamento")
            valor = PdvService._to_decimal(pagamento.get("valor"), "valor do pagamento")
            comprovante = (pagamento.get("comprovante") or "").strip() or None

            pagamentos_compilados.append({
                "forma_pagamento": formas[forma_pagamento_id],
                "valor": valor,
                "comprovante": comprovante,
            })
            total_pagamentos += valor

        if total_pagamentos.quantize(Decimal("0.01")) != total_esperado.quantize(Decimal("0.01")):
            raise ValueError("A soma dos pagamentos deve ser igual ao total da venda.")

        return pagamentos_compilados

    @staticmethod
    def _mesclar_observacao(observacao_atual, observacao_nova):
        if observacao_atual and observacao_nova:
            return f"{observacao_atual}\n{observacao_nova}"
        return observacao_nova or observacao_atual

    @staticmethod
    def _gerar_numero_unico(empresa_id):
        timestamp = TimeService.now_utc_naive().strftime("%Y%m%d%H%M%S")
        return f"VEN-{empresa_id}-{timestamp}-{uuid4().hex[:6].upper()}"

    @staticmethod
    def _to_optional_status(value):
        if value in (None, ""):
            return None

        try:
            return StatusVenda[(value or "").strip().upper()]
        except KeyError:
            raise ValueError("Status de venda invalido.")

    @staticmethod
    def _to_int(value, field_name):
        if value in (None, ""):
            raise ValueError(f"{field_name} e obrigatorio.")

        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} invalido.")

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
    def _to_decimal(value, field_name):
        if value in (None, ""):
            raise ValueError(f"Informe {field_name}.")

        try:
            valor = Decimal(str(value).replace(",", "."))
        except (InvalidOperation, ValueError):
            raise ValueError(f"Valor invalido para {field_name}.")

        if valor <= 0:
            raise ValueError(f"{field_name.capitalize()} deve ser maior que zero.")

        return valor.quantize(Decimal("0.01"))

    @staticmethod
    def _to_optional_decimal(value, field_name):
        if value in (None, ""):
            return Decimal("0.00") if field_name == "desconto manual" else None

        try:
            valor = Decimal(str(value).replace(",", "."))
        except (InvalidOperation, ValueError):
            raise ValueError(f"Valor invalido para {field_name}.")

        if valor < 0:
            raise ValueError(f"{field_name.capitalize()} nao pode ser negativo.")

        return valor.quantize(Decimal("0.01"))

    @staticmethod
    def _to_decimal_value(value):
        if isinstance(value, Decimal):
            return value.quantize(Decimal("0.01"))

        try:
            return Decimal(str(value or 0)).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError):
            return Decimal("0.00")
