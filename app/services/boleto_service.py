from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from app.extensions import db
from app.models.db import (
    BaseCalculoJurosMulta,
    Boleto,
    CategoriaFinanceira,
    ConfiguracaoParcelamento,
    EventoBoleto,
    FormaPagamento,
    LancamentoFinanceiro,
    ParcelaBoleto,
    RegraJurosMulta,
    StatusBoleto,
    TipoEventoBoleto,
    TipoFinanceiro,
    TipoJurosBoleto,
    TipoMultaBoleto,
)
from app.repositorys.boleto_repository import BoletoRepository
from app.services.acesso_empresa_service import AcessoEmpresaService
from app.services.time_service import TimeService
from app.services.tenant_bootstrap_service import TenantBootstrapService


class BoletoService:
    @staticmethod
    def listar_bancos_emissores(tenant_id, escopo, empresa_id=None, ativo=None):
        empresa_ids = AcessoEmpresaService.filtrar_empresa_ids(escopo)
        if empresa_id:
            AcessoEmpresaService.validar_empresa(empresa_id, escopo)
        bancos = BoletoRepository.listar_bancos_emissores(tenant_id, empresa_ids=empresa_ids, empresa_id=empresa_id, ativo=ativo)
        return [{
            "id": item.id,
            "empresa_id": item.empresa_id,
            "banco_codigo": item.banco_codigo,
            "banco_nome": item.banco_nome,
            "carteira": item.carteira,
            "agencia": item.agencia,
            "conta": item.conta,
            "codigo_cedente": item.codigo_cedente,
            "layout_arquivo": item.layout_arquivo.value if item.layout_arquivo else None,
            "ambiente": item.ambiente.value if item.ambiente else None,
            "is_padrao": bool(item.is_padrao),
            "ativo": bool(item.ativo),
        } for item in bancos]

    @staticmethod
    def listar_configuracoes_parcelamento(tenant_id, escopo, empresa_id=None, ativo=None):
        empresa_ids = AcessoEmpresaService.filtrar_empresa_ids(escopo)
        if empresa_id:
            AcessoEmpresaService.validar_empresa(empresa_id, escopo)
        configs = BoletoRepository.listar_configuracoes_parcelamento(tenant_id, empresa_ids=empresa_ids, empresa_id=empresa_id, ativo=ativo)
        return [{
            "id": item.id,
            "empresa_id": item.empresa_id,
            "banco_emissor_id": item.banco_emissor_id,
            "numero_min_parcelas": item.numero_min_parcelas,
            "numero_max_parcelas": item.numero_max_parcelas,
            "intervalo_dias_padrao": item.intervalo_dias_padrao,
            "permite_intervalo_customizado": bool(item.permite_intervalo_customizado),
            "dia_fixo_vencimento": item.dia_fixo_vencimento,
            "valor_minimo_por_parcela": str(item.valor_minimo_por_parcela),
            "regra_distribuicao": item.regra_distribuicao.value if item.regra_distribuicao else None,
            "arredondamento_ultima_parcela": bool(item.arredondamento_ultima_parcela),
            "ativo": bool(item.ativo),
        } for item in configs]

    @staticmethod
    def listar_regras_juros_multa(tenant_id, escopo, empresa_id=None):
        empresa_ids = AcessoEmpresaService.filtrar_empresa_ids(escopo)
        if empresa_id:
            AcessoEmpresaService.validar_empresa(empresa_id, escopo)
        regras = BoletoRepository.listar_regras_juros_multa(tenant_id, empresa_ids=empresa_ids, empresa_id=empresa_id)
        return [{
            "id": item.id,
            "empresa_id": item.empresa_id,
            "banco_emissor_id": item.banco_emissor_id,
            "tipo_multa": item.tipo_multa.value if item.tipo_multa else None,
            "percentual_multa": str(item.percentual_multa) if item.percentual_multa is not None else None,
            "valor_fixo_multa": str(item.valor_fixo_multa) if item.valor_fixo_multa is not None else None,
            "tipo_juros": item.tipo_juros.value if item.tipo_juros else None,
            "percentual_juros": str(item.percentual_juros) if item.percentual_juros is not None else None,
            "dias_carencia": item.dias_carencia,
            "base_calculo": item.base_calculo.value if item.base_calculo else None,
            "percentual_maximo_teto": str(item.percentual_maximo_teto),
            "vigente_desde": item.vigente_desde.isoformat() if item.vigente_desde else None,
            "vigente_ate": item.vigente_ate.isoformat() if item.vigente_ate else None,
            "ativo": bool(item.ativo),
        } for item in regras]

    @staticmethod
    def listar_boletos(tenant_id, escopo, empresa_id=None, status=None, banco_emissor_id=None, limite=100):
        empresa_ids = AcessoEmpresaService.filtrar_empresa_ids(escopo)
        if empresa_id:
            AcessoEmpresaService.validar_empresa(empresa_id, escopo)
        boletos = BoletoRepository.listar_boletos(
            tenant_id,
            empresa_ids=empresa_ids,
            empresa_id=empresa_id,
            status=status,
            banco_emissor_id=banco_emissor_id,
            limite=limite,
        )
        return [BoletoService.serializar_boleto(item) for item in boletos]

    @staticmethod
    def buscar_boleto(tenant_id, escopo, boleto_id, empresa_id=None):
        if empresa_id:
            AcessoEmpresaService.validar_empresa(empresa_id, escopo)
        boleto = BoletoRepository.buscar_boleto(boleto_id, tenant_id, empresa_id=empresa_id)
        if not boleto:
            raise LookupError("Boleto nao encontrado.")
        return BoletoService.serializar_boleto(boleto)

    @staticmethod
    def criar_boleto(data, tenant_id, escopo, funcionario_id):
        try:
            empresa_id = BoletoService._to_int(data.get("empresa_id"), "empresa_id")
            AcessoEmpresaService.validar_empresa(empresa_id, escopo)

            cliente_id = BoletoService._to_int(data.get("cliente_id"), "cliente_id")
            banco_emissor_id = BoletoService._to_int(data.get("banco_emissor_id"), "banco_emissor_id")
            forma_pagamento_id = BoletoService._to_int(data.get("forma_pagamento_id"), "forma_pagamento_id")
            categoria_id = BoletoService._to_int(data.get("categoria_id"), "categoria_id")
            valor_nominal = BoletoService._to_decimal(data.get("valor_nominal"), "valor_nominal")
            data_vencimento = BoletoService._to_optional_date(data.get("data_vencimento"))
            if data_vencimento is None:
                raise ValueError("data_vencimento e obrigatoria.")
            numero_boleto = (data.get("numero_boleto") or "").strip() or BoletoService._gerar_numero_boleto(tenant_id)
            if BoletoRepository.existe_numero_boleto(tenant_id, numero_boleto):
                raise ValueError("Ja existe um boleto com esse numero.")

            banco_emissor = BoletoRepository.buscar_banco_emissor(banco_emissor_id, tenant_id, empresa_id=empresa_id)
            if not banco_emissor or not banco_emissor.ativo:
                raise ValueError("Banco emissor nao encontrado ou inativo.")
            forma_pagamento = db.session.get(FormaPagamento, forma_pagamento_id)
            if not forma_pagamento or not forma_pagamento.ativo:
                raise ValueError("Forma de pagamento invalida.")
            categoria = db.session.get(CategoriaFinanceira, categoria_id)
            if not categoria or not categoria.ativo:
                raise ValueError("Categoria financeira invalida.")

            boleto = Boleto(
                tenant_id=tenant_id,
                empresa_id=empresa_id,
                cliente_id=cliente_id,
                venda_id=data.get("venda_id"),
                banco_emissor_id=banco_emissor.id,
                configuracao_parcelamento_id=data.get("configuracao_parcelamento_id"),
                numero_boleto=numero_boleto,
                nosso_numero=data.get("nosso_numero"),
                status=StatusBoleto.PENDENTE,
                valor_nominal=valor_nominal,
                valor_pago=Decimal("0.00"),
                valor_restante=valor_nominal,
                data_emissao=TimeService.now_utc_naive(),
                data_vencimento=data_vencimento,
                data_pagamento=None,
                data_baixa=None,
                forma_pagamento_id=forma_pagamento.id,
                categoria_id=categoria.id,
                codigo_barras=data.get("codigo_barras"),
                linha_digitavel=data.get("linha_digitavel"),
                arquivo_pdf_path=data.get("arquivo_pdf_path"),
                arquivo_html_path=data.get("arquivo_html_path"),
                observacao=(data.get("observacao") or "").strip() or None,
            )
            BoletoRepository.adicionar(boleto)
            BoletoRepository.flush()

            parcelas = BoletoService._criar_parcelas(boleto, data, tenant_id, funcionario_id)
            boleto.status = StatusBoleto.EMITIDO if parcelas else StatusBoleto.PENDENTE
            if parcelas:
                boleto.valor_restante = sum((p.valor_restante or Decimal("0.00")) for p in parcelas)
            BoletoRepository.salvar()
            BoletoService._registrar_evento(boleto, None, TipoEventoBoleto.EMISSAO, "Boleto emitido", None, funcionario_id)
            return BoletoService.serializar_boleto(boleto)
        except Exception:
            BoletoRepository.rollback()
            raise

    @staticmethod
    def _criar_parcelas(boleto, data, tenant_id, funcionario_id):
        parcelas_input = data.get("parcelas") or []
        if not parcelas_input:
            return []

        parcelas = []
        for item in parcelas_input:
            numero_parcela = int(item.get("numero_parcela") or 1)
            valor_parcela = BoletoService._to_decimal(item.get("valor_parcela"), "valor_parcela")
            data_vencimento = BoletoService._to_optional_date(item.get("data_vencimento")) or boleto.data_vencimento
            parcela = ParcelaBoleto(
                boleto_id=boleto.id,
                numero_parcela=numero_parcela,
                valor_parcela=valor_parcela,
                valor_pago=Decimal("0.00"),
                valor_restante=valor_parcela,
                data_vencimento=data_vencimento,
                data_pagamento=None,
                status=StatusBoleto.EMITIDO,
                juros_calculados=Decimal("0.00"),
                multa_calculada=Decimal("0.00"),
                desconto_aplicado=Decimal("0.00"),
                observacao=(item.get("observacao") or "").strip() or None,
            )
            BoletoRepository.adicionar(parcela)
            parcelas.append(parcela)
        BoletoRepository.flush()
        return parcelas

    @staticmethod
    def baixar_boleto(tenant_id, escopo, boleto_id, data, funcionario_id):
        try:
            boleto = BoletoRepository.buscar_boleto(boleto_id, tenant_id)
            if not boleto:
                raise LookupError("Boleto nao encontrado.")
            AcessoEmpresaService.validar_empresa(boleto.empresa_id, escopo)
            valor = BoletoService._to_decimal(data.get("valor_pago") or data.get("valor"), "valor_pago")
            if valor <= 0:
                raise ValueError("valor_pago deve ser maior que zero.")
            if boleto.status in [StatusBoleto.PAGO, StatusBoleto.CANCELADO, StatusBoleto.ESTORNADO]:
                raise ValueError("Esse boleto nao pode receber baixa.")

            if boleto.valor_restante < valor:
                raise ValueError("valor_pago nao pode exceder o valor restante do boleto.")

            boleto.valor_pago = (boleto.valor_pago + valor).quantize(Decimal("0.01"))
            boleto.valor_restante = (boleto.valor_restante - valor).quantize(Decimal("0.01"))
            boleto.data_pagamento = TimeService.now_utc_naive()
            boleto.data_baixa = TimeService.now_utc_naive()
            boleto.status = StatusBoleto.PAGO if boleto.valor_restante <= Decimal("0.00") else StatusBoleto.PARCIALMENTE_PAGO

            lancamento = LancamentoFinanceiro(
                tenant_id=tenant_id,
                empresa_id=boleto.empresa_id,
                funcionario_id=funcionario_id,
                categoria_id=boleto.categoria_id,
                forma_pagamento_id=boleto.forma_pagamento_id,
                boleto_id=boleto.id,
                parcela_boleto_id=None,
                tipo=TipoFinanceiro.ENTRADA,
                descricao=f"Baixa de boleto {boleto.numero_boleto}",
                valor=valor,
                data_lancamento=TimeService.now_utc_naive(),
                data_competencia=date.today(),
                observacao="Baixa de boleto via service",
            )
            BoletoRepository.adicionar(lancamento)
            BoletoService._registrar_evento(boleto, None, TipoEventoBoleto.PAGAMENTO, "Baixa registrada", valor, funcionario_id)
            BoletoRepository.salvar()
            return BoletoService.serializar_boleto(boleto)
        except Exception:
            BoletoRepository.rollback()
            raise

    @staticmethod
    def recalcular_juros_multa(tenant_id, escopo, boleto_id, data_referencia=None, funcionario_id=None):
        try:
            boleto = BoletoRepository.buscar_boleto(boleto_id, tenant_id)
            if not boleto:
                raise LookupError("Boleto nao encontrado.")
            AcessoEmpresaService.validar_empresa(boleto.empresa_id, escopo)
            data_ref = BoletoService._to_optional_date(data_referencia) or date.today()
            regra = BoletoRepository.buscar_regra_vigente_em(tenant_id, boleto.empresa_id, data_ref, banco_emissor_id=boleto.banco_emissor_id)
            if regra is None:
                raise ValueError("Nao existe regra de juros/multa vigente para esta empresa.")

            total_juros = Decimal("0.00")
            total_multa = Decimal("0.00")
            for parcela in boleto.parcelas:
                resultado = BoletoService.calcular_juros_multa(
                    valor_nominal=parcela.valor_parcela,
                    valor_pago=parcela.valor_pago,
                    data_vencimento=parcela.data_vencimento,
                    data_referencia=data_ref,
                    regra={
                        "tipo_multa": regra.tipo_multa,
                        "percentual_multa": regra.percentual_multa,
                        "valor_fixo_multa": regra.valor_fixo_multa,
                        "tipo_juros": regra.tipo_juros,
                        "percentual_juros": regra.percentual_juros,
                        "dias_carencia": regra.dias_carencia,
                        "base_calculo": regra.base_calculo,
                    },
                )
                parcela.juros_calculados = resultado["juros"]
                parcela.multa_calculada = resultado["multa"]
                parcela.valor_restante = (parcela.valor_parcela + resultado["juros"] + resultado["multa"] - parcela.valor_pago).quantize(Decimal("0.01"))
                if parcela.valor_restante < Decimal("0.00"):
                    parcela.valor_restante = Decimal("0.00")
                total_juros += resultado["juros"]
                total_multa += resultado["multa"]

            boleto.valor_restante = (boleto.valor_restante + total_juros + total_multa).quantize(Decimal("0.01"))
            if boleto.data_vencimento < data_ref and boleto.status == StatusBoleto.EMITIDO:
                boleto.status = StatusBoleto.VENCIDO
            BoletoService._registrar_evento(boleto, None, TipoEventoBoleto.RECALCULO_JUROS, "Recalculo de juros/multa aplicado", total_juros + total_multa, funcionario_id)
            BoletoRepository.salvar()
            return BoletoService.serializar_boleto(boleto)
        except Exception:
            BoletoRepository.rollback()
            raise

    @staticmethod
    def calcular_juros_multa(valor_nominal, valor_pago, data_vencimento, data_referencia, regra):
        valor_nominal = BoletoService._to_decimal_value(valor_nominal)
        valor_pago = BoletoService._to_decimal_value(valor_pago)
        data_vencimento = BoletoService._to_optional_date(data_vencimento)
        data_referencia = BoletoService._to_optional_date(data_referencia)
        if data_referencia is None:
            data_referencia = date.today()
        if data_vencimento is None:
            raise ValueError("data_vencimento e obrigatoria.")
        if data_referencia < data_vencimento:
            return {"multa": Decimal("0.00"), "juros": Decimal("0.00"), "total": Decimal("0.00")}

        multa = Decimal("0.00")
        juros = Decimal("0.00")
        dias_atraso = (data_referencia - data_vencimento).days
        tipo_multa = regra.get("tipo_multa") if isinstance(regra, dict) else getattr(regra, "tipo_multa", None)
        percentual_multa = BoletoService._to_decimal_value(regra.get("percentual_multa") if isinstance(regra, dict) else getattr(regra, "percentual_multa", None))
        valor_fixo_multa = BoletoService._to_decimal_value(regra.get("valor_fixo_multa") if isinstance(regra, dict) else getattr(regra, "valor_fixo_multa", None))
        tipo_juros = regra.get("tipo_juros") if isinstance(regra, dict) else getattr(regra, "tipo_juros", None)
        percentual_juros = BoletoService._to_decimal_value(regra.get("percentual_juros") if isinstance(regra, dict) else getattr(regra, "percentual_juros", None))
        dias_carencia = int(regra.get("dias_carencia") if isinstance(regra, dict) else getattr(regra, "dias_carencia", 0) or 0)
        base_calculo = regra.get("base_calculo") if isinstance(regra, dict) else getattr(regra, "base_calculo", BaseCalculoJurosMulta.valor_restante)

        if dias_atraso > dias_carencia:
            if tipo_multa == TipoMultaBoleto.percentual:
                multa = (valor_nominal * (percentual_multa / Decimal("100"))).quantize(Decimal("0.01"))
            elif tipo_multa == TipoMultaBoleto.fixo:
                multa = valor_fixo_multa

            if tipo_juros == TipoJurosBoleto.diario:
                valor_base = valor_nominal - valor_pago if base_calculo == BaseCalculoJurosMulta.valor_restante else valor_nominal
                juros = (valor_base * (percentual_juros / Decimal("100")) * Decimal(max(dias_atraso - dias_carencia, 0))).quantize(Decimal("0.01"))
            elif tipo_juros == TipoJurosBoleto.mensal:
                valor_base = valor_nominal - valor_pago if base_calculo == BaseCalculoJurosMulta.valor_restante else valor_nominal
                juros = (valor_base * (percentual_juros / Decimal("100")) * Decimal(max((dias_atraso - dias_carencia) // 30, 0))).quantize(Decimal("0.01"))

        total = (multa + juros).quantize(Decimal("0.01"))
        return {"multa": multa.quantize(Decimal("0.01")), "juros": juros.quantize(Decimal("0.01")), "total": total}

    @staticmethod
    def _registrar_evento(boleto, parcela, tipo_evento, descricao, valor, funcionario_id):
        evento = EventoBoleto(
            boleto_id=boleto.id,
            parcela_id=getattr(parcela, "id", None),
            tipo_evento=tipo_evento,
            descricao=descricao,
            valor=BoletoService._to_decimal_value(valor),
            regra_juros_multa_id=None,
            criado_por_funcionario_id=funcionario_id,
            criado_em=TimeService.now_utc_naive(),
        )
        BoletoRepository.adicionar(evento)

    @staticmethod
    def _gerar_numero_boleto(tenant_id):
        return f"{tenant_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    @staticmethod
    def serializar_boleto(boleto):
        return {
            "id": boleto.id,
            "tenant_id": boleto.tenant_id,
            "empresa_id": boleto.empresa_id,
            "cliente_id": boleto.cliente_id,
            "venda_id": boleto.venda_id,
            "banco_emissor_id": boleto.banco_emissor_id,
            "numero_boleto": boleto.numero_boleto,
            "nosso_numero": boleto.nosso_numero,
            "status": boleto.status.value if boleto.status else None,
            "valor_nominal": str(BoletoService._to_decimal_value(boleto.valor_nominal)),
            "valor_pago": str(BoletoService._to_decimal_value(boleto.valor_pago)),
            "valor_restante": str(BoletoService._to_decimal_value(boleto.valor_restante)),
            "data_emissao": TimeService.serialize_utc_iso(boleto.data_emissao),
            "data_vencimento": boleto.data_vencimento.isoformat() if boleto.data_vencimento else None,
            "data_pagamento": TimeService.serialize_utc_iso(boleto.data_pagamento) if boleto.data_pagamento else None,
            "data_baixa": TimeService.serialize_utc_iso(boleto.data_baixa) if boleto.data_baixa else None,
            "forma_pagamento_id": boleto.forma_pagamento_id,
            "categoria_id": boleto.categoria_id,
            "codigo_barras": boleto.codigo_barras,
            "linha_digitavel": boleto.linha_digitavel,
            "arquivo_pdf_path": boleto.arquivo_pdf_path,
            "arquivo_html_path": boleto.arquivo_html_path,
            "observacao": boleto.observacao,
            "parcelas": [{
                "id": item.id,
                "numero_parcela": item.numero_parcela,
                "valor_parcela": str(BoletoService._to_decimal_value(item.valor_parcela)),
                "valor_pago": str(BoletoService._to_decimal_value(item.valor_pago)),
                "valor_restante": str(BoletoService._to_decimal_value(item.valor_restante)),
                "data_vencimento": item.data_vencimento.isoformat() if item.data_vencimento else None,
                "data_pagamento": TimeService.serialize_utc_iso(item.data_pagamento) if item.data_pagamento else None,
                "status": item.status.value if item.status else None,
                "juros_calculados": str(BoletoService._to_decimal_value(item.juros_calculados)),
                "multa_calculada": str(BoletoService._to_decimal_value(item.multa_calculada)),
                "desconto_aplicado": str(BoletoService._to_decimal_value(item.desconto_aplicado)),
                "observacao": item.observacao,
            } for item in getattr(boleto, "parcelas", []) or []],
            "eventos": [{
                "id": item.id,
                "tipo_evento": item.tipo_evento.value if item.tipo_evento else None,
                "descricao": item.descricao,
                "valor": str(BoletoService._to_decimal_value(item.valor)),
                "criado_em": TimeService.serialize_utc_iso(item.criado_em),
            } for item in getattr(boleto, "eventos", []) or []],
        }

    @staticmethod
    def _to_int(value, field_name):
        if value in (None, ""):
            raise ValueError(f"{field_name} e obrigatorio.")
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} invalido.")

    @staticmethod
    def _to_decimal(value, field_name):
        if value in (None, ""):
            raise ValueError(f"Informe {field_name}.")
        try:
            valor = Decimal(str(value).replace(",", "."))
        except (InvalidOperation, ValueError):
            raise ValueError(f"Valor invalido para {field_name}.")
        if valor < 0:
            raise ValueError(f"{field_name.capitalize()} nao pode ser negativo.")
        return valor.quantize(Decimal("0.01"))

    @staticmethod
    def _to_decimal_value(value):
        try:
            return Decimal(str(value or 0)).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError):
            return Decimal("0.00")

    @staticmethod
    def _to_optional_date(value):
        if value in (None, ""):
            return None
        try:
            return datetime.strptime(str(value), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Data invalida. Use o formato YYYY-MM-DD.")
