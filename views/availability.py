"""Availability — recurring clinic sessions and time off (college/exams/leave).
These feed directly into the Smart Slot Suggestions recommender."""
from __future__ import annotations

from datetime import time, timedelta

import streamlit as st

from lib import repository
from lib.config import DAY_NAMES
from lib.timeutil import today_local, fmt_time, fmt_date


def render() -> None:
    st.header("🕒 Availability")
    tab1, tab2 = st.tabs(["Clinic sessions", "Time off / College"])
    with tab1:
        _clinic_sessions()
    with tab2:
        _unavailable()


def _clinic_sessions() -> None:
    st.caption("When you normally see patients. The recommender only suggests slots inside these.")
    blocks = [b for b in repository.list_blocks("clinic_session") if b.day_of_week is not None]
    blocks.sort(key=lambda b: (b.day_of_week, b.start_time))
    for b in blocks:
        c = st.columns([4, 1])
        c[0].markdown(f"**{DAY_NAMES[b.day_of_week]}** · "
                      f"{fmt_time(b.start_time)}–{fmt_time(b.end_time)}")
        if c[1].button("Delete", key=f"delcs-{b.id}"):
            repository.delete_block(b.id)
            st.rerun()

    with st.form("add_session"):
        st.markdown("**Add a clinic session**")
        days = st.multiselect("Day(s)", list(range(7)),
                              format_func=lambda d: DAY_NAMES[d])
        c = st.columns(2)
        start = c[0].time_input("Start", value=time(17, 0), step=timedelta(minutes=15))
        end = c[1].time_input("End", value=time(20, 0), step=timedelta(minutes=15))
        if st.form_submit_button("Add session"):
            if not days:
                st.error("Pick at least one day.")
            elif end <= start:
                st.error("End must be after start.")
            else:
                for d in days:
                    repository.create_block("clinic_session", start, end,
                                            day_of_week=d, label="Clinic session")
                st.rerun()


def _unavailable() -> None:
    st.caption("Block college hours, lectures, exams, or leave. Nothing is suggested here.")
    blocks = repository.list_blocks("unavailable")
    recurring = [b for b in blocks if b.day_of_week is not None]
    oneoff = [b for b in blocks if b.day_of_week is None]

    if recurring:
        st.markdown("**Weekly**")
        for b in sorted(recurring, key=lambda b: (b.day_of_week, b.start_time)):
            c = st.columns([4, 1])
            c[0].markdown(f"{DAY_NAMES[b.day_of_week]} · "
                          f"{fmt_time(b.start_time)}–{fmt_time(b.end_time)} · "
                          f"{b.label or 'Blocked'}")
            if c[1].button("Delete", key=f"delu-{b.id}"):
                repository.delete_block(b.id)
                st.rerun()

    if oneoff:
        st.markdown("**One-off**")
        for b in sorted(oneoff, key=lambda b: (b.start_date or today_local())):
            c = st.columns([4, 1])
            span = fmt_date(b.start_date)
            if b.end_date and b.end_date != b.start_date:
                span += f" → {fmt_date(b.end_date)}"
            c[0].markdown(f"{span} · {fmt_time(b.start_time)}–{fmt_time(b.end_time)} · "
                          f"{b.label or 'Blocked'}")
            if c[1].button("Delete", key=f"delo-{b.id}"):
                repository.delete_block(b.id)
                st.rerun()

    with st.form("add_block"):
        st.markdown("**Add time off**")
        kind = st.radio("Repeats?", ["Weekly (recurring)", "One-off dates"],
                        horizontal=True)
        label = st.text_input("Label", value="College")
        c = st.columns(2)
        start = c[0].time_input("Start", value=time(9, 0), step=timedelta(minutes=15))
        end = c[1].time_input("End", value=time(17, 0), step=timedelta(minutes=15))
        days = st.multiselect("Day(s)", list(range(7)),
                              format_func=lambda d: DAY_NAMES[d])
        dr = st.date_input("Date range (one-off)",
                           value=(today_local(), today_local()))
        if st.form_submit_button("Add time off"):
            if end <= start:
                st.error("End must be after start.")
            elif kind.startswith("Weekly"):
                if not days:
                    st.error("Pick at least one day.")
                else:
                    for d in days:
                        repository.create_block("unavailable", start, end,
                                                day_of_week=d, label=label or "Blocked")
                    st.rerun()
            else:
                sd, ed = (dr if isinstance(dr, tuple) else (dr, dr))
                repository.create_block("unavailable", start, end, start_date=sd,
                                        end_date=ed, label=label or "Blocked")
                st.rerun()
