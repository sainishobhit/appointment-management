"""CRUD over the schema, returning plain dataclasses from models.py.

Reads are intentionally uncached: at ~30-40 appointments/week the queries are
trivial, and reading fresh on every Streamlit rerun eliminates a whole class of
stale-cache bugs.
"""
from __future__ import annotations

from datetime import datetime, date, timedelta

from sqlalchemy import and_, delete, insert, or_, select, update

from . import db
from .config import ACTIVE_STATUSES
from .models import Appointment, AvailabilityBlock, Patient, Settings
from .timeutil import now_local


# --- row mappers -------------------------------------------------------------

def _patient(r) -> Patient:
    return Patient(
        id=r.id, name=r.name, phone=r.phone, age=r.age, sex=r.sex,
        medical_flags=r.medical_flags, notes=r.notes, recall_due=r.recall_due,
        created_at=r.created_at,
    )


def _appt(r) -> Appointment:
    return Appointment(
        id=r.id, patient_id=r.patient_id, start_ts=r.start_ts,
        duration_min=r.duration_min, procedure=r.procedure, status=r.status,
        notes=r.notes, follow_up_of=r.follow_up_of, reminder_sent=r.reminder_sent,
        created_at=r.created_at,
        patient_name=getattr(r, "patient_name", None),
        patient_phone=getattr(r, "patient_phone", None),
    )


def _block(r) -> AvailabilityBlock:
    return AvailabilityBlock(
        id=r.id, kind=r.kind, start_time=r.start_time, end_time=r.end_time,
        day_of_week=r.day_of_week, start_date=r.start_date, end_date=r.end_date,
        label=r.label,
    )


# --- settings ----------------------------------------------------------------

def get_settings() -> Settings:
    eng = db.get_engine()
    with eng.connect() as conn:
        r = conn.execute(select(db.settings).where(db.settings.c.id == 1)).first()
    return Settings(
        buffer_min=r.buffer_min, daily_cap=r.daily_cap, timezone=r.timezone,
        procedures=list(r.procedures or []), templates=dict(r.templates or {}),
    )


def update_settings(**fields) -> None:
    eng = db.get_engine()
    with eng.begin() as conn:
        conn.execute(update(db.settings).where(db.settings.c.id == 1).values(**fields))


# --- patients ----------------------------------------------------------------

def list_patients() -> list[Patient]:
    eng = db.get_engine()
    with eng.connect() as conn:
        rows = conn.execute(select(db.patients).order_by(db.patients.c.name)).all()
    return [_patient(r) for r in rows]


def search_patients(q: str) -> list[Patient]:
    if not q:
        return list_patients()
    like = f"%{q.strip()}%"
    eng = db.get_engine()
    with eng.connect() as conn:
        rows = conn.execute(
            select(db.patients)
            .where(or_(db.patients.c.name.ilike(like), db.patients.c.phone.ilike(like)))
            .order_by(db.patients.c.name)
        ).all()
    return [_patient(r) for r in rows]


def get_patient(pid: int) -> Patient | None:
    eng = db.get_engine()
    with eng.connect() as conn:
        r = conn.execute(select(db.patients).where(db.patients.c.id == pid)).first()
    return _patient(r) if r else None


def find_patient_by_phone(phone: str) -> Patient | None:
    from .whatsapp import normalize_phone
    target = normalize_phone(phone)
    if not target:
        return None
    for p in list_patients():
        if normalize_phone(p.phone) == target:
            return p
    return None


def create_patient(name: str, phone: str, **fields) -> int:
    eng = db.get_engine()
    with eng.begin() as conn:
        res = conn.execute(insert(db.patients).values(
            name=name.strip(), phone=phone.strip(), created_at=now_local(), **fields
        ))
        return int(res.inserted_primary_key[0])


def update_patient(pid: int, **fields) -> None:
    eng = db.get_engine()
    with eng.begin() as conn:
        conn.execute(update(db.patients).where(db.patients.c.id == pid).values(**fields))


