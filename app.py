"""DentaFlow — solo-dentist appointment manager. Entry point: auth gate + a
simple session_state router so cross-page actions (Reschedule/Follow-up) work."""
from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="DentaFlow", page_icon="🦷", layout="centered")

from sqlalchemy.exc import SQLAlchemyError

from lib.auth import require_auth
from lib.db import init_schema
from views import (availability, book, patients, reminders, today, week)
from views import settings as settings_view

try:
    init_schema()
except SQLAlchemyError as e:
    # psycopg error messages contain host/port/reason but never the password,
    # so it's safe to surface them instead of the redacted Streamlit crash.
    reason = str(getattr(e, "orig", e)).strip()
    st.error("🦷 DentaFlow could not connect to its database.")
    st.markdown("**Underlying error:**")
    st.code(reason or repr(e))
    st.markdown(
        "**Most likely fixes**\n"
        "- On Supabase free tier, use the **Session pooler** connection string, "
        "not the direct one:\n"
        "  - host `aws-0-<region>.pooler.supabase.com` (not `db.<ref>.supabase.co`)\n"
        "  - user `postgres.<project-ref>` (not just `postgres`)\n"
        "  - scheme `postgresql+psycopg://`, ending with `?sslmode=require`\n"
        "- If it says *password authentication failed*: fix the password and "
        "URL-encode special characters (`@`→`%40`, `#`→`%23`, `/`→`%2F`).\n"
        "- If it says *could not translate host name*: the region/host is wrong.\n"
        "- Make sure the Supabase project isn't **paused**.\n\n"
        "Update `db_url` in **Manage app → Settings → Secrets**, then reboot."
    )
    st.stop()

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
