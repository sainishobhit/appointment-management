"""Today — the home screen. Today's appointments with quick actions."""
from __future__ import annotations

from datetime import time, timedelta

import streamlit as st

from lib import repository
from lib.timeutil import today_local, combine_local, fmt_date, fmt_time, to_local
from views.common import get_settings, render_appointment_card, whatsapp_button


def render() -> None:
    settings = get_settings()
    tz = settings.timezone
    today = today_local(tz)

    st.header(f"📅 Today")
    st.caption(fmt_date(today))

    start = combine_local(today, time(0, 0), tz)
    end = start + timedelta(days=1)
    appts = repository.list_appointments(start, end)

    active = [a for a in appts if a.status != "cancelled"]
    cancelled = [a for a in appts if a.status == "cancelled"]

    if not active:
        st.info("No appointments today. Enjoy the breather. ☕")
    else:
        done = sum(1 for a in active if a.status == "completed")
        st.caption(f"{len(active)} appointment(s) · {done} completed")
        for a in active:
            render_appointment_card(a, settings)

    if cancelled:
        with st.expander(f"Cancelled today ({len(cancelled)})"):
            for a in cancelled:
                st.markdown(f"~~{fmt_time(to_local(a.start_ts, tz))} · {a.procedure} · "
                            f"{a.patient_name}~~")
                whatsapp_button("💬 Send cancellation notice", a, settings,
                                "cancellation", key=f"wacx-{a.id}")
