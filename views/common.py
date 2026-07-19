"""Helpers shared across screens."""
from __future__ import annotations

from datetime import timedelta

import streamlit as st

from lib import repository, scheduler
from lib.config import STATUS_LABELS
from lib.models import Settings
from lib.timeutil import to_naive_local, now_local, fmt_time, to_local
from lib.whatsapp import build_link, render_message

_STATUS_EMOJI = {
    "scheduled": "🕒", "confirmed": "✅", "completed": "☑️",
    "no_show": "🚫", "cancelled": "❌",
}


def get_settings() -> Settings:
    return repository.get_settings()


def status_badge(status: str) -> str:
    return f"{_STATUS_EMOJI.get(status, '•')} {STATUS_LABELS.get(status, status)}"


def patient_label(p) -> str:
    return f"{p.name} · {p.phone}"


def build_scheduler_inputs(settings: Settings, exclude_appt_id: int | None = None):
    """Return (sessions, blocks, busy) for the recommender, in naive local time."""
    sessions = [
        scheduler.Session(day_of_week=b.day_of_week, start=b.start_time, end=b.end_time)
        for b in repository.list_blocks("clinic_session") if b.day_of_week is not None
    ]
    blocks = [
        scheduler.Block(start=b.start_time, end=b.end_time, day_of_week=b.day_of_week,
                        start_date=b.start_date, end_date=b.end_date)
        for b in repository.list_blocks("unavailable")
    ]
    window_start = now_local(settings.timezone) - timedelta(days=1)
    window_end = now_local(settings.timezone) + timedelta(days=90)
    busy = [
        scheduler.Busy(start=to_naive_local(a.start_ts, settings.timezone),
                       duration_min=a.duration_min)
        for a in repository.active_between(window_start, window_end)
        if a.id != exclude_appt_id
    ]
    return sessions, blocks, busy


def patient_usual_tod(patient_id: int, settings: Settings) -> str | None:
    """Most common time-of-day from a patient's past appointments, if any."""
    counts: dict[str, int] = {}
    for a in repository.appointments_for_patient(patient_id):
        local = to_local(a.start_ts, settings.timezone)
        if local:
            tod = scheduler.time_of_day(local.time())
            counts[tod] = counts.get(tod, 0) + 1
    return max(counts, key=counts.get) if counts else None


def whatsapp_button(label: str, appt, settings: Settings, template_key: str, key: str):
    """Render a wa.me link button pre-filled from a template for an appointment."""
    tmpl = settings.templates.get(template_key, "")
    text = render_message(
        tmpl, name=appt.patient_name or "there",
        when=to_local(appt.start_ts, settings.timezone), procedure=appt.procedure,
    )
    st.link_button(label, build_link(appt.patient_phone or "", text),
                   use_container_width=True)


def go(page_key: str, **state):
    """Store navigation intent then switch pages via session_state flags."""
    for k, v in state.items():
        st.session_state[k] = v
    st.session_state["_goto"] = page_key


def render_appointment_card(a, settings: Settings) -> None:
    """A single appointment with status-appropriate actions. Shared by Today/Week."""
    tz = settings.timezone
    with st.container(border=True):
        top = st.columns([3, 2])
        top[0].markdown(f"**{fmt_time(to_local(a.start_ts, tz))}** · {a.procedure}")
        top[0].caption(f"{a.patient_name} · {a.patient_phone}")
        top[1].markdown(status_badge(a.status))

        acts = []
        if a.status == "scheduled":
            acts.append(("Confirm", lambda: repository.set_status(a.id, "confirmed")))
        if a.status in ("scheduled", "confirmed"):
            acts += [
                ("Complete", lambda: repository.set_status(a.id, "completed")),
                ("No-show", lambda: repository.set_status(a.id, "no_show")),
                ("Reschedule", lambda: go("Book", book_mode="reschedule",
                                          reschedule_appt_id=a.id)),
                ("Cancel", lambda: repository.set_status(a.id, "cancelled")),
            ]
        if a.status == "completed":
            acts.append(("Follow-up", lambda: go("Book", book_mode="followup",
                                                 followup_patient_id=a.patient_id,
                                                 followup_procedure=a.procedure)))
        if a.status == "no_show":
            acts.append(("Reschedule", lambda: go("Book", book_mode="reschedule",
                                                  reschedule_appt_id=a.id)))
        if acts:
            cols = st.columns(len(acts))
            for i, (label, cb) in enumerate(acts):
                if cols[i].button(label, key=f"act-{label}-{a.id}",
                                  use_container_width=True):
                    cb()
                    st.rerun()

        if a.status in ("scheduled", "confirmed"):
            whatsapp_button("💬 Send WhatsApp reminder", a, settings, "reminder",
                            key=f"wa-{a.id}")
