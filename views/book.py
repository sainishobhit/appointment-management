"""Book — create, reschedule, or set a follow-up appointment, with Smart Slot
Suggestions (brief §7). Mode is carried in session_state and set by the cards
on Today/Week."""
from __future__ import annotations

from datetime import time, timedelta

import streamlit as st

from lib import repository
from lib.scheduler import suggest_slots, has_conflict, Busy
from lib.timeutil import (now_local, today_local, to_naive_local, combine_local,
                          fmt_date, fmt_time, to_local)
from views.common import (get_settings, build_scheduler_inputs, patient_usual_tod,
                          patient_label, whatsapp_button)


def render() -> None:
    settings = get_settings()
    _show_last_result(settings)

    mode = st.session_state.get("book_mode", "new")
    if mode == "reschedule":
        _render_reschedule(settings)
    else:
        _render_new_or_followup(settings, mode)


# --- post-save confirmation --------------------------------------------------

def _show_last_result(settings) -> None:
    res = st.session_state.get("booked_result")
    if not res:
        return
    appt = repository.get_appointment(res["appt_id"])
    if appt:
        tz = settings.timezone
        st.success(f"Saved — {appt.patient_name} · {fmt_date(to_local(appt.start_ts, tz))} "
                   f"at {fmt_time(to_local(appt.start_ts, tz))} · {appt.procedure}")
        whatsapp_button("💬 Send WhatsApp message", appt, settings, res["template"],
                        key="wa-result")
    if st.button("➕ Book another"):
        for k in ("booked_result", "book_mode", "book_patient_id",
                  "followup_patient_id", "followup_procedure", "reschedule_appt_id"):
            st.session_state.pop(k, None)
        st.rerun()
    st.divider()


# --- reschedule --------------------------------------------------------------

def _render_reschedule(settings) -> None:
    aid = st.session_state.get("reschedule_appt_id")
    appt = repository.get_appointment(aid) if aid else None
    if not appt:
        st.warning("No appointment selected to reschedule.")
        return
    tz = settings.timezone
    st.header("🔁 Reschedule")
    st.info(f"Currently: **{appt.patient_name}** · {appt.procedure} · "
            f"{fmt_date(to_local(appt.start_ts, tz))} at {fmt_time(to_local(appt.start_ts, tz))}")

    sessions, blocks, busy = build_scheduler_inputs(settings, exclude_appt_id=appt.id)
    _slot_picker(settings, sessions, blocks, busy, appt.duration_min,
                 procedure=appt.procedure, patient_id=appt.patient_id,
                 on_pick=lambda start: _do_reschedule(appt.id, start, settings))


def _do_reschedule(aid, start_aware, settings) -> None:
    repository.update_appointment(aid, start_ts=start_aware, status="scheduled",
                                  reminder_sent=False)
    st.session_state["booked_result"] = {"appt_id": aid, "template": "reschedule"}
    for k in ("book_mode", "reschedule_appt_id"):
        st.session_state.pop(k, None)
    st.rerun()


# --- new / follow-up ---------------------------------------------------------

def _render_new_or_followup(settings, mode) -> None:
    st.header("➕ Book appointment" if mode == "new" else "➕ Book follow-up")
    if mode == "followup":
        st.caption("Follow-up booking — patient and procedure pre-filled.")

    patient_id = _patient_picker(settings, mode)
    if not patient_id:
        return

    # Procedure + duration
    proc_names = [p["name"] for p in settings.procedures]
    durations = {p["name"]: p["duration_min"] for p in settings.procedures}
    pre_proc = st.session_state.get("followup_procedure") if mode == "followup" else None
    idx = proc_names.index(pre_proc) if pre_proc in proc_names else 0
    procedure = st.selectbox("Procedure", proc_names, index=idx)
    duration = st.number_input("Duration (minutes)", 5, 240,
                               value=int(durations.get(procedure, 30)), step=5)

    interval = None
    if mode == "followup":
        interval = st.number_input("Follow-up in (days)", 1, 180, value=7)

    sessions, blocks, busy = build_scheduler_inputs(settings)
    followup_of = None
    template = "followup" if mode == "followup" else "confirmation"
    _slot_picker(settings, sessions, blocks, busy, int(duration),
                 procedure=procedure, patient_id=patient_id,
                 target_interval_days=int(interval) if interval else None,
                 on_pick=lambda start: _do_create(patient_id, start, int(duration),
                                                   procedure, template, followup_of, settings))


