"""Database engine + schema. SQLAlchemy Core keeps SQL explicit and avoids ORM
session pitfalls under Streamlit's rerun model.

Connection string comes from `st.secrets["db_url"]` (Postgres in production) and
falls back to a local SQLite file for development.
"""
from __future__ import annotations

import os

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer, JSON, MetaData,
    String, Table, Time, create_engine, insert, select,
)
from sqlalchemy.engine import Engine

from . import config

metadata = MetaData()

patients = Table(
    "patients", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(120), nullable=False),
    Column("phone", String(32), nullable=False),
    Column("age", Integer),
    Column("sex", String(16)),
    Column("medical_flags", String(500)),
    Column("notes", String(2000)),
    Column("recall_due", Date),
    Column("created_at", DateTime(timezone=True)),
)

appointments = Table(
    "appointments", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("patient_id", Integer, ForeignKey("patients.id"), nullable=False),
    Column("start_ts", DateTime(timezone=True), nullable=False),
    Column("duration_min", Integer, nullable=False),
    Column("procedure", String(120), nullable=False),
    Column("status", String(20), nullable=False, default="scheduled"),
    Column("notes", String(2000)),
    Column("follow_up_of", Integer, ForeignKey("appointments.id")),
    Column("reminder_sent", Boolean, nullable=False, default=False),
    Column("created_at", DateTime(timezone=True)),
)

availability_blocks = Table(
    "availability_blocks", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("kind", String(20), nullable=False),  # clinic_session | unavailable
    Column("day_of_week", Integer),               # Monday=0..Sunday=6
    Column("start_time", Time, nullable=False),
    Column("end_time", Time, nullable=False),
    Column("start_date", Date),
    Column("end_date", Date),
    Column("label", String(120)),
)

settings = Table(
    "settings", metadata,
    Column("id", Integer, primary_key=True),  # always 1
    Column("buffer_min", Integer, nullable=False),
    Column("daily_cap", Integer, nullable=False),
    Column("timezone", String(64), nullable=False),
    Column("procedures", JSON, nullable=False),
    Column("templates", JSON, nullable=False),
)


def _secret(key: str, default: str | None = None) -> str | None:
    """Read from st.secrets if available, else env var, else default."""
    try:
        import streamlit as st
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key.upper(), default)


def _db_url() -> str:
    return _secret("db_url", "sqlite:///dentaflow.db")


def _make_engine() -> Engine:
    url = _db_url()
    kwargs = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


def get_engine() -> Engine:
    """Cached singleton engine (via st.cache_resource when inside Streamlit)."""
    try:
        import streamlit as st
        return st.cache_resource(_make_engine)()
    except Exception:
        global _ENGINE
        try:
            return _ENGINE
        except NameError:
            _ENGINE = _make_engine()
            return _ENGINE


def init_schema() -> None:
    """Create tables if missing and seed the single settings row. Idempotent."""
    engine = get_engine()
    metadata.create_all(engine)
    with engine.begin() as conn:
        existing = conn.execute(select(settings.c.id).where(settings.c.id == 1)).first()
        if existing is None:
            conn.execute(insert(settings).values(
                id=1,
                buffer_min=config.DEFAULT_BUFFER_MIN,
                daily_cap=config.DEFAULT_DAILY_CAP,
                timezone=config.DEFAULT_TIMEZONE,
                procedures=config.DEFAULT_PROCEDURES,
                templates=config.DEFAULT_TEMPLATES,
            ))
            # seed default recurring clinic sessions
            for s in config.DEFAULT_CLINIC_SESSIONS:
                conn.execute(insert(availability_blocks).values(
                    kind="clinic_session",
                    day_of_week=s["day_of_week"],
                    start_time=s["start"],
                    end_time=s["end"],
                    label="Clinic session",
                ))
