from datetime import datetime

from lib.whatsapp import normalize_phone, build_link, render_message


def test_normalize_indian_variants():
    assert normalize_phone("+91 98765 43210") == "919876543210"
    assert normalize_phone("9876543210") == "919876543210"
    assert normalize_phone("09876543210") == "919876543210"
    assert normalize_phone("+1 (415) 555-2671") == "14155552671"


def test_normalize_empty():
    assert normalize_phone("") == ""
    assert normalize_phone(None) == ""


def test_build_link_encodes_text():
    link = build_link("9876543210", "Hi there!")
    assert link.startswith("https://wa.me/919876543210?text=")
    assert "Hi%20there%21" in link


def test_render_message_fills_placeholders():
    when = datetime(2026, 7, 22, 18, 30)
    msg = render_message("Hi {name}, {procedure} on {date} at {time}.",
                         name="Asha", when=when, procedure="RCT")
    assert "Asha" in msg
    assert "RCT" in msg
    assert "6:30 PM" in msg
    assert "22 Jul 2026" in msg


def test_render_message_keeps_unknown_placeholder():
    msg = render_message("Hi {name} {unknown}", name="X", when="", procedure="Y")
    assert "{unknown}" in msg
