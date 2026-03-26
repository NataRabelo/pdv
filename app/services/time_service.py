from datetime import datetime, timezone
from zoneinfo import ZoneInfo


class TimeService:
    """
    Serviço centralizado para manipulação de datas e horários.
    Regra: tudo entra e sai em UTC.
    Conversão para fuso local apenas na exibição.
    """

    TZ_UTC = timezone.utc
    TZ_BR = ZoneInfo("America/Sao_Paulo")

    @staticmethod
    def now_utc() -> datetime:
        """Retorna datetime atual em UTC (aware)."""
        return datetime.now(TimeService.TZ_UTC)

    @staticmethod
    def to_utc(dt: datetime) -> datetime:
        """
        Garante que um datetime esteja em UTC.
        - Se naive, assume que já está em UTC
        - Se aware, converte para UTC
        """
        if dt.tzinfo is None:
            return dt.replace(tzinfo=TimeService.TZ_UTC)
        return dt.astimezone(TimeService.TZ_UTC)

    @staticmethod
    def to_brasilia(dt: datetime) -> datetime:
        """
        Converte datetime (UTC ou naive) para horário de Brasília.
        """
        dt_utc = TimeService.to_utc(dt)
        return dt_utc.astimezone(TimeService.TZ_BR)

    @staticmethod
    def format_br(dt: datetime, fmt: str = "%d/%m/%Y %H:%M") -> str:
        """
        Formata datetime no padrão brasileiro.
        """
        if dt is None:
            return ""
        return TimeService.to_brasilia(dt).strftime(fmt)