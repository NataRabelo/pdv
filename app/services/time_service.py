from datetime import datetime, timezone
from zoneinfo import ZoneInfo


class TimeService:
    """
    Regras do sistema:
    - Persistencia em UTC
    - Serializacao para API com offset explicito
    - Conversao para horario local apenas na exibicao
    """

    TZ_UTC = timezone.utc
    TZ_BR = ZoneInfo("America/Sao_Paulo")

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(TimeService.TZ_UTC)

    @staticmethod
    def now_utc_naive() -> datetime:
        return TimeService.now_utc().replace(tzinfo=None)

    @staticmethod
    def today_br():
        return TimeService.now_utc().astimezone(TimeService.TZ_BR).date()

    @staticmethod
    def local_date_start_to_utc_naive(local_date):
        local_dt = datetime.combine(local_date, datetime.min.time(), tzinfo=TimeService.TZ_BR)
        return local_dt.astimezone(TimeService.TZ_UTC).replace(tzinfo=None)

    @staticmethod
    def to_utc(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None

        if dt.tzinfo is None:
            return dt.replace(tzinfo=TimeService.TZ_UTC)

        return dt.astimezone(TimeService.TZ_UTC)

    @staticmethod
    def to_brasilia(dt: datetime | None) -> datetime | None:
        dt_utc = TimeService.to_utc(dt)
        if dt_utc is None:
            return None
        return dt_utc.astimezone(TimeService.TZ_BR)

    @staticmethod
    def serialize_utc_iso(dt: datetime | None) -> str | None:
        dt_utc = TimeService.to_utc(dt)
        if dt_utc is None:
            return None
        return dt_utc.isoformat()

    @staticmethod
    def format_br(dt: datetime | None, fmt: str = "%d/%m/%Y %H:%M") -> str:
        if dt is None:
            return ""

        dt_br = TimeService.to_brasilia(dt)
        return dt_br.strftime(fmt) if dt_br else ""
