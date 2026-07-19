"""Pure WhatsApp helpers — build wa.me deep links and render message templates.
No Streamlit import, so this is unit-tested directly."""
from __future__ import annotations

import re
from urllib.parse import quote

from .config import DEFAULT_COUNTRY_CODE
from .timeutil import fmt_date, fmt_time


def normalize_phone(phone: str, default_cc: str = DEFAULT_COUNTRY_CODE) -> str:
    """Return digits-only E.164 (no '+') suitable for wa.me.

    Handles '+91 98xxx', '098xxx...', '98xxx...' (assumes default country).
    """
    raw = (phone or "").strip()
    if raw.startswith("+"):
        return re.sub(r"\D", "", raw)
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return ""
    # strip a single leading trunk 0 (common in local Indian numbers)
    if digits.startswith("0"):
        digits = digits.lstrip("0")
    # a bare 10-digit local number -> prepend country code
    if len(digits) == 10:
        return f"{default_cc}{digits}"
    return digits


def build_link(phone: str, text: str) -> str:
    """https://wa.me/<digits>?text=<url-encoded message>."""
    digits = normalize_phone(phone)
    return f"https://wa.me/{digits}?text={quote(text)}"


def render_message(template: str, *, name: str, when: object, procedure: str) -> str:
    """Fill a template string. `when` is a datetime (aware or naive).

    Unknown placeholders are left intact rather than raising.
    """
    from datetime import datetime

    date_str = fmt_date(when) if isinstance(when, datetime) else str(when)
    time_str = fmt_time(when) if isinstance(when, datetime) else ""
    fields = {
        "name": name or "there",
        "date": date_str,
        "time": time_str,
        "procedure": procedure or "your appointment",
    }

    class _Safe(dict):
        def __missing__(self, key):  # keep {unknown} untouched
            return "{" + key + "}"

    return template.format_map(_Safe(fields))
