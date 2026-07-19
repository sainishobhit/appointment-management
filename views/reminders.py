"""Reminders — tomorrow's patients to remind, and recalls due."""
from __future__ import annotations

from datetime import time, timedelta

import streamlit as st

from lib import repository
from lib.config import ACTIVE_STATUSES
from lib.timeutil import today_local, combine_local, fmt_date, fmt_time, to_local
from lib.whatsapp import build_link, render_message
from views.common import get_settings, whatsapp_button, go


def render() -> None:
    settings = get_settings()
    tz = settings.timezone
    st.header("🔔 Reminders")

    tomorrow = today_local(tz) + timedelta(days=1)
    start = combine_local(tomorrow, time(0, 0), tz)
    end = start + timedelta(days=1)
    appts = repository.list_appointments(start, end, statuses=ACTIVE_STATUSES)

    st.subheader(f"Remind tomorrow — {fmt_date(tomorrow)}")
    if not appts:
        st.info("No appointments tomorrow.")
    for a in appts:
        with st.container(border=True):
            mark = " ✅" if a.reminder_sent else ""
            st.markdown(f"**{fmt_time(to_local(a.start_ts, tz))}** · {a.procedure} · "
                        f"{a.patient_name}{mark}")
            c = st.columns(2)
            with c[0]:
                whatsapp_button("💬 Send reminder", a, settings, "reminder",
                                key=f"rem-{a.id}")
            if c[1].button("Mark reminded", key=f"mk-{a.id}"):
                repository.update_appointment(a.id, reminder_sent=True)
                st.rerun()

    st.divider()
    st.subheader("Recalls due")
    due = repository.patients_recall_due(today_local(tz))
    if not due:
        st.info("No recalls due. 🎉")
    for p in due:
        with st.container(border=True):
            st.markdown(f"**{p.name}** · {p.phone} — due {fmt_date(p.recall_due)}")
            text = render_message(settings.templates.get("recall", ""),
                                  name=p.name, when="", procedure="check-up")
            c = st.columns(2)
            c[0].link_button("💬 Send recall invite", build_link(p.phone, text),
                             use_container_width=True)
            if c[1].button("Book now", key=f"rc-{p.id}", use_container_width=True):
                go("Book", book_mode="new", book_patient_id=p.id)
                st.rerun()
