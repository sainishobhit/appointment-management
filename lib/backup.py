"""JSON export/import of all data — the dentist's one-tap backup."""
from __future__ import annotations

import json
from datetime import datetime, date, time

from sqlalchemy import insert, select

from . import db


def _serialize(v):
    if isinstance(v, (datetime, date, time)):
        return v.isoformat()
    return v


def export_all() -> str:
    """Dump every table to a JSON string."""
    eng = db.get_engine()
    out: dict[str, list[dict]] = {}
    tables = {
        "patients": db.patients,
        "appointments": db.appointments,
        "availability_blocks": db.availability_blocks,
        "settings": db.settings,
    }
    with eng.connect() as conn:
        for name, tbl in tables.items():
            rows = conn.execute(select(tbl)).mappings().all()
            out[name] = [{k: _serialize(v) for k, v in row.items()} for row in rows]
    return json.dumps(out, indent=2)


def _coerce(tbl, row: dict) -> dict:
    """Best-effort parse of ISO strings back into date/time/datetime by column type."""
    from sqlalchemy import Date, DateTime, Time
    result = {}
    for col in tbl.columns:
        if col.name not in row:
            continue
        val = row[col.name]
        if isinstance(val, str) and val:
            if isinstance(col.type, DateTime):
                val = datetime.fromisoformat(val)
            elif isinstance(col.type, Date):
                val = date.fromisoformat(val)
            elif isinstance(col.type, Time):
                val = time.fromisoformat(val)
        result[col.name] = val
    return result


def import_all(payload: str) -> None:
    """Replace all data with the contents of a previous export."""
    data = json.loads(payload)
    eng = db.get_engine()
    tables = {
        "patients": db.patients,
        "appointments": db.appointments,
        "availability_blocks": db.availability_blocks,
        "settings": db.settings,
    }
    with eng.begin() as conn:
        # delete children before parents
        for name in ("appointments", "availability_blocks", "patients", "settings"):
            conn.execute(tables[name].delete())
        for name in ("patients", "settings", "availability_blocks", "appointments"):
            for row in data.get(name, []):
                conn.execute(insert(tables[name]).values(**_coerce(tables[name], row)))