def _do_create(patient_id, start_aware, duration, procedure, template,
               followup_of, settings) -> None:
    aid = repository.create_appointment(patient_id, start_aware, duration, procedure,
                                        follow_up_of=followup_of)
    st.session_state["booked_result"] = {"appt_id": aid, "template": template}
    for k in ("book_mode", "book_patient_id", "followup_patient_id",
              "followup_procedure"):
        st.session_state.pop(k, None)
    st.rerun()


# --- shared widgets ----------------------------------------------------------

def _patient_picker(settings, mode) -> int | None:
    patients = repository.list_patients()
    id_to_label = {p.id: patient_label(p) for p in patients}
    ids = list(id_to_label.keys())
    labels = list(id_to_label.values())
    ADD_NEW = "➕ Add new patient"
    options = [ADD_NEW] + labels

    pre_id = st.session_state.get("book_patient_id")
    if pre_id is None and mode == "followup":
        pre_id = st.session_state.get("followup_patient_id")
    default_index = 1 + ids.index(pre_id) if pre_id in ids else (1 if labels else 0)

    sel = st.selectbox("Patient", options, index=default_index)
    if sel == ADD_NEW:
        return _add_patient_form()
    pid = ids[options.index(sel) - 1]
    st.session_state["book_patient_id"] = pid
    return pid


def _add_patient_form() -> int | None:
    with st.form("new_patient"):
        name = st.text_input("Name")
        phone = st.text_input("Phone (with country code, e.g. +91 98xxxxxxxx)")
        c = st.columns(2)
        age = c[0].number_input("Age", 0, 120, value=0)
        sex = c[1].selectbox("Sex", ["", "Female", "Male", "Other"])
        submitted = st.form_submit_button("Add patient")
    if submitted:
        if not name.strip() or not phone.strip():
            st.error("Name and phone are required.")
            return None
        existing = repository.find_patient_by_phone(phone)
        if existing:
            st.warning(f"A patient with this phone already exists: {existing.name}.")
            pid = existing.id
        else:
            pid = repository.create_patient(name, phone, age=age or None,
                                            sex=sex or None)
        st.session_state["book_patient_id"] = pid
        st.rerun()
    return None


def _slot_picker(settings, sessions, blocks, busy, duration, *, procedure,
                 patient_id, on_pick, target_interval_days=None) -> None:
    tz = settings.timezone
    now = now_local(tz)
    not_before = to_naive_local(now, tz)
    tod = patient_usual_tod(patient_id, settings)

    slots = suggest_slots(
        duration_min=duration, buffer_min=settings.buffer_min,
        daily_cap=settings.daily_cap, sessions=sessions, blocks=blocks, busy=busy,
        from_date=today_local(tz), not_before=not_before,
        target_interval_days=target_interval_days, patient_usual_tod=tod, n=3,
    )

    st.subheader("Suggested slots")
    if not slots:
        st.warning("No open slots found in the next few weeks. Check your clinic "
                   "sessions in Availability, or pick a time manually below.")
    else:
        cols = st.columns(len(slots))
        for i, s in enumerate(slots):
            label = f"{fmt_date(s.start)}\n{fmt_time(s.start)}"
            if cols[i].button(label, key=f"slot-{i}", use_container_width=True):
                on_pick(combine_local(s.start.date(), s.start.time(), tz))

    with st.expander("Pick a different time"):
        d = st.date_input("Date", value=today_local(tz), min_value=today_local(tz))
        t = st.time_input("Time", value=time(18, 0), step=timedelta(minutes=15))
        if st.button("Book this time", key="manual-book"):
            start_naive = combine_local(d, t, tz).replace(tzinfo=None)
            if start_naive < not_before:
                st.error("That time is in the past.")
            elif has_conflict(start_naive, duration, busy, settings.buffer_min):
                st.error("That time clashes with another appointment (incl. buffer).")
            else:
                on_pick(combine_local(d, t, tz))
