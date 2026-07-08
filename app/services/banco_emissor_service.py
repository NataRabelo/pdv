from decimal import Decimal
from app.models.db import (
    BancoEmissor, ConfiguracaoParcelamento, RegraJurosMulta,
    LayoutArquivoBoleto, AmbienteBoleto, TipoMultaBoleto, TipoJurosBoleto,
    BaseCalculoJurosMulta, RegraDistribuicaoParcelamento, db
)
from app.repositorys.boleto_repository import BoletoRepository
from app.services.acesso_empresa_service import AcessoEmpresaService
from app.services.time_service import TimeService


class BancoEmissorService:
    """Service para gerenciar bancos emissores e suas configurações"""

    @staticmethod
    def criar_banco_emissor(data, tenant_id, escopo, funcionario_id):
        """Cria um novo banco emissor para uma empresa"""
        try:
            empresa_id = BancoEmissorService._to_int(data.get("empresa_id"), "empresa_id")
            AcessoEmpresaService.validar_empresa(empresa_id, escopo)

            # Validar dados obrigatórios
            banco_codigo = (data.get("banco_codigo") or "").strip()
            if not banco_codigo:
                raise ValueError("banco_codigo é obrigatório")
            if len(banco_codigo) > 20:
                raise ValueError("banco_codigo não pode ter mais de 20 caracteres")

            banco_nome = (data.get("banco_nome") or "").strip()
            if not banco_nome:
                raise ValueError("banco_nome é obrigatório")
            if len(banco_nome) > 120:
                raise ValueError("banco_nome não pode ter mais de 120 caracteres")

            carteira = (data.get("carteira") or "").strip()
            if not carteira:
                raise ValueError("carteira é obrigatória")

            agencia = (data.get("agencia") or "").strip()
            if not agencia:
                raise ValueError("agencia é obrigatória")

            conta = (data.get("conta") or "").strip()
            if not conta:
                raise ValueError("conta é obrigatória")

            codigo_cedente = (data.get("codigo_cedente") or "").strip()
            if not codigo_cedente:
                raise ValueError("codigo_cedente é obrigatório")

            # Campos opcionais
            convenio = (data.get("convenio") or "").strip() or None
            agencia_dv = (data.get("agencia_dv") or "").strip() or None
            conta_dv = (data.get("conta_dv") or "").strip() or None
            variacao_carteira = (data.get("variacao_carteira") or "").strip() or None

            # Enums com defaults
            layout_arquivo = data.get("layout_arquivo", "CNAB400")
            try:
                layout_arquivo = LayoutArquivoBoleto[layout_arquivo]
            except KeyError:
                raise ValueError(f"layout_arquivo inválido: {layout_arquivo}")

            ambiente = data.get("ambiente", "sandbox")
            try:
                ambiente = AmbienteBoleto[ambiente]
            except KeyError:
                raise ValueError(f"ambiente inválido: {ambiente}")

            especie_documento = (data.get("especie_documento") or "DM").strip()
            credenciais_api_ref = (data.get("credenciais_api_ref") or "").strip() or None

            # Criar banco
            banco_emissor = BancoEmissor(
                tenant_id=tenant_id,
                empresa_id=empresa_id,
                banco_codigo=banco_codigo,
                banco_nome=banco_nome,
                convenio=convenio,
                carteira=carteira,
                variacao_carteira=variacao_carteira,
                agencia=agencia,
                agencia_dv=agencia_dv,
                conta=conta,
                conta_dv=conta_dv,
                codigo_cedente=codigo_cedente,
                especie_documento=especie_documento,
                layout_arquivo=layout_arquivo,
                ambiente=ambiente,
                credenciais_api_ref=credenciais_api_ref,
                is_padrao=bool(data.get("is_padrao", False)),
                ativo=bool(data.get("ativo", True))
            )

            BoletoRepository.adicionar(banco_emissor)
            BoletoRepository.salvar()
            return BancoEmissorService.serializar_banco_emissor(banco_emissor)

        except Exception:
            BoletoRepository.rollback()
            raise

    @staticmethod
    def criar_configuracao_parcelamento(data, tenant_id, escopo):
        """Cria uma configuração de parcelamento para um banco"""
        try:
            empresa_id = BancoEmissorService._to_int(data.get("empresa_id"), "empresa_id")
            AcessoEmpresaService.validar_empresa(empresa_id, escopo)

            banco_emissor_id = data.get("banco_emissor_id")
            if banco_emissor_id:
                banco_emissor = BoletoRepository.buscar_banco_emissor(banco_emissor_id, tenant_id, empresa_id=empresa_id)
                if not banco_emissor:
                    raise ValueError("Banco emissor não encontrado")

            numero_max_parcelas = BancoEmissorService._to_int(data.get("numero_max_parcelas"), "numero_max_parcelas")
            numero_min_parcelas = BancoEmissorService._to_int(data.get("numero_min_parcelas", 1), "numero_min_parcelas")
            intervalo_dias_padrao = BancoEmissorService._to_int(data.get("intervalo_dias_padrao", 30), "intervalo_dias_padrao")

            if numero_min_parcelas < 1:
                raise ValueError("numero_min_parcelas deve ser >= 1")
            if numero_max_parcelas < numero_min_parcelas:
                raise ValueError("numero_max_parcelas deve ser >= numero_min_parcelas")
            if intervalo_dias_padrao < 1:
                raise ValueError("intervalo_dias_padrao deve ser >= 1")

            valor_minimo_por_parcela = BancoEmissorService._to_decimal(
                data.get("valor_minimo_por_parcela", "0.01"),
                "valor_minimo_por_parcela"
            )

            dia_fixo_vencimento = data.get("dia_fixo_vencimento")
            if dia_fixo_vencimento is not None:
                dia_fixo_vencimento = int(dia_fixo_vencimento)
                if dia_fixo_vencimento < 1 or dia_fixo_vencimento > 28:
                    raise ValueError("dia_fixo_vencimento deve estar entre 1 e 28")

            regra_distribuicao = data.get("regra_distribuicao", "proporcional")
            try:
                regra_distribuicao = RegraDistribuicaoParcelamento[regra_distribuicao]
            except KeyError:
                raise ValueError(f"regra_distribuicao inválida: {regra_distribuicao}")

            config = ConfiguracaoParcelamento(
                tenant_id=tenant_id,
                empresa_id=empresa_id,
                banco_emissor_id=banco_emissor_id,
                numero_min_parcelas=numero_min_parcelas,
                numero_max_parcelas=numero_max_parcelas,
                intervalo_dias_padrao=intervalo_dias_padrao,
                permite_intervalo_customizado=bool(data.get("permite_intervalo_customizado", False)),
                dia_fixo_vencimento=dia_fixo_vencimento,
                valor_minimo_por_parcela=valor_minimo_por_parcela,
                regra_distribuicao=regra_distribuicao,
                arredondamento_ultima_parcela=bool(data.get("arredondamento_ultima_parcela", True)),
                ativo=bool(data.get("ativo", True))
            )

            BoletoRepository.adicionar(config)
            BoletoRepository.salvar()
            return BancoEmissorService.serializar_configuracao_parcelamento(config)

        except Exception:
            BoletoRepository.rollback()
            raise

    @staticmethod
    def criar_regra_juros_multa(data, tenant_id, escopo):
        """Cria uma regra de juros e multa para um banco"""
        try:
            empresa_id = BancoEmissorService._to_int(data.get("empresa_id"), "empresa_id")
            AcessoEmpresaService.validar_empresa(empresa_id, escopo)

            banco_emissor_id = data.get("banco_emissor_id")
            if banco_emissor_id:
                banco_emissor = BoletoRepository.buscar_banco_emissor(banco_emissor_id, tenant_id, empresa_id=empresa_id)
                if not banco_emissor:
                    raise ValueError("Banco emissor não encontrado")

            # Tipo de multa
            tipo_multa = data.get("tipo_multa", "nenhum")
            try:
                tipo_multa = TipoMultaBoleto[tipo_multa]
            except KeyError:
                raise ValueError(f"tipo_multa inválido: {tipo_multa}")

            percentual_multa = None
            valor_fixo_multa = None

            if tipo_multa == TipoMultaBoleto.percentual:
                percentual_multa = BancoEmissorService._to_decimal(
                    data.get("percentual_multa"), "percentual_multa"
                )
            elif tipo_multa == TipoMultaBoleto.fixo:
                valor_fixo_multa = BancoEmissorService._to_decimal(
                    data.get("valor_fixo_multa"), "valor_fixo_multa"
                )

            # Tipo de juros
            tipo_juros = data.get("tipo_juros", "nenhum")
            try:
                tipo_juros = TipoJurosBoleto[tipo_juros]
            except KeyError:
                raise ValueError(f"tipo_juros inválido: {tipo_juros}")

            percentual_juros = None
            if tipo_juros != TipoJurosBoleto.nenhum:
                percentual_juros = BancoEmissorService._to_decimal(
                    data.get("percentual_juros"), "percentual_juros"
                )

            dias_carencia = BancoEmissorService._to_int(data.get("dias_carencia", 0), "dias_carencia")
            if dias_carencia < 0:
                raise ValueError("dias_carencia não pode ser negativo")

            base_calculo = data.get("base_calculo", "valor_restante")
            try:
                base_calculo = BaseCalculoJurosMulta[base_calculo]
            except KeyError:
                raise ValueError(f"base_calculo inválida: {base_calculo}")

            percentual_maximo_teto = BancoEmissorService._to_decimal(
                data.get("percentual_maximo_teto", "100.00"),
                "percentual_maximo_teto"
            )

            regra = RegraJurosMulta(
                tenant_id=tenant_id,
                empresa_id=empresa_id,
                banco_emissor_id=banco_emissor_id,
                tipo_multa=tipo_multa,
                percentual_multa=percentual_multa,
                valor_fixo_multa=valor_fixo_multa,
                tipo_juros=tipo_juros,
                percentual_juros=percentual_juros,
                dias_carencia=dias_carencia,
                base_calculo=base_calculo,
                percentual_maximo_teto=percentual_maximo_teto,
                vigente_desde=TimeService.now_utc_naive(),
                vigente_ate=None,
                ativo=bool(data.get("ativo", True))
            )

            BoletoRepository.adicionar(regra)
            BoletoRepository.salvar()
            return BancoEmissorService.serializar_regra_juros_multa(regra)

        except Exception:
            BoletoRepository.rollback()
            raise

    @staticmethod
    def serializar_banco_emissor(banco):
        """Converte objeto banco_emissor para dict"""
        return {
            "id": banco.id,
            "empresa_id": banco.empresa_id,
            "banco_codigo": banco.banco_codigo,
            "banco_nome": banco.banco_nome,
            "convenio": banco.convenio,
            "carteira": banco.carteira,
            "variacao_carteira": banco.variacao_carteira,
            "agencia": banco.agencia,
            "agencia_dv": banco.agencia_dv,
            "conta": banco.conta,
            "conta_dv": banco.conta_dv,
            "codigo_cedente": banco.codigo_cedente,
            "especie_documento": banco.especie_documento,
            "layout_arquivo": banco.layout_arquivo.value if banco.layout_arquivo else None,
            "ambiente": banco.ambiente.value if banco.ambiente else None,
            "credenciais_api_ref": banco.credenciais_api_ref,
            "is_padrao": banco.is_padrao,
            "ativo": banco.ativo,
            "criado_em": banco.criado_em.isoformat() if banco.criado_em else None,
        }

    @staticmethod
    def serializar_configuracao_parcelamento(config):
        """Converte objeto configuracao_parcelamento para dict"""
        return {
            "id": config.id,
            "empresa_id": config.empresa_id,
            "banco_emissor_id": config.banco_emissor_id,
            "numero_min_parcelas": config.numero_min_parcelas,
            "numero_max_parcelas": config.numero_max_parcelas,
            "intervalo_dias_padrao": config.intervalo_dias_padrao,
            "permite_intervalo_customizado": bool(config.permite_intervalo_customizado),
            "dia_fixo_vencimento": config.dia_fixo_vencimento,
            "valor_minimo_por_parcela": str(config.valor_minimo_por_parcela),
            "regra_distribuicao": config.regra_distribuicao.value if config.regra_distribuicao else None,
            "arredondamento_ultima_parcela": bool(config.arredondamento_ultima_parcela),
            "ativo": config.ativo,
            "criado_em": config.criado_em.isoformat() if config.criado_em else None,
        }

    @staticmethod
    def serializar_regra_juros_multa(regra):
        """Converte objeto regra_juros_multa para dict"""
        return {
            "id": regra.id,
            "empresa_id": regra.empresa_id,
            "banco_emissor_id": regra.banco_emissor_id,
            "tipo_multa": regra.tipo_multa.value if regra.tipo_multa else None,
            "percentual_multa": str(regra.percentual_multa) if regra.percentual_multa else None,
            "valor_fixo_multa": str(regra.valor_fixo_multa) if regra.valor_fixo_multa else None,
            "tipo_juros": regra.tipo_juros.value if regra.tipo_juros else None,
            "percentual_juros": str(regra.percentual_juros) if regra.percentual_juros else None,
            "dias_carencia": regra.dias_carencia,
            "base_calculo": regra.base_calculo.value if regra.base_calculo else None,
            "percentual_maximo_teto": str(regra.percentual_maximo_teto),
            "vigente_desde": regra.vigente_desde.isoformat() if regra.vigente_desde else None,
            "vigente_ate": regra.vigente_ate.isoformat() if regra.vigente_ate else None,
            "ativo": regra.ativo,
            "criado_em": regra.criado_em.isoformat() if regra.criado_em else None,
        }

    @staticmethod
    def _to_int(value, field_name):
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} deve ser um número inteiro válido")

    @staticmethod
    def _to_decimal(value, field_name):
        try:
            valor = Decimal(str(value).replace(",", "."))
        except:
            raise ValueError(f"Valor inválido para {field_name}")
        if valor < 0:
            raise ValueError(f"{field_name} não pode ser negativo")
        return valor.quantize(Decimal("0.01"))
