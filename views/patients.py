"""Patients — search, add, edit, and view a patient's appointment history."""
from __future__ import annotations

from datetime import timedelta

import streamlit as st

from lib import repository
from lib.config import RECALL_MONTHS, STATUS_LABELS
from lib.timeutil import today_local, fmt_date, fmt_time, to_local
from views.common import get_settings, patient_label, go


def render() -> None:
    settings = get_settings()
    st.header("👤 Patients")

    with st.expander("➕ Add new patient"):
        _add_form()

    q = st.text_input("Search by name or phone")
    results = repository.search_patients(q)
    st.caption(f"{len(results)} patient(s)")

    for p in results:
        if st.button(patient_label(p), key=f"pt-{p.id}", use_container_width=True):
            st.session_state["sel_patient"] = p.id
            st.rerun()

    sel = st.session_state.get("sel_patient")
    if sel:
        st.divider()
        _detail(sel, settings)


def _add_form() -> None:
    with st.form("add_patient_page"):
        name = st.text_input("Name")
        phone = st.text_input("Phone (with country code, e.g. +91 98xxxxxxxx)")
        c = st.columns(2)
        age = c[0].number_input("Age", 0, 120, value=0)
        sex = c[1].selectbox("Sex", ["", "Female", "Male", "Other"])
        flags = st.text_input("Medical flags / allergies")
        notes = st.text_area("Notes")
        if st.form_submit_button("Add patient"):
            if not name.strip() or not phone.strip():
                st.error("Name and phone are required.")
                return
            if repository.find_patient_by_phone(phone):
                st.warning("A patient with this phone already exists.")
                return
            pid = repository.create_patient(name, phone, age=age or None,
                                            sex=sex or None,
                                            medical_flags=flags or None,
                                            notes=notes or None)
            st.session_state["sel_patient"] = pid
            st.success("Patient added.")
            st.rerun()


def _detail(pid: int, settings) -> None:
    p = repository.get_patient(pid)
    if not p:
        st.session_state.pop("sel_patient", None)
        return
    tz = settings.timezone
    st.subheader(f"{p.name}")

    with st.form("edit_patient"):
        name = st.text_input("Name", value=p.name)
        phone = st.text_input("Phone", value=p.phone)
        c = st.columns(2)
        age = c[0].number_input("Age", 0, 120, value=int(p.age or 0))
        sex = c[1].selectbox("Sex", ["", "Female", "Male", "Other"],
                             index=["", "Female", "Male", "Other"].index(p.sex or ""))
        flags = st.text_input("Medical flags / allergies", value=p.medical_flags or "")
        notes = st.text_area("Notes", value=p.notes or "")
        recall = st.date_input("Recall due (leave in past/today if due now)",
                               value=p.recall_due) if p.recall_due else \
            st.date_input("Recall due", value=None)
        if st.form_submit_button("Save changes"):
            repository.update_patient(pid, name=name, phone=phone, age=age or None,
                                      sex=sex or None, medical_flags=flags or None,
                                      notes=notes or None, recall_due=recall)
            st.success("Saved.")
            st.rerun()

    cols = st.columns(2)
    if cols[0].button(f"Set {RECALL_MONTHS}-month recall from today"):
        due = today_local(tz) + timedelta(days=RECALL_MONTHS * 30)
        repository.update_patient(pid, recall_due=due)
        st.rerun()
    if cols[1].button("➕ Book for this patient"):
        go("Book", book_mode="new", book_patient_id=pid)
        st.rerun()

    st.markdown("**Appointment history**")
    history = repository.appointments_for_patient(pid)
    if not history:
        st.caption("No appointments yet.")
    for a in history:
        when = to_local(a.start_ts, tz)
        st.markdown(f"- {fmt_date(when)} {fmt_time(when)} · {a.procedure} · "
                    f"*{STATUS_LABELS.get(a.status, a.status)}*")
