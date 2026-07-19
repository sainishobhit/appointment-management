"""Pure scheduling logic — no Streamlit, no DB. Implements brief §7.

All datetimes here are *naive local wall-clock* (the clinic's timezone). The
view layer converts to/from aware datetimes at the storage boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, time, timedelta

from .models import Slot


@dataclass
class Session:
    day_of_week: int      # Monday=0..Sunday=6
    start: time
    end: time


@dataclass
class Block:
    """An unavailable interval — recurring (day_of_week) or dated (start/end date)."""
    start: time
    end: time
    day_of_week: int | None = None
    start_date: date | None = None
    end_date: date | None = None


@dataclass
class Busy:
    start: datetime       # naive local
    duration_min: int

    @property
    def end(self) -> datetime:
        return self.start + timedelta(minutes=self.duration_min)


# --- time-of-day helpers -----------------------------------------------------

def time_of_day(t: time) -> str:
    if t.hour < 12:
        return "morning"
    if t.hour < 16:
        return "afternoon"
    return "evening"


def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def _sessions_for(sessions: list[Session], d: date) -> list[Session]:
    return [s for s in sessions if s.day_of_week == d.weekday()]


def _blocks_for(blocks: list[Block], d: date) -> list[tuple[time, time]]:
    out: list[tuple[time, time]] = []
    for b in blocks:
        if b.day_of_week is not None:
            if b.day_of_week == d.weekday():
                out.append((b.start, b.end))
        else:
            sd = b.start_date
            ed = b.end_date or sd
            if sd and sd <= d <= ed:
                out.append((b.start, b.end))
    return out


def has_conflict(start: datetime, duration_min: int, busy: list[Busy],
                 buffer_min: int = 0) -> bool:
    """True if [start, start+duration] collides with any busy interval,
    keeping at least `buffer_min` gap on each side."""
    end = start + timedelta(minutes=duration_min)
    for b in busy:
        if _overlaps(start, end,
                     b.start - timedelta(minutes=buffer_min),
                     b.end + timedelta(minutes=buffer_min)):
            return True
    return False


def _candidate_on_day(
    d: date,
    duration_min: int,
    buffer_min: int,
    sessions: list[Session],
    blocks: list[Block],
    busy: list[Busy],
    not_before: datetime,
    step_min: int,
    preferred_tod: str | None,
) -> datetime | None:
    """Earliest valid start on day `d`, preferring the patient's usual
    time-of-day when one is supplied (falling back to any valid time)."""
    day_sessions = _sessions_for(sessions, d)
    if not day_sessions:
        return None
    day_blocks = _blocks_for(blocks, d)

    preferred: list[datetime] = []
    fallback: list[datetime] = []
    for s in sorted(day_sessions, key=lambda x: x.start):
        cur = datetime.combine(d, s.start)
        session_end = datetime.combine(d, s.end)
        while cur + timedelta(minutes=duration_min) <= session_end:
            if cur >= not_before:
                blocked = any(
                    _overlaps(cur, cur + timedelta(minutes=duration_min),
                              datetime.combine(d, bs), datetime.combine(d, be))
                    for bs, be in day_blocks
                )
                if not blocked and not has_conflict(cur, duration_min, busy, buffer_min):
                    if preferred_tod and time_of_day(cur.time()) == preferred_tod:
                        preferred.append(cur)
                    else:
                        fallback.append(cur)
            cur += timedelta(minutes=step_min)
    pool = preferred or fallback
    return min(pool) if pool else None


def suggest_slots(
    *,
    duration_min: int,
    buffer_min: int,
    daily_cap: int,
    sessions: list[Session],
    blocks: list[Block],
    busy: list[Busy],
    from_date: date,
    not_before: datetime,
    horizon_days: int = 21,
    target_interval_days: int | None = None,
    patient_usual_tod: str | None = None,
    n: int = 3,
    step_min: int = 15,
) -> list[Slot]:
    """Return up to `n` recommended slots, one per day, ranked per brief §7:

    1/2. inside a clinic session, outside blocked time, fits duration+buffer;
    3.   cluster onto days that already have appointments;
    4.   for follow-ups, center on the target interval;
    5.   prefer the patient's usual time-of-day;
    6.   respect the daily cap; 7. earliest wins ties.
    """
    horizon = horizon_days
    target_date = None
    if target_interval_days is not None:
        target_date = from_date + timedelta(days=target_interval_days)
        horizon = max(horizon, target_interval_days + 10)

    ranked: list[tuple[tuple, Slot]] = []
    for offset in range(0, horizon + 1):
        d = from_date + timedelta(days=offset)
        day_busy = [b for b in busy if b.start.date() == d]
        if len(day_busy) >= daily_cap:
            continue
        cand = _candidate_on_day(
            d, duration_min, buffer_min, sessions, blocks, busy,
            not_before, step_min, patient_usual_tod,
        )
        if cand is None:
            continue
        day_has_appts = len(day_busy) > 0
        key = (
            abs((d - target_date).days) if target_date else 0,   # follow-up proximity
            0 if day_has_appts else 1,                           # prefer busy days
            offset,                                              # earlier better
            cand.hour * 60 + cand.minute,                        # earlier in day
        )
        ranked.append((key, Slot(start=cand, duration_min=duration_min)))

    ranked.sort(key=lambda x: x[0])
    return [slot for _, slot in ranked[:n]]
