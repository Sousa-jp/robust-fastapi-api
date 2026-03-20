from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .settings import settings


def app_timezone() -> ZoneInfo:
    try:
        return ZoneInfo(settings.app.timezone)
    except (TypeError, ZoneInfoNotFoundError):
        return ZoneInfo("UTC")


def now() -> datetime:
    return datetime.now(tz=app_timezone())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
