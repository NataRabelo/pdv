from datetime import date
from decimal import Decimal

from app.models.db import BaseCalculoJurosMulta, TipoJurosBoleto, TipoMultaBoleto
from app.services.boleto_service import BoletoService


def test_calcular_juros_multa_aplica_regra_basica():
    regra = {
        "tipo_multa": TipoMultaBoleto.percentual,
        "percentual_multa": Decimal("2"),
        "tipo_juros": TipoJurosBoleto.diario,
        "percentual_juros": Decimal("1"),
        "dias_carencia": 0,
        "base_calculo": BaseCalculoJurosMulta.valor_restante,
    }

    resultado = BoletoService.calcular_juros_multa(
        valor_nominal=Decimal("100.00"),
        valor_pago=Decimal("0.00"),
        data_vencimento=date(2024, 1, 1),
        data_referencia=date(2024, 1, 3),
        regra=regra,
    )

    assert resultado["multa"] == Decimal("2.00")
    assert resultado["juros"] == Decimal("2.00")
    assert resultado["total"] == Decimal("4.00")
