"""Timezone helpers. The clinic runs in a single timezone, so we keep all
in-app logic in local time and only normalise at the storage boundary."""
from __future__ import annotations

from datetime import datetime, date, time
from zoneinfo import ZoneInfo

DEFAULT_TZ = "Asia/Kolkata"


def get_tz(name: str | None = None) -> ZoneInfo:
    return ZoneInfo(name or DEFAULT_TZ)


def now_local(tz_name: str | None = None) -> datetime:
    return datetime.now(get_tz(tz_name))


def today_local(tz_name: str | None = None) -> date:
    return now_local(tz_name).date()


def to_local(dt: datetime | None, tz_name: str | None = None) -> datetime | None:
    """Return an aware datetime in the clinic timezone.

    Naive datetimes (e.g. from SQLite) are assumed to already be local.
    """
    if dt is None:
        return None
    tz = get_tz(tz_name)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt.astimezone(tz)


def to_naive_local(dt: datetime | None, tz_name: str | None = None) -> datetime | None:
    """Aware -> naive local wall-clock datetime (used by the scheduler)."""
    loc = to_local(dt, tz_name)
    return loc.replace(tzinfo=None) if loc else None


def combine_local(d: date, t: time, tz_name: str | None = None) -> datetime:
    """Build an aware local datetime from a date + time (for storage)."""
    return datetime.combine(d, t).replace(tzinfo=get_tz(tz_name))


def fmt_date(dt: datetime | date) -> str:
    if isinstance(dt, datetime):
        dt = dt.date()
    return dt.strftime("%a %d %b %Y")


def fmt_time(dt: datetime | time) -> str:
    if isinstance(dt, datetime):
        dt = dt.time()
    return dt.strftime("%I:%M %p").lstrip("0")
