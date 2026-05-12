import os

from app.models.db import (
    AmbienteFiscal,
    ConfiguracaoFiscalEmpresa,
    NotaFiscalVenda,
    RegimeTributarioFiscal,
    StatusNotaFiscal,
    StatusVenda,
)
from app.repositorys.fiscal_repository import FiscalRepository
from app.services.acesso_empresa_service import AcessoEmpresaService
from app.services.time_service import TimeService


class FiscalService:
    REQUIRED_CONFIG_FIELDS = (
        ("inscricao_estadual", "Inscricao estadual"),
        ("uf", "UF"),
        ("municipio_nome", "Municipio"),
        ("municipio_codigo_ibge", "Codigo IBGE do municipio"),
        ("cep", "CEP"),
        ("logradouro", "Logradouro"),
        ("numero", "Numero"),
        ("bairro", "Bairro"),
        ("certificado_caminho", "Caminho do certificado"),
        ("certificado_senha_env", "Variavel de ambiente da senha do certificado"),
        ("csc_id", "ID do CSC"),
        ("csc_token", "Token CSC"),
    )

    @staticmethod
    def listar_auxiliares(tenant_id, escopo):
        empresa_ids = AcessoEmpresaService.filtrar_empresa_ids(escopo)
        empresas = FiscalRepository.listar_empresas(tenant_id, empresa_ids=empresa_ids)

        return {
            "empresas": [
                {
                    "id": empresa.id,
                    "nome": empresa.nome_fantasia,
                    "configurada": bool(empresa.configuracao_fiscal),
                    "ambiente": (
                        getattr(empresa.configuracao_fiscal.ambiente, "value", AmbienteFiscal.HOMOLOGACAO.value)
                        if empresa.configuracao_fiscal
                        else AmbienteFiscal.HOMOLOGACAO.value
                    ),
                }
                for empresa in empresas
            ],
            "ambientes": [item.value for item in AmbienteFiscal],
            "regimes_tributarios": [item.value for item in RegimeTributarioFiscal],
        }

    @staticmethod
    def obter_configuracao(empresa_id, tenant_id, escopo):
        AcessoEmpresaService.validar_empresa(empresa_id, escopo)
        empresa = FiscalRepository.buscar_empresa(empresa_id, tenant_id)
        if not empresa:
            raise ValueError("Empresa nao encontrada.")

        configuracao = FiscalRepository.buscar_configuracao_por_empresa(empresa_id, tenant_id)
        return FiscalService._serializar_configuracao(
            configuracao or FiscalService._build_default_config(empresa_id, tenant_id),
            empresa=empresa,
        )

    @staticmethod
    def atualizar_configuracao(empresa_id, data, tenant_id, escopo):
        try:
            AcessoEmpresaService.validar_empresa(empresa_id, escopo)
            empresa = FiscalRepository.buscar_empresa(empresa_id, tenant_id)
            if not empresa:
                raise ValueError("Empresa nao encontrada.")

            configuracao = FiscalRepository.buscar_configuracao_por_empresa(empresa_id, tenant_id)
            if not configuracao:
                configuracao = ConfiguracaoFiscalEmpresa(
                    tenant_id=tenant_id,
                    empresa_id=empresa_id,
                )
                FiscalRepository.adicionar(configuracao)

            configuracao.ambiente = FiscalService._to_ambiente(data.get("ambiente"))
            configuracao.regime_tributario = FiscalService._to_regime(data.get("regime_tributario"))
            configuracao.serie_nfce = FiscalService._to_positive_int(data.get("serie_nfce"), "serie NFC-e", default=1)
            configuracao.proximo_numero_nfce = FiscalService._to_positive_int(
                data.get("proximo_numero_nfce"),
                "proximo numero NFC-e",
                default=1,
            )
            configuracao.inscricao_estadual = FiscalService._optional_text(data.get("inscricao_estadual"), max_length=30)
            configuracao.inscricao_municipal = FiscalService._optional_text(data.get("inscricao_municipal"), max_length=30)
            configuracao.cnae = FiscalService._optional_text(data.get("cnae"), max_length=20)
            configuracao.uf = FiscalService._optional_text(data.get("uf"), max_length=2, uppercase=True)
            configuracao.municipio_nome = FiscalService._optional_text(data.get("municipio_nome"), max_length=120)
            configuracao.municipio_codigo_ibge = FiscalService._only_digits(data.get("municipio_codigo_ibge"), max_length=7)
            configuracao.cep = FiscalService._only_digits(data.get("cep"), max_length=8)
            configuracao.logradouro = FiscalService._optional_text(data.get("logradouro"), max_length=180)
            configuracao.numero = FiscalService._optional_text(data.get("numero"), max_length=20)
            configuracao.complemento = FiscalService._optional_text(data.get("complemento"), max_length=120)
            configuracao.bairro = FiscalService._optional_text(data.get("bairro"), max_length=120)
            configuracao.certificado_caminho = FiscalService._optional_text(data.get("certificado_caminho"), max_length=255)
            configuracao.certificado_senha_env = FiscalService._optional_text(
                data.get("certificado_senha_env"),
                max_length=120,
                uppercase=True,
            )
            configuracao.csc_id = FiscalService._optional_text(data.get("csc_id"), max_length=20)
            configuracao.csc_token = FiscalService._optional_text(data.get("csc_token"), max_length=255)
            configuracao.contingencia_ativa = FiscalService._to_bool(data.get("contingencia_ativa"), default=False)

            FiscalService._atualizar_status_certificado(configuracao)
            FiscalRepository.salvar()

            configuracao = FiscalRepository.buscar_configuracao_por_empresa(empresa_id, tenant_id)
            return FiscalService._serializar_configuracao(configuracao, empresa=empresa)
        except Exception:
            FiscalRepository.rollback()
            raise

    @staticmethod
    def listar_notas(tenant_id, escopo, limite=50):
        empresa_ids = AcessoEmpresaService.filtrar_empresa_ids(escopo)
        notas = FiscalRepository.listar_notas(tenant_id, empresa_ids=empresa_ids, limite=limite)
        return [FiscalService._serializar_nota(nota) for nota in notas]

    @staticmethod
    def prevalidar_venda(venda_id, tenant_id, escopo):
        try:
            empresa_ids = AcessoEmpresaService.filtrar_empresa_ids(escopo)
            venda = FiscalRepository.buscar_venda(venda_id, tenant_id, empresa_ids=empresa_ids)
            if not venda:
                raise ValueError("Venda nao encontrada.")

            configuracao = FiscalRepository.buscar_configuracao_por_empresa(venda.empresa_id, tenant_id)
            nota = FiscalRepository.buscar_nota_por_venda(venda.id, tenant_id)
            if not nota:
                nota = NotaFiscalVenda(
                    tenant_id=tenant_id,
                    empresa_id=venda.empresa_id,
                    venda_id=venda.id,
                    configuracao_fiscal_id=configuracao.id if configuracao else None,
                    ambiente=configuracao.ambiente if configuracao else AmbienteFiscal.HOMOLOGACAO,
                    status=StatusNotaFiscal.PENDENTE,
                )
                FiscalRepository.adicionar(nota)

            pendencias = FiscalService._validar_prontidao_venda(venda, configuracao)
            nota.configuracao_fiscal_id = configuracao.id if configuracao else None
            nota.ambiente = configuracao.ambiente if configuracao else AmbienteFiscal.HOMOLOGACAO
            nota.status = (
                StatusNotaFiscal.PRONTA_PARA_EMISSAO if not pendencias else StatusNotaFiscal.VALIDACAO_ERRO
            )
            nota.mensagem_retorno = "\n".join(pendencias) if pendencias else "Venda pronta para emissao fiscal."
            nota.enviado_em = TimeService.now_utc_naive()

            FiscalRepository.salvar()
            nota = FiscalRepository.buscar_nota_por_venda(venda.id, tenant_id)
            return {
                "venda_id": venda.id,
                "venda_numero": venda.numero_unico,
                "status": nota.status.value,
                "pendencias": pendencias,
                "nota": FiscalService._serializar_nota(nota),
            }
        except Exception:
            FiscalRepository.rollback()
            raise

    @staticmethod
    def _validar_prontidao_venda(venda, configuracao):
        pendencias = []

        if venda.status != StatusVenda.FINALIZADA:
            pendencias.append("Somente vendas finalizadas podem seguir para emissao fiscal.")

        if not configuracao:
            pendencias.append("A empresa nao possui configuracao fiscal cadastrada.")
            return pendencias

        for field_name, label in FiscalService.REQUIRED_CONFIG_FIELDS:
            if not getattr(configuracao, field_name, None):
                pendencias.append(f"{label} nao configurado.")

        certificado_ok, certificado_detalhe = FiscalService._validar_certificado(configuracao)
        if not certificado_ok:
            pendencias.append(certificado_detalhe)

        if not venda.itens:
            pendencias.append("A venda nao possui itens para emissao.")
            return pendencias

        for item in venda.itens:
            produto = item.produto
            if not produto:
                pendencias.append(f"Item {item.id} sem produto vinculado.")
                continue
            if not produto.possui_ncm or not (produto.ncm or "").strip():
                pendencias.append(f"Produto '{produto.nome}' sem NCM fiscal configurado.")

        return pendencias

    @staticmethod
    def _serializar_configuracao(configuracao, empresa=None):
        certificado_ok, certificado_detalhe = FiscalService._validar_certificado(configuracao)
        pendencias = [
            mensagem
            for mensagem in FiscalService._validar_prontidao_configuracao(configuracao)
            if mensagem
        ]

        return {
            "empresa_id": configuracao.empresa_id,
            "empresa_nome": empresa.nome_fantasia if empresa else None,
            "ambiente": getattr(configuracao.ambiente, "value", AmbienteFiscal.HOMOLOGACAO.value),
            "regime_tributario": getattr(
                configuracao.regime_tributario,
                "value",
                RegimeTributarioFiscal.SIMPLES_NACIONAL.value,
            ),
            "serie_nfce": int(configuracao.serie_nfce or 1),
            "proximo_numero_nfce": int(configuracao.proximo_numero_nfce or 1),
            "inscricao_estadual": configuracao.inscricao_estadual or "",
            "inscricao_municipal": configuracao.inscricao_municipal or "",
            "cnae": configuracao.cnae or "",
            "uf": configuracao.uf or "",
            "municipio_nome": configuracao.municipio_nome or "",
            "municipio_codigo_ibge": configuracao.municipio_codigo_ibge or "",
            "cep": configuracao.cep or "",
            "logradouro": configuracao.logradouro or "",
            "numero": configuracao.numero or "",
            "complemento": configuracao.complemento or "",
            "bairro": configuracao.bairro or "",
            "certificado_caminho": configuracao.certificado_caminho or "",
            "certificado_senha_env": configuracao.certificado_senha_env or "",
            "csc_id": configuracao.csc_id or "",
            "csc_token": configuracao.csc_token or "",
            "contingencia_ativa": bool(configuracao.contingencia_ativa),
            "certificado_ok": certificado_ok,
            "certificado_detalhe": certificado_detalhe,
            "ultimo_teste_certificado_em": TimeService.serialize_utc_iso(configuracao.ultimo_teste_certificado_em),
            "ultimo_teste_certificado_status": configuracao.ultimo_teste_certificado_status,
            "ultimo_teste_certificado_detalhe": configuracao.ultimo_teste_certificado_detalhe,
            "pendencias": pendencias,
            "pronto_para_emissao": not pendencias,
        }

    @staticmethod
    def _serializar_nota(nota):
        return {
            "id": nota.id,
            "empresa_id": nota.empresa_id,
            "empresa_nome": nota.empresa.nome_fantasia if nota.empresa else None,
            "venda_id": nota.venda_id,
            "venda_numero": nota.venda.numero_unico if nota.venda else None,
            "ambiente": getattr(nota.ambiente, "value", AmbienteFiscal.HOMOLOGACAO.value),
            "status": getattr(nota.status, "value", StatusNotaFiscal.PENDENTE.value),
            "serie": nota.serie,
            "numero": nota.numero,
            "chave_acesso": nota.chave_acesso,
            "protocolo": nota.protocolo,
            "mensagem_retorno": nota.mensagem_retorno,
            "enviado_em": TimeService.serialize_utc_iso(nota.enviado_em),
            "emitida_em": TimeService.serialize_utc_iso(nota.emitida_em),
            "cancelada_em": TimeService.serialize_utc_iso(nota.cancelada_em),
        }

    @staticmethod
    def _build_default_config(empresa_id, tenant_id):
        return ConfiguracaoFiscalEmpresa(
            tenant_id=tenant_id,
            empresa_id=empresa_id,
            ambiente=AmbienteFiscal.HOMOLOGACAO,
            regime_tributario=RegimeTributarioFiscal.SIMPLES_NACIONAL,
            serie_nfce=1,
            proximo_numero_nfce=1,
            contingencia_ativa=False,
        )

    @staticmethod
    def _validar_prontidao_configuracao(configuracao):
        pendencias = []
        for field_name, label in FiscalService.REQUIRED_CONFIG_FIELDS:
            if not getattr(configuracao, field_name, None):
                pendencias.append(f"{label} nao configurado.")

        certificado_ok, certificado_detalhe = FiscalService._validar_certificado(configuracao)
        if not certificado_ok:
            pendencias.append(certificado_detalhe)

        return pendencias

    @staticmethod
    def _atualizar_status_certificado(configuracao):
        certificado_ok, certificado_detalhe = FiscalService._validar_certificado(configuracao)
        configuracao.ultimo_teste_certificado_em = TimeService.now_utc_naive()
        configuracao.ultimo_teste_certificado_status = "VALIDO" if certificado_ok else "ERRO"
        configuracao.ultimo_teste_certificado_detalhe = certificado_detalhe

    @staticmethod
    def _validar_certificado(configuracao):
        caminho = (configuracao.certificado_caminho or "").strip()
        senha_env = (configuracao.certificado_senha_env or "").strip()

        if not caminho:
            return False, "Caminho do certificado digital nao configurado."
        if not os.path.exists(caminho):
            return False, "O arquivo do certificado digital nao foi encontrado no caminho informado."
        if not senha_env:
            return False, "Informe a variavel de ambiente que contem a senha do certificado."
        if not os.getenv(senha_env):
            return False, "A variavel de ambiente da senha do certificado nao esta carregada."

        extensao = os.path.splitext(caminho)[1].lower()
        if extensao not in {".pfx", ".p12"}:
            return False, "Utilize um certificado A1 no formato .pfx ou .p12."

        return True, "Certificado localizado e pronto para uso pelo integrador fiscal."

    @staticmethod
    def _to_ambiente(value):
        raw_value = (value or "").strip().upper()
        if not raw_value:
            return AmbienteFiscal.HOMOLOGACAO

        try:
            return AmbienteFiscal[raw_value]
        except KeyError:
            raise ValueError("Ambiente fiscal invalido.")

    @staticmethod
    def _to_regime(value):
        raw_value = (value or "").strip().upper()
        if not raw_value:
            return RegimeTributarioFiscal.SIMPLES_NACIONAL

        try:
            return RegimeTributarioFiscal[raw_value]
        except KeyError:
            raise ValueError("Regime tributario invalido.")

    @staticmethod
    def _to_positive_int(value, field_name, default=1):
        if value in (None, ""):
            return int(default)

        try:
            parsed = int(str(value).strip())
        except (TypeError, ValueError):
            raise ValueError(f"{field_name.capitalize()} invalido.")

        if parsed <= 0:
            raise ValueError(f"{field_name.capitalize()} deve ser maior que zero.")

        return parsed

    @staticmethod
    def _optional_text(value, max_length=None, uppercase=False):
        text = str(value or "").strip()
        if uppercase:
            text = text.upper()
        if max_length:
            text = text[:max_length]
        return text or None

    @staticmethod
    def _only_digits(value, max_length=None):
        digits = "".join(char for char in str(value or "") if char.isdigit())
        if max_length:
            digits = digits[:max_length]
        return digits or None

    @staticmethod
    def _to_bool(value, default=False):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "t", "sim", "yes", "on"}
