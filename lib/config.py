"""Default configuration. These seed the `settings` row on first run and are
fully editable later in the Settings screen (brief §13 stays non-blocking)."""
from __future__ import annotations

from datetime import time

# --- Scheduling defaults -----------------------------------------------------
DEFAULT_BUFFER_MIN = 10
DEFAULT_DAILY_CAP = 8
DEFAULT_TIMEZONE = "Asia/Kolkata"
RECALL_MONTHS = 6
SUGGESTION_HORIZON_DAYS = 21
SLOT_STEP_MIN = 15

# name -> minutes. Order is preserved in the picker.
DEFAULT_PROCEDURES = [
    {"name": "Consultation", "duration_min": 15},
    {"name": "Scaling / Cleaning", "duration_min": 30},
    {"name": "Filling", "duration_min": 30},
    {"name": "Root Canal (RCT)", "duration_min": 45},
    {"name": "Extraction", "duration_min": 30},
    {"name": "Crown", "duration_min": 30},
    {"name": "Follow-up", "duration_min": 15},
]

# Default recurring clinic sessions. day_of_week uses Monday=0 .. Sunday=6.
# Mon-Sat evenings 5-8 PM, plus Saturday morning 10 AM-1 PM.
DEFAULT_CLINIC_SESSIONS = [
    {"day_of_week": d, "start": time(17, 0), "end": time(20, 0)} for d in range(0, 6)
] + [
    {"day_of_week": 5, "start": time(10, 0), "end": time(13, 0)},
]

# --- WhatsApp message templates ---------------------------------------------
# Placeholders: {name} {date} {time} {procedure}
DEFAULT_TEMPLATES = {
    "confirmation": (
        "Hi {name}, your dental appointment for {procedure} is confirmed on "
        "{date} at {time}. Please arrive 5 minutes early. — Dr. S"
    ),
    "reminder": (
        "Hi {name}, a reminder of your dental appointment for {procedure} "
        "tomorrow, {date} at {time}. Reply here if you need to reschedule. — Dr. S"
    ),
    "reschedule": (
        "Hi {name}, your dental appointment has been moved to {date} at {time} "
        "({procedure}). See you then! — Dr. S"
    ),
    "cancellation": (
        "Hi {name}, your dental appointment on {date} at {time} has been "
        "cancelled. Please message me to rebook. — Dr. S"
    ),
    "followup": (
        "Hi {name}, it's time to schedule your follow-up ({procedure}). "
        "I've proposed {date} at {time} — does that work? — Dr. S"
    ),
    "recall": (
        "Hi {name}, it's been a while since your last visit — a good time for a "
        "routine dental check-up. Would you like to book? — Dr. S"
    ),
}

DEFAULT_COUNTRY_CODE = "91"  # India
DEV_PASSWORD_FALLBACK = "dentist"  # only used when no app_password secret is set

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
STATUS_LABELS = {
    "scheduled": "Scheduled",
    "confirmed": "Confirmed",
    "completed": "Completed",
    "no_show": "No-show",
    "cancelled": "Cancelled",
}
ACTIVE_STATUSES = ("scheduled", "confirmed")
