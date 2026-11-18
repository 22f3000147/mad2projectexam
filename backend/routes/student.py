"""Student APIs: browse exams, book / cancel slots, upcoming + history, profile."""
from datetime import datetime
import os
import re
from flask import Blueprint, jsonify, request, g, send_file
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from extensions import db
from models import Course, Examination, ExaminationSlot, Booking, Evaluation
from models.constants import *
from utils.auth import roles_required
from utils.helpers import (ApiError, body, need_int, need_text, show_dt, get_or_404, refresh_slot)
from utils.validators import PHONE_RE
from utils.jobs import start_job, job_status
from tasks import export_history_csv
from config import Config

student_bp = Blueprint("student", __name__)
student_only = roles_required(ROLE_STUDENT)


def starts_at(slot):
    return datetime.combine(slot.date, slot.start_time)


def booking_state(exam):
    """Is student booking open for this exam right now? -> (True/False, reason)"""
    if exam.status != EXAM_BOOKING_OPEN:
        return False, "Booking is not open"
    now = datetime.now()         
    if exam.booking_start and now < exam.booking_start:
        return False, f"Booking opens {exam.booking_start:%d %b %H:%M}"
    if exam.booking_end and now > exam.booking_end:
        return False, f"Booking closed {exam.booking_end:%d %b %H:%M}"
    return True, ""


def my_bookings():
    return Booking.query.filter_by(student_id=g.current_user.id).order_by(Booking.id.desc()).all()


def held_by_exam(bookings):
    """exam_id -> booking, for bookings that still count (Booked / Completed)."""
    return {b.examination_id: b for b in bookings if b.status in (BOOKING_BOOKED, BOOKING_COMPLETED)}


def slot_state(slot, held, bookings):
    """Can this student book this slot? -> (True/False, reason)"""
    ok, note = booking_state(slot.examination)
    if not ok:
        return False, note
    mine = held.get(slot.examination_id)
    if mine:
        return False, "Booked by you" if mine.slot_id == slot.id else "You already booked this exam"
    if slot.status != SLOT_AVAILABLE or slot.available_seats < 1:
        return False, "Slot is full"
    if starts_at(slot) <= datetime.now():
        return False, "Slot has already started"
    for b in bookings:
        o = b.slot
        if b.status == BOOKING_BOOKED and o.date == slot.date and slot.start_time < o.end_time and slot.end_time > o.start_time:
            return False, "Clashes with another booking"
    return True, ""


def cancel_state(b):
    """Can the student cancel? Only while booking is open, before the deadline and slot start."""
    if b.status != BOOKING_BOOKED:
        return False, ""
    exam = b.examination
    if exam.status != EXAM_BOOKING_OPEN:
        return False, "Booking is closed, cancellation not allowed"
    if exam.booking_end and datetime.now() > exam.booking_end:
        return False, "Cancellation deadline has passed"
    if starts_at(b.slot) <= datetime.now():
        return False, "Slot has already started"
    return True, ""


def open_exams_query():
    return (Examination.query.join(Course, Examination.course_id == Course.id)
            .filter(Examination.status == EXAM_BOOKING_OPEN, Course.status == COURSE_ACTIVE))


def exam_dict(e, held, detail=False):
    ok, note = booking_state(e)
    mine = held.get(e.id)
    d = {
        "id": e.id, "course_id": e.course_id, "course_code": e.course.code, "course_name": e.course.name,
        "name": e.name, "exam_type": e.exam_type, "duration_minutes": e.duration_minutes,
        "max_marks": e.max_marks, "status": e.status,
        "booking_start": show_dt(e.booking_start), "booking_end": show_dt(e.booking_end),
        "open_slots": len([s for s in e.slots if s.status == SLOT_AVAILABLE and s.available_seats > 0]),
        "booked": bool(mine), "my_slot": f"{mine.slot.date} {mine.slot.start_time:%H:%M}" if mine else None,
        "bookable": ok and not mine, "note": "You have booked this exam" if mine else note,
    }
    if detail:
        d["instructions"] = e.instructions
        d["rubrics"] = [{"criterion_name": r.criterion_name, "max_marks": r.max_marks,
                         "description": r.description} for r in e.rubrics]
    return d


