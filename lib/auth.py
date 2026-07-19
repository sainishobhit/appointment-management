"""Single-password gate for the dentist. The password lives in st.secrets
(prod) or falls back to a dev default locally."""
from __future__ import annotations

import hmac

import streamlit as st

from .config import DEV_PASSWORD_FALLBACK
from .db import _secret


def _expected_password() -> str:
    return _secret("app_password", DEV_PASSWORD_FALLBACK)


def require_auth() -> None:
    """Block the app until the correct password is entered."""
    if st.session_state.get("authed"):
        return

    st.title("🦷 DentaFlow")
    st.caption("Please sign in to manage your appointments.")
    with st.form("login"):
        pw = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", use_container_width=True)
    if submitted:
        if hmac.compare_digest(pw, str(_expected_password())):
            st.session_state["authed"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()
