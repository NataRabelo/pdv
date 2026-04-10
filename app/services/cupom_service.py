from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from app.models.db import Cupom, TipoDesconto
from app.repositorys.cupom_repository import CupomRepository


class CupomService:

    @staticmethod
    def listar(tenant_id):
        return [CupomService.serializar(item) for item in CupomRepository.listar(tenant_id)]

    @staticmethod
    def criar(data, tenant_id, funcionario_id=None):
        try:
            nome = (data.get("nome") or "").strip()
            codigo = (data.get("codigo") or "").strip().upper()
            data_validade = CupomService._to_date(data.get("data_validade"), obrigatoria=True)
            tipo_desconto = CupomService._to_tipo_desconto(data.get("tipo_desconto"))
            valor_desconto = CupomService._to_decimal(data.get("valor_desconto"), "valor do desconto")
            ativo = CupomService._to_bool(data.get("ativo", True))

            CupomService._validar_dados(
                nome=nome,
                codigo=codigo,
                data_validade=data_validade,
                tipo_desconto=tipo_desconto,
                valor_desconto=valor_desconto,
                tenant_id=tenant_id,
            )

            cupom = Cupom(
                tenant_id=tenant_id,
                criado_por_funcionario_id=funcionario_id,
                nome=nome,
                codigo=codigo,
                data_validade=data_validade,
                tipo_desconto=tipo_desconto,
                valor_desconto=valor_desconto,
                ativo=ativo,
            )
            CupomRepository.adicionar(cupom)
            CupomRepository.salvar()
            return CupomRepository.buscar_por_id(cupom.id, tenant_id)
        except Exception:
            CupomRepository.rollback()
            raise

    @staticmethod
    def atualizar(cupom_id, data, tenant_id):
        try:
            cupom = CupomRepository.buscar_por_id(cupom_id, tenant_id)
            if not cupom:
                raise ValueError("Cupom nao encontrado.")

            nome = (data.get("nome") or "").strip()
            codigo = (data.get("codigo") or "").strip().upper()
            data_validade = CupomService._to_date(data.get("data_validade"), obrigatoria=True)
            tipo_desconto = CupomService._to_tipo_desconto(data.get("tipo_desconto"))
            valor_desconto = CupomService._to_decimal(data.get("valor_desconto"), "valor do desconto")
            ativo = CupomService._to_bool(data.get("ativo", True))

            CupomService._validar_dados(
                nome=nome,
                codigo=codigo,
                data_validade=data_validade,
                tipo_desconto=tipo_desconto,
                valor_desconto=valor_desconto,
                tenant_id=tenant_id,
                ignorar_id=cupom.id,
            )

            cupom.nome = nome
            cupom.codigo = codigo
            cupom.data_validade = data_validade
            cupom.tipo_desconto = tipo_desconto
            cupom.valor_desconto = valor_desconto
            cupom.ativo = ativo

            CupomRepository.salvar()
            return CupomRepository.buscar_por_id(cupom.id, tenant_id)
        except Exception:
            CupomRepository.rollback()
            raise

    @staticmethod
    def deletar(cupom_id, tenant_id):
        try:
            cupom = CupomRepository.buscar_por_id(cupom_id, tenant_id)
            if not cupom:
                raise ValueError("Cupom nao encontrado.")

            CupomRepository.deletar(cupom)
            CupomRepository.salvar()
        except Exception:
            CupomRepository.rollback()
            raise

    @staticmethod
    def serializar(cupom):
        hoje = date.today()
        status = "EXPIRADO" if cupom.data_validade < hoje else "ATIVO" if cupom.ativo else "INATIVO"
        return {
            "id": cupom.id,
            "nome": cupom.nome,
            "codigo": cupom.codigo,
            "data_validade": cupom.data_validade.isoformat(),
            "tipo_desconto": cupom.tipo_desconto.value,
            "valor_desconto": str(CupomService._to_decimal_value(cupom.valor_desconto)),
            "ativo": cupom.ativo,
            "status": status,
            "criado_por_nome": cupom.criado_por.nome if cupom.criado_por else None,
        }

    @staticmethod
    def _validar_dados(nome, codigo, data_validade, tipo_desconto, valor_desconto, tenant_id, ignorar_id=None):
        if not nome:
            raise ValueError("Nome do cupom e obrigatorio.")

        if not codigo:
            raise ValueError("Codigo do cupom e obrigatorio.")

        if CupomRepository.buscar_por_codigo(codigo, tenant_id, ignorar_id=ignorar_id):
            raise ValueError("Ja existe um cupom com esse codigo.")

        if tipo_desconto == TipoDesconto.PERCENTUAL and valor_desconto > Decimal("100.00"):
            raise ValueError("O desconto percentual nao pode ser maior que 100%.")

        if data_validade < date.today():
            raise ValueError("A validade do cupom nao pode estar no passado.")

    @staticmethod
    def _to_tipo_desconto(value):
        try:
            return TipoDesconto[(value or "").strip().upper()]
        except KeyError:
            raise ValueError("Tipo de desconto invalido.")

    @staticmethod
    def _to_date(value, obrigatoria=False):
        if value in (None, ""):
            if obrigatoria:
                raise ValueError("Data de validade e obrigatoria.")
            return None

        try:
            return datetime.strptime(str(value), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Data invalida. Use o formato YYYY-MM-DD.")

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
    def _to_bool(value, default=False):
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "on", "sim", "yes"}

    @staticmethod
    def _to_decimal_value(value):
        try:
            return Decimal(str(value or 0)).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError):
            return Decimal("0.00")