def slot_dict(s, held, bookings):
    can, note = slot_state(s, held, bookings)
    mine = held.get(s.examination_id)
    mine = mine if mine and mine.slot_id == s.id and mine.status == BOOKING_BOOKED else None
    can_cancel, cancel_note = cancel_state(mine) if mine else (False, "")
    return {"id": s.id, "examination_id": s.examination_id, "exam_name": s.examination.name,
            "course_code": s.examination.course.code, "examiner_name": s.examiner.full_name,
            "date": s.date.isoformat(), "start_time": s.start_time.strftime("%H:%M"),
            "end_time": s.end_time.strftime("%H:%M"), "max_capacity": s.max_capacity,
            "available_seats": s.available_seats, "status": s.status, "meeting_link": s.meeting_link,
            "can_book": can, "note": note,
            "my_booking_id": mine.id if mine else None, "can_cancel": can_cancel, "cancel_note": cancel_note}


def booking_dict(b):
    s, e, ev = b.slot, b.examination, b.evaluation
    can_cancel, cancel_note = cancel_state(b)
    result = None
    if ev and ev.status == EVAL_PUBLISHED:         
        result = {"total": ev.total_marks, "max": e.max_marks, "remarks": ev.remarks,
                  "date": show_dt(ev.evaluation_date),
                  "examiner": ev.examiner.full_name,
                  "scores": [{"criterion": sc.rubric.criterion_name, "awarded": sc.awarded_marks,
                              "max": sc.rubric.max_marks} for sc in ev.scores]}
    if result:
        result_status = "Published"
    elif ev and ev.status == EVAL_SUBMITTED:
        result_status = "Evaluated, awaiting publication"
    else:
        result_status = "Pending"
    return {"id": b.id, "status": b.status, "booking_date": show_dt(b.booking_date),
            "exam_id": e.id, "exam_name": e.name, "course_code": e.course.code, "exam_type": e.exam_type,
            "duration_minutes": e.duration_minutes, "max_marks": e.max_marks,
            "slot_id": s.id, "slot_date": s.date.isoformat(), "slot_start": s.start_time.strftime("%H:%M"),
            "slot_end": s.end_time.strftime("%H:%M"), "examiner_name": s.examiner.full_name,
            "meeting_link": s.meeting_link, "can_cancel": can_cancel, "cancel_note": cancel_note,
            "result_status": result_status, "result": result}


@student_bp.get("/dashboard")
@student_only
def dashboard():
    bookings = my_bookings()
    held = held_by_exam(bookings)
    exams = open_exams_query().all()
    slots = [s for e in exams for s in e.slots]
    now = datetime.now()
    return jsonify(
        available_exams=len([e for e in exams if e.id not in held and booking_state(e)[0]]),
        available_slots=len([s for s in slots if slot_state(s, held, bookings)[0]]),
        upcoming=len([b for b in bookings if b.status == BOOKING_BOOKED and starts_at(b.slot) > now]),
        results=len([b for b in bookings if b.evaluation and b.evaluation.status == EVAL_PUBLISHED]),
    )


@student_bp.get("/courses")
@student_only
def list_courses():
    courses = {e.course_id: e.course for e in open_exams_query().all()}
    return jsonify([{"id": c.id, "code": c.code, "name": c.name} for c in courses.values()])


@student_bp.get("/exams")
@student_only
def list_exams():
    """Available exams (booking open) with search + filters."""
    query = open_exams_query()
    q = request.args.get("q", "").strip()
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Examination.name.ilike(like), Course.code.ilike(like), Course.name.ilike(like)))
    if request.args.get("exam_type"):
        query = query.filter(Examination.exam_type == request.args["exam_type"])
    if request.args.get("course_id"):
        query = query.filter(Examination.course_id == int(request.args["course_id"]))
    held = held_by_exam(my_bookings())
    return jsonify([exam_dict(e, held) for e in query.order_by(Examination.id).all()])


@student_bp.get("/exams/<int:exam_id>")
@student_only
def exam_detail(exam_id):
    exam = get_or_404(Examination, exam_id, "Examination")
    held = held_by_exam(my_bookings())
    if exam.status != EXAM_BOOKING_OPEN and exam.id not in {b.examination_id for b in my_bookings()}:
        raise ApiError("Examination not found", 404)
    return jsonify(exam_dict(exam, held, detail=True))


@student_bp.get("/slots")
@student_only
def list_slots():
    bookings = my_bookings()
    held = held_by_exam(bookings)
    slots = []
    for e in open_exams_query().all():
        if request.args.get("exam_id") and e.id != int(request.args["exam_id"]):
            continue
        slots += [s for s in e.slots if s.status in (SLOT_AVAILABLE, SLOT_FULL)]
    slots.sort(key=lambda s: (s.date, s.start_time))
    return jsonify([slot_dict(s, held, bookings) for s in slots])