# --- appointments ------------------------------------------------------------

def _appt_join():
    j = db.appointments.join(db.patients, db.appointments.c.patient_id == db.patients.c.id)
    return (
        select(
            db.appointments,
            db.patients.c.name.label("patient_name"),
            db.patients.c.phone.label("patient_phone"),
        ).select_from(j)
    )


def list_appointments(start: datetime, end: datetime,
                      statuses: tuple[str, ...] | None = None) -> list[Appointment]:
    stmt = _appt_join().where(
        and_(db.appointments.c.start_ts >= start, db.appointments.c.start_ts < end)
    ).order_by(db.appointments.c.start_ts)
    if statuses:
        stmt = stmt.where(db.appointments.c.status.in_(statuses))
    eng = db.get_engine()
    with eng.connect() as conn:
        rows = conn.execute(stmt).all()
    return [_appt(r) for r in rows]


def get_appointment(aid: int) -> Appointment | None:
    eng = db.get_engine()
    with eng.connect() as conn:
        r = conn.execute(_appt_join().where(db.appointments.c.id == aid)).first()
    return _appt(r) if r else None


def appointments_for_patient(pid: int) -> list[Appointment]:
    stmt = _appt_join().where(db.appointments.c.patient_id == pid).order_by(
        db.appointments.c.start_ts.desc())
    eng = db.get_engine()
    with eng.connect() as conn:
        rows = conn.execute(stmt).all()
    return [_appt(r) for r in rows]


def active_between(start: datetime, end: datetime) -> list[Appointment]:
    """Active (scheduled/confirmed) appointments — feeds the scheduler."""
    return list_appointments(start, end, statuses=ACTIVE_STATUSES)


def create_appointment(patient_id: int, start_ts: datetime, duration_min: int,
                       procedure: str, **fields) -> int:
    eng = db.get_engine()
    with eng.begin() as conn:
        res = conn.execute(insert(db.appointments).values(
            patient_id=patient_id, start_ts=start_ts, duration_min=duration_min,
            procedure=procedure, status="scheduled", reminder_sent=False,
            created_at=now_local(), **fields,
        ))
        return int(res.inserted_primary_key[0])


def update_appointment(aid: int, **fields) -> None:
    eng = db.get_engine()
    with eng.begin() as conn:
        conn.execute(update(db.appointments).where(db.appointments.c.id == aid).values(**fields))


def set_status(aid: int, status: str) -> None:
    update_appointment(aid, status=status)


# --- availability ------------------------------------------------------------

def list_blocks(kind: str | None = None) -> list[AvailabilityBlock]:
    stmt = select(db.availability_blocks)
    if kind:
        stmt = stmt.where(db.availability_blocks.c.kind == kind)
    eng = db.get_engine()
    with eng.connect() as conn:
        rows = conn.execute(stmt).all()
    return [_block(r) for r in rows]


def create_block(kind: str, start_time, end_time, **fields) -> int:
    eng = db.get_engine()
    with eng.begin() as conn:
        res = conn.execute(insert(db.availability_blocks).values(
            kind=kind, start_time=start_time, end_time=end_time, **fields))
        return int(res.inserted_primary_key[0])


def delete_block(bid: int) -> None:
    eng = db.get_engine()
    with eng.begin() as conn:
        conn.execute(delete(db.availability_blocks).where(db.availability_blocks.c.id == bid))


# --- recalls -----------------------------------------------------------------

def patients_recall_due(as_of: date | None = None) -> list[Patient]:
    as_of = as_of or now_local().date()
    eng = db.get_engine()
    with eng.connect() as conn:
        rows = conn.execute(
            select(db.patients)
            .where(and_(db.patients.c.recall_due.is_not(None),
                        db.patients.c.recall_due <= as_of))
            .order_by(db.patients.c.recall_due)
        ).all()
    return [_patient(r) for r in rows]
