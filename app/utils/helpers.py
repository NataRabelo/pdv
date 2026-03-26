def parse_float(value):
    if not value:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    value = value.replace("R$", "").strip()
    value = value.replace(".", "")
    value = value.replace(",", ".")

    try:
        return float(value)
    except ValueError:
        raise ValueError("Valor monetário inválido.")
    

def _to_int_or_none(value):
    return int(value) if value not in (None, "", "null") else None