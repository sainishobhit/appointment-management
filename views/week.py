"""Week — the next 7 days, grouped by day, with blocked/college time shown."""
from __future__ import annotations

from datetime import time, timedelta

import streamlit as st

from lib import repository
from lib.config import DAY_NAMES
from lib.timeutil import today_local, combine_local, fmt_date, fmt_time, to_local
from views.common import get_settings, render_appointment_card


def _blocks_for_day(d):
    """Unavailable blocks (college/exam/leave) that apply on date d."""
    labels = []
    for b in repository.list_blocks("unavailable"):
        if b.day_of_week is not None and b.day_of_week == d.weekday():
            labels.append(b)
        elif b.day_of_week is None and b.start_date:
            end = b.end_date or b.start_date
            if b.start_date <= d <= end:
                labels.append(b)
    return labels


def render() -> None:
    settings = get_settings()
    tz = settings.timezone
    start_day = today_local(tz)

    st.header("🗓️ Week")
    st.caption(f"{fmt_date(start_day)} → {fmt_date(start_day + timedelta(days=6))}")

    for i in range(7):
        d = start_day + timedelta(days=i)
        day_start = combine_local(d, time(0, 0), tz)
        day_end = day_start + timedelta(days=1)
        appts = [a for a in repository.list_appointments(day_start, day_end)
                 if a.status != "cancelled"]

        header = f"**{DAY_NAMES[d.weekday()]} {d.strftime('%d %b')}**"
        count = f" — {len(appts)} appt(s)" if appts else " — free"
        st.markdown(header + count)

        for b in _blocks_for_day(d):
            st.caption(f"🚫 {b.label or 'Blocked'} "
                       f"({fmt_time(b.start_time)}–{fmt_time(b.end_time)})")

        for a in appts:
            render_appointment_card(a, settings)

        st.divider()
