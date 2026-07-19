"""Settings — procedures, scheduling knobs, message templates, and backup."""
from __future__ import annotations

import streamlit as st

from lib import repository
from lib.backup import export_all, import_all
from views.common import get_settings


def render() -> None:
    settings = get_settings()
    st.header("⚙️ Settings")

    with st.form("sched_settings"):
        st.subheader("Scheduling")
        c = st.columns(3)
        buffer_min = c[0].number_input("Buffer between patients (min)", 0, 60,
                                       value=settings.buffer_min, step=5)
        daily_cap = c[1].number_input("Max appointments/day", 1, 30,
                                      value=settings.daily_cap)
        timezone = c[2].text_input("Timezone", value=settings.timezone)

        st.subheader("Procedures & durations")
        procs = st.data_editor(
            settings.procedures, num_rows="dynamic", use_container_width=True,
            column_config={
                "name": st.column_config.TextColumn("Procedure", required=True),
                "duration_min": st.column_config.NumberColumn("Minutes", min_value=5,
                                                              max_value=240, step=5),
            }, key="proc_editor",
        )

        st.subheader("WhatsApp message templates")
        st.caption("Placeholders: {name} {date} {time} {procedure}")
        templates = {}
        for key, val in settings.templates.items():
            templates[key] = st.text_area(key.capitalize(), value=val, height=80)

        if st.form_submit_button("Save settings"):
            cleaned = [p for p in procs if p.get("name")]
            repository.update_settings(
                buffer_min=int(buffer_min), daily_cap=int(daily_cap),
                timezone=timezone.strip() or settings.timezone,
                procedures=cleaned, templates=templates,
            )
            st.success("Settings saved.")
            st.rerun()

    st.divider()
    st.subheader("Backup")
    st.download_button("⬇️ Download backup (JSON)", data=export_all(),
                       file_name="dentaflow-backup.json", mime="application/json")
    up = st.file_uploader("Restore from a backup file", type=["json"])
    if up is not None and st.button("⚠️ Restore (replaces all data)"):
        import_all(up.getvalue().decode("utf-8"))
        st.success("Data restored.")
        st.rerun()

    st.divider()
    st.caption("The app password is managed via Streamlit secrets (`app_password`), "
               "not here — change it in the Streamlit Cloud Secrets settings.")
