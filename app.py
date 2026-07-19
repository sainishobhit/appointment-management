"""DentaFlow — solo-dentist appointment manager. Entry point: auth gate + a
simple session_state router so cross-page actions (Reschedule/Follow-up) work."""
from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="DentaFlow", page_icon="🦷", layout="centered")

from lib.auth import require_auth
from lib.db import init_schema
from views import (availability, book, patients, reminders, today, week)
from views import settings as settings_view

init_schema()
require_auth()

PAGES = {
    "Today": ("📅", today.render),
    "Week": ("🗓️", week.render),
    "Book": ("➕", book.render),
    "Patients": ("👤", patients.render),
    "Availability": ("🕒", availability.render),
    "Reminders": ("🔔", reminders.render),
    "Settings": ("⚙️", settings_view.render),
}

# Programmatic navigation requested by go() (e.g. a Reschedule button).
goto = st.session_state.pop("_goto", None)
if goto in PAGES:
    st.session_state["nav"] = goto

with st.sidebar:
    st.title("🦷 DentaFlow")
    choice = st.radio("Menu", list(PAGES.keys()),
                      format_func=lambda k: f"{PAGES[k][0]} {k}", key="nav")
    st.divider()
    if st.button("Sign out", use_container_width=True):
        st.session_state.clear()
        st.rerun()

PAGES[choice][1]()
