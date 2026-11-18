"""Small helper functions used by the route files."""
from datetime import datetime, date, time
from flask import request
from extensions import db
from models import Booking
from models.constants import BOOKING_BOOKED, SLOT_AVAILABLE, SLOT_FULL


class ApiError(Exception):
    """Raise this anywhere in a route -> app.py turns it into a JSON error."""
    def __init__(self, message, status=400):
        self.message = message
        self.status = status


def body():
    return request.get_json(silent=True) or {}


def need_text(data, key, label):
    value = str(data.get(key) or "").strip()
    if not value:
        raise ApiError(f"{label} is required")
    return value


def need_int(data, key, label, minimum=1):
    try:
        value = int(data.get(key))
    except (TypeError, ValueError):
        raise ApiError(f"{label} must be a number")
    if value < minimum:
        raise ApiError(f"{label} must be at least {minimum}")
    return value


def opt_dt(data, key, label):
    raw = data.get(key)
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        raise ApiError(f"{label} is not a valid date/time")


def need_date(data, key, label):
    try:
        return date.fromisoformat(data.get(key) or "")
    except ValueError:
        raise ApiError(f"{label} is not a valid date")


def need_time(data, key, label):
    try:
        return time.fromisoformat(data.get(key) or "")
    except ValueError:
        raise ApiError(f"{label} is not a valid time")


def show_dt(value):
    return value.isoformat(timespec="minutes") if value else None


def get_or_404(model, item_id, label):
    item = db.session.get(model, item_id)
    if not item:
        raise ApiError(f"{label} not found", 404)
    return item


def refresh_slot(slot):
    """Recount seats from the bookings table and set Available/Full."""
    booked = Booking.query.filter_by(slot_id=slot.id, status=BOOKING_BOOKED).count()
    slot.available_seats = max(slot.max_capacity - booked, 0)
    if slot.status in (SLOT_AVAILABLE, SLOT_FULL):
        slot.status = SLOT_FULL if slot.available_seats == 0 else SLOT_AVAILABLE
