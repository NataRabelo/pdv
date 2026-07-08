import calendar
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation


class ParcelamentoService:
    @staticmethod
    def gerar_parcelas(valor_total, configuracao_parcelamento, numero_parcelas, data_base, intervalo_customizado=None):
        total = ParcelamentoService._to_decimal(valor_total, "valor total")
        qtd = ParcelamentoService._to_int(numero_parcelas, "numero de parcelas")
        data_base_obj = ParcelamentoService._to_date(data_base)

        minimo = int(configuracao_parcelamento.numero_min_parcelas or 1)
        maximo = int(configuracao_parcelamento.numero_max_parcelas or 1)
        if qtd < minimo or qtd > maximo:
            raise ValueError(f"Numero de parcelas deve ficar entre {minimo} e {maximo}.")

        intervalo = int(configuracao_parcelamento.intervalo_dias_padrao or 30)
        if intervalo_customizado not in (None, ""):
            if not configuracao_parcelamento.permite_intervalo_customizado:
                raise ValueError("Intervalo customizado nao permitido para esta configuracao.")
            intervalo = ParcelamentoService._to_int(intervalo_customizado, "intervalo customizado")
        if intervalo < 1:
            raise ValueError("Intervalo entre parcelas deve ser maior que zero.")

        valor_minimo = ParcelamentoService._to_decimal(configuracao_parcelamento.valor_minimo_por_parcela, "valor minimo por parcela")
        valor_base = (total / Decimal(qtd)).quantize(Decimal("0.01"))
        parcelas = []
        soma = Decimal("0.00")
        vencimento_anterior = data_base_obj

        for numero in range(1, qtd + 1):
            if numero == qtd:
                valor_parcela = (total - soma).quantize(Decimal("0.01"))
            else:
                valor_parcela = valor_base
                soma += valor_parcela

            if valor_parcela < valor_minimo:
                raise ValueError("Valor da parcela abaixo do minimo; reduza o numero de parcelas.")

            vencimento = ParcelamentoService._proximo_vencimento(configuracao_parcelamento, vencimento_anterior, intervalo)
            vencimento_anterior = vencimento
            parcelas.append({
                "numero_parcela": numero,
                "valor_parcela": valor_parcela,
                "data_vencimento": vencimento,
            })

        return parcelas

    @staticmethod
    def _proximo_vencimento(configuracao, data_anterior, intervalo):
        dia_fixo = configuracao.dia_fixo_vencimento
        if not dia_fixo:
            return data_anterior + timedelta(days=intervalo)

        mes = data_anterior.month + 1
        ano = data_anterior.year
        if mes > 12:
            mes = 1
            ano += 1
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        return date(ano, mes, min(int(dia_fixo), ultimo_dia))

    @staticmethod
    def _to_decimal(value, field_name):
        try:
            valor = Decimal(str(value).replace(",", "."))
        except (InvalidOperation, ValueError):
            raise ValueError(f"Valor invalido para {field_name}.")
        if valor <= 0:
            raise ValueError(f"{field_name.capitalize()} deve ser maior que zero.")
        return valor.quantize(Decimal("0.01"))

    @staticmethod
    def _to_int(value, field_name):
        try:
            valor = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name.capitalize()} invalido.")
        return valor

    @staticmethod
    def _to_date(value):
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        try:
            return datetime.strptime(str(value), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Data invalida. Use o formato YYYY-MM-DD.")