@student_bp.post("/bookings")
@student_only
def book_slot():
    slot = get_or_404(ExaminationSlot, need_int(body(), "slot_id", "Slot"), "Slot")
    bookings = my_bookings()
    ok, reason = slot_state(slot, held_by_exam(bookings), bookings)
    if not ok:
        raise ApiError(reason, 409)
    taken = ExaminationSlot.query.filter(
        ExaminationSlot.id == slot.id, ExaminationSlot.status == SLOT_AVAILABLE,
        ExaminationSlot.available_seats > 0
    ).update({ExaminationSlot.available_seats: ExaminationSlot.available_seats - 1}, synchronize_session=False)
    if not taken:
        db.session.rollback()
        raise ApiError("Sorry, the slot just got full", 409)
    booking = Booking(student_id=g.current_user.id, slot_id=slot.id, examination_id=slot.examination_id)
    db.session.add(booking)
    try:
        db.session.flush()
    except IntegrityError:              
        db.session.rollback()
        raise ApiError("You already booked this exam", 409)
    refresh_slot(slot)                  
    db.session.commit()
    return jsonify(booking_dict(booking)), 201


@student_bp.post("/bookings/<int:booking_id>/cancel")
@student_only
def cancel_booking(booking_id):
    booking = get_or_404(Booking, booking_id, "Booking")
    if booking.student_id != g.current_user.id:
        raise ApiError("Booking not found", 404)
    ok, reason = cancel_state(booking)
    if not ok:
        raise ApiError(reason or "This booking cannot be cancelled", 409)
    booking.status = BOOKING_CANCELLED
    db.session.flush()
    refresh_slot(booking.slot)         
    db.session.commit()
    return jsonify(booking_dict(booking))


@student_bp.get("/bookings")
@student_only
def list_bookings():
    """?upcoming=1 -> future booked exams, ?history=1 -> finished / cancelled / past ones."""
    now = datetime.now()
    rows = my_bookings()
    if request.args.get("upcoming"):
        rows = [b for b in rows if b.status == BOOKING_BOOKED and starts_at(b.slot) > now]
        rows.sort(key=lambda b: starts_at(b.slot))
    elif request.args.get("history"):
        rows = [b for b in rows if b.status != BOOKING_BOOKED or starts_at(b.slot) <= now]
    return jsonify([booking_dict(b) for b in rows])


@student_bp.get("/profile")
@student_only
def get_profile():
    return jsonify(g.current_user.to_dict())


@student_bp.put("/profile")
@student_only
def update_profile():
    data = body()
    me = g.current_user
    name = need_text(data, "full_name", "Full name")
    phone = (data.get("phone") or "").strip()
    if phone and not PHONE_RE.match(phone):
        raise ApiError("Phone must be 10 digits")
    new_password = data.get("new_password") or ""
    if new_password:
        if not me.check_password(data.get("current_password") or ""):
            raise ApiError("Current password is wrong")
        if len(new_password) < 6:
            raise ApiError("New password must be at least 6 characters")
        me.set_password(new_password)
    me.full_name, me.phone = name, phone or None
    me.department = (data.get("department") or "").strip() or None
    db.session.commit()
    return jsonify(me.to_dict())


def export_path(task_id):
    """Each student can only reach their own file: the name contains their id."""
    if not re.fullmatch(r"[0-9a-f\-]{36}", task_id):
        raise ApiError("Export not found", 404)
    return os.path.join(Config.EXPORT_DIR, f"student_{g.current_user.id}_{task_id}.csv")


@student_bp.post("/export")
@student_only
def start_export():
    """Starts a Celery job; the student is alerted when it finishes."""
    return jsonify(task_id=start_job(export_history_csv, g.current_user.id)), 202


@student_bp.get("/export/<task_id>")
@student_only
def export_status(task_id):
    path = export_path(task_id)
    status = job_status(task_id)
    ready = status["state"] == "SUCCESS" and os.path.exists(path)
    return jsonify(state=status["state"], ready=ready, error=status["error"],
                   rows=(status["result"] or {}).get("rows") if ready else None)


@student_bp.get("/export/<task_id>/download")
@student_only
def export_download(task_id):
    path = export_path(task_id)
    if not os.path.exists(path):
        raise ApiError("Export is not ready", 404)
    return send_file(path, mimetype="text/csv", as_attachment=True, download_name="exam_history.csv")
