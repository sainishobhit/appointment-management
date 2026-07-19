from datetime import date, datetime, time, timedelta

from lib.scheduler import Session, Block, Busy, suggest_slots, has_conflict, time_of_day

# Clinic open every day 17:00-20:00 keeps tests independent of weekday.
ALL_DAYS = [Session(day_of_week=d, start=time(17, 0), end=time(20, 0)) for d in range(7)]
FROM = date(2026, 7, 20)
MIDNIGHT = datetime(2026, 7, 20, 0, 0)


def _suggest(**kw):
    base = dict(duration_min=30, buffer_min=10, daily_cap=8, sessions=ALL_DAYS,
                blocks=[], busy=[], from_date=FROM, not_before=MIDNIGHT, n=3)
    base.update(kw)
    return suggest_slots(**base)


def test_suggests_inside_session():
    slots = _suggest()
    assert slots, "expected at least one slot"
    first = slots[0]
    assert first.start.date() == FROM
    assert first.start.time() == time(17, 0)


def test_respects_blocks():
    # Block the whole first-day session; earliest slot must move to the next day.
    block = Block(start=time(17, 0), end=time(20, 0), day_of_week=FROM.weekday())
    slots = _suggest(blocks=[block])
    assert all(s.start.date() != FROM for s in slots)


def test_clusters_onto_busy_day():
    # A day that already has an appointment should be preferred over empty days.
    busy_day = FROM + timedelta(days=2)
    busy = [Busy(start=datetime.combine(busy_day, time(17, 0)), duration_min=30)]
    slots = _suggest(busy=busy)
    assert slots[0].start.date() == busy_day


def test_no_overlap_with_buffer():
    busy = [Busy(start=datetime.combine(FROM, time(17, 0)), duration_min=30)]
    slots = _suggest(busy=busy)
    same_day = [s for s in slots if s.start.date() == FROM]
    # earliest valid start on the busy day respects the 10-min buffer (>= 17:40)
    assert same_day and same_day[0].start.time() >= time(17, 40)


def test_followup_centers_on_interval():
    slots = _suggest(target_interval_days=7)
    assert slots[0].start.date() == FROM + timedelta(days=7)


def test_daily_cap_skips_full_day():
    full = [Busy(start=datetime.combine(FROM, time(17, 0)) + timedelta(minutes=15 * i),
                 duration_min=5) for i in range(8)]
    slots = _suggest(busy=full, daily_cap=8)
    assert all(s.start.date() != FROM for s in slots)


def test_has_conflict():
    busy = [Busy(start=datetime.combine(FROM, time(17, 0)), duration_min=30)]
    assert has_conflict(datetime.combine(FROM, time(17, 20)), 15, busy)
    assert not has_conflict(datetime.combine(FROM, time(19, 0)), 30, busy, buffer_min=10)


def test_time_of_day():
    assert time_of_day(time(9, 0)) == "morning"
    assert time_of_day(time(14, 0)) == "afternoon"
    assert time_of_day(time(18, 0)) == "evening"
