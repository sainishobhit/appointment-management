"""Plain dataclasses returned by the repository. Kept free of Streamlit and
SQLAlchemy so views and tests can use them directly."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date, time


@dataclass
class Patient:
    id: int | None
    name: str
    phone: str
    age: int | None = None
    sex: str | None = None
    medical_flags: str | None = None
    notes: str | None = None
    recall_due: date | None = None
    created_at: datetime | None = None


@dataclass
class Appointment:
    id: int | None
    patient_id: int
    start_ts: datetime            # aware, clinic-local
    duration_min: int
    procedure: str
    status: str = "scheduled"
    notes: str | None = None
    follow_up_of: int | None = None
    reminder_sent: bool = False
    created_at: datetime | None = None
    # convenience join fields (populated by list queries)
    patient_name: str | None = None
    patient_phone: str | None = None


@dataclass
class AvailabilityBlock:
    id: int | None
    kind: str                     # 'clinic_session' | 'unavailable'
    start_time: time
    end_time: time
    day_of_week: int | None = None   # Monday=0..Sunday=6 (recurring)
    start_date: date | None = None   # for dated one-offs
    end_date: date | None = None
    label: str | None = None


@dataclass
class Settings:
    buffer_min: int
    daily_cap: int
    timezone: str
    procedures: list[dict] = field(default_factory=list)
    templates: dict = field(default_factory=dict)


@dataclass
class Slot:
    """A recommended appointment slot in naive clinic-local wall-clock time."""
    start: datetime               # naive local
    duration_min: int

    @property
    def end(self) -> datetime:
        from datetime import timedelta
        return self.start + timedelta(minutes=self.duration_min)
