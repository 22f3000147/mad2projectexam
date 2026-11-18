"""Small helper functions used by the route files."""
from datetime import datetime, date, time
from flask import request
from extensions import db
from models import Booking, Examination
from models.constants import (BOOKING_BOOKED, BOOKING_COMPLETED, SLOT_AVAILABLE, SLOT_FULL,
                              SLOT_COMPLETED, EXAM_BOOKING_OPEN, EXAM_CLOSED, EXAM_COMPLETED)


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


def count_booked(slot):
    """Students holding a seat = Booked + Completed (cancelled ones free the seat)."""
    if slot.id is None:
        return 0
    return Booking.query.filter(Booking.slot_id == slot.id,
                                Booking.status.in_((BOOKING_BOOKED, BOOKING_COMPLETED))).count()


def refresh_slot(slot):
    """Recount seats from the bookings table and set Available/Full."""
    booked = count_booked(slot)
    slot.available_seats = max(slot.max_capacity - booked, 0)
    if slot.status in (SLOT_AVAILABLE, SLOT_FULL):
        slot.status = SLOT_FULL if slot.available_seats == 0 else SLOT_AVAILABLE


def finish_exam(exam):
    """Mark an exam Completed (used by admin AND examiner). Every booked student must be evaluated."""
    pending = Booking.query.filter_by(examination_id=exam.id, status=BOOKING_BOOKED).count()
    if pending:
        raise ApiError(f"{pending} student(s) are still waiting for evaluation")
    exam.status = EXAM_COMPLETED
    for slot in exam.slots:
        if slot.status in (SLOT_AVAILABLE, SLOT_FULL):
            slot.status = SLOT_COMPLETED


def close_expired_bookings():
    """Exams whose booking deadline has passed move from Booking Open to Closed."""
    expired = Examination.query.filter(Examination.status == EXAM_BOOKING_OPEN,
                                       Examination.booking_end.isnot(None),
                                       Examination.booking_end < datetime.now()).all()
    for exam in expired:
        exam.status = EXAM_CLOSED
    if expired:
        db.session.commit()
