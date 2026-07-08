from datetime import date, datetime
from decimal import Decimal, InvalidOperation


class CalculoJurosMultaService:
    @staticmethod
    def calcular(valor_nominal, valor_pago, data_vencimento, data_referencia, regra):
        nominal = CalculoJurosMultaService._to_decimal(valor_nominal)
        pago = CalculoJurosMultaService._to_decimal(valor_pago)
        restante = max((nominal - pago).quantize(Decimal("0.01")), Decimal("0.00"))
        vencimento = CalculoJurosMultaService._to_date(data_vencimento)
        referencia = CalculoJurosMultaService._to_date(data_referencia)
        dias_carencia = int(getattr(regra, "dias_carencia", 0) or 0)
        dias_atraso = max(0, (referencia - vencimento).days - dias_carencia)

        if dias_atraso <= 0 or restante <= Decimal("0.00"):
            return {
                "valor_restante": restante,
                "dias_em_atraso": dias_atraso,
                "juros_calculado": Decimal("0.00"),
                "multa_calculada": Decimal("0.00"),
                "valor_atualizado": restante,
                "teto_aplicado": False,
            }

        base_calculo = getattr(getattr(regra, "base_calculo", None), "value", getattr(regra, "base_calculo", "valor_restante"))
        valor_base = nominal if base_calculo == "valor_nominal" else restante

        tipo_multa = getattr(getattr(regra, "tipo_multa", None), "value", getattr(regra, "tipo_multa", "nenhum"))
        if tipo_multa == "percentual":
            multa = (valor_base * (CalculoJurosMultaService._to_decimal(getattr(regra, "percentual_multa", 0)) / Decimal("100"))).quantize(Decimal("0.01"))
        elif tipo_multa == "fixo":
            multa = CalculoJurosMultaService._to_decimal(getattr(regra, "valor_fixo_multa", 0))
        else:
            multa = Decimal("0.00")

        tipo_juros = getattr(getattr(regra, "tipo_juros", None), "value", getattr(regra, "tipo_juros", "nenhum"))
        percentual_juros = CalculoJurosMultaService._to_decimal(getattr(regra, "percentual_juros", 0))
        if tipo_juros == "diario":
            juros = (valor_base * (percentual_juros / Decimal("100")) * Decimal(dias_atraso)).quantize(Decimal("0.01"))
        elif tipo_juros == "mensal":
            juros = (valor_base * (percentual_juros / Decimal("100")) * (Decimal(dias_atraso) / Decimal("30"))).quantize(Decimal("0.01"))
        else:
            juros = Decimal("0.00")

        valor_atualizado = (restante + juros + multa).quantize(Decimal("0.01"))
        teto = (nominal * (Decimal("1") + (CalculoJurosMultaService._to_decimal(getattr(regra, "percentual_maximo_teto", 0)) / Decimal("100")))).quantize(Decimal("0.01"))
        teto_aplicado = False
        if valor_atualizado > teto:
            valor_atualizado = teto
            teto_aplicado = True

        return {
            "valor_restante": restante,
            "dias_em_atraso": dias_atraso,
            "juros_calculado": juros,
            "multa_calculada": multa,
            "valor_atualizado": valor_atualizado,
            "teto_aplicado": teto_aplicado,
        }

    @staticmethod
    def _to_decimal(value):
        try:
            return Decimal(str(value or 0).replace(",", ".")).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError):
            return Decimal("0.00")

    @staticmethod
    def _to_date(value):
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        return datetime.strptime(str(value), "%Y-%m-%d").date()
