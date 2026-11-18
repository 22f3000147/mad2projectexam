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
from utils.cache import remember
from utils.queries import exam_rubrics
from tasks import export_history_csv
from config import Config

student_bp = Blueprint("student", __name__)
student_only = roles_required(ROLE_STUDENT)


def starts_at(slot):
    return datetime.combine(slot.date, slot.start_time)


def window_state(status, start, end):
    """Is booking open? start / end are ISO strings (or None) so cached data can use this too."""
    if status != EXAM_BOOKING_OPEN:
        return False, "Booking is not open"
    now = datetime.now()         
    if start and now < datetime.fromisoformat(start):
        return False, f"Booking opens {datetime.fromisoformat(start):%d %b %H:%M}"
    if end and now > datetime.fromisoformat(end):
        return False, f"Booking closed {datetime.fromisoformat(end):%d %b %H:%M}"
    return True, ""


def booking_state(exam):
    return window_state(exam.status, show_dt(exam.booking_start), show_dt(exam.booking_end))


def my_bookings():
    return Booking.query.filter_by(student_id=g.current_user.id).order_by(Booking.id.desc()).all()


def held_by_exam(bookings):
    """exam_id -> booking, for bookings that still count (Booked / Completed)."""
    return {b.examination_id: b for b in bookings if b.status in (BOOKING_BOOKED, BOOKING_COMPLETED)}


def slot_state(slot, held, bookings):
    """Can this student book this slot? slot is the plain dict from slot_base(). -> (True/False, reason)"""
    ok, note = window_state(slot["exam_status"], slot["booking_start"], slot["booking_end"])
    if not ok:
        return False, note
    mine = held.get(slot["examination_id"])
    if mine:
        return False, "Booked by you" if mine.slot_id == slot["id"] else "You already booked this exam"
    if slot["status"] != SLOT_AVAILABLE or slot["available_seats"] < 1:
        return False, "Slot is full"
    if datetime.fromisoformat(f"{slot['date']}T{slot['start_time']}") <= datetime.now():
        return False, "Slot has already started"
    for b in bookings:
        o = b.slot
        if (b.status == BOOKING_BOOKED and o.date.isoformat() == slot["date"]
                and slot["start_time"] < o.end_time.strftime("%H:%M") and slot["end_time"] > o.start_time.strftime("%H:%M")):
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


def exam_base(e):
    """The part of an exam that is the same for every student (this is what gets cached)."""
    return {
        "id": e.id, "course_id": e.course_id, "course_code": e.course.code, "course_name": e.course.name,
        "name": e.name, "exam_type": e.exam_type, "duration_minutes": e.duration_minutes,
        "max_marks": e.max_marks, "status": e.status,
        "booking_start": show_dt(e.booking_start), "booking_end": show_dt(e.booking_end),
        "open_slots": len([s for s in e.slots if s.status == SLOT_AVAILABLE and s.available_seats > 0]),
    }


def open_exams_base():
    """All exams open for booking, cached. Search/filter + per-student flags are applied after."""
    return remember("exams:open", Config.CACHE_TTL_SHORT,
                    lambda: [exam_base(e) for e in open_exams_query().order_by(Examination.id).all()])


def personal_exam(base, held):
    """Cached exam + what is different for THIS student (already booked? can book now?)."""
    ok, note = window_state(base["status"], base["booking_start"], base["booking_end"])
    mine = held.get(base["id"])
    return {**base, "booked": bool(mine),
            "my_slot": f"{mine.slot.date} {mine.slot.start_time:%H:%M}" if mine else None,
            "bookable": ok and not mine, "note": "You have booked this exam" if mine else note}


def slot_base(s):
    """The part of a slot that is the same for every student (this is what gets cached)."""
    e = s.examination
    return {"id": s.id, "examination_id": s.examination_id, "exam_name": e.name, "course_code": e.course.code,
            "examiner_name": s.examiner.full_name, "date": s.date.isoformat(),
            "start_time": s.start_time.strftime("%H:%M"), "end_time": s.end_time.strftime("%H:%M"),
            "max_capacity": s.max_capacity, "available_seats": s.available_seats, "status": s.status,
            "meeting_link": s.meeting_link, "exam_status": e.status,
            "booking_start": show_dt(e.booking_start), "booking_end": show_dt(e.booking_end)}


def open_slots_base():
    """The exam schedule: every bookable/full slot of the exams open for booking, cached."""
    def build():
        slots = [slot_base(s) for e in open_exams_query().all() for s in e.slots
                 if s.status in (SLOT_AVAILABLE, SLOT_FULL)]
        return sorted(slots, key=lambda d: (d["date"], d["start_time"]))
    return remember("slots:open", Config.CACHE_TTL_SHORT, build)


def personal_slot(base, held, bookings):
    can, note = slot_state(base, held, bookings)
    mine = held.get(base["examination_id"])
    mine = mine if mine and mine.slot_id == base["id"] and mine.status == BOOKING_BOOKED else None
    can_cancel, cancel_note = cancel_state(mine) if mine else (False, "")
    shown = {k: v for k, v in base.items() if k not in ("exam_status", "booking_start", "booking_end")}
    return {**shown, "can_book": can, "note": note, "my_booking_id": mine.id if mine else None,
            "can_cancel": can_cancel, "cancel_note": cancel_note}


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
    now = datetime.now()
    exams, slots = open_exams_base(), open_slots_base()
    return jsonify(
        available_exams=len([e for e in exams if e["id"] not in held
                             and window_state(e["status"], e["booking_start"], e["booking_end"])[0]]),
        available_slots=len([s for s in slots if slot_state(s, held, bookings)[0]]),
        upcoming=len([b for b in bookings if b.status == BOOKING_BOOKED and starts_at(b.slot) > now]),
        results=len([b for b in bookings if b.evaluation and b.evaluation.status == EVAL_PUBLISHED]),
    )


@student_bp.get("/courses")
@student_only
def list_courses():
    courses = {e["course_id"]: {"id": e["course_id"], "code": e["course_code"], "name": e["course_name"]}
               for e in open_exams_base()}
    return jsonify(list(courses.values()))


@student_bp.get("/exams")
@student_only
def list_exams():
    """Available exams (booking open) with search + filters. Filtering is done on the cached list."""
    q = request.args.get("q", "").strip().lower()
    exam_type = request.args.get("exam_type")
    course_id = int(request.args["course_id"]) if request.args.get("course_id") else None
    held = held_by_exam(my_bookings())
    rows = []
    for e in open_exams_base():
        if q and not any(q in e[k].lower() for k in ("name", "course_code", "course_name")):
            continue
        if exam_type and e["exam_type"] != exam_type:
            continue
        if course_id and e["course_id"] != course_id:
            continue
        rows.append(personal_exam(e, held))
    return jsonify(rows)


@student_bp.get("/exams/<int:exam_id>")
@student_only
def exam_detail(exam_id):
    exam = get_or_404(Examination, exam_id, "Examination")
    bookings = my_bookings()
    if exam.status != EXAM_BOOKING_OPEN and exam.id not in {b.examination_id for b in bookings}:
        raise ApiError("Examination not found", 404)
    detail = personal_exam(exam_base(exam), held_by_exam(bookings))
    detail["instructions"] = exam.instructions
    detail["rubrics"] = exam_rubrics(exam.id)        
    return jsonify(detail)


@student_bp.get("/slots")
@student_only
def list_slots():
    bookings = my_bookings()
    held = held_by_exam(bookings)
    exam_id = int(request.args["exam_id"]) if request.args.get("exam_id") else None
    return jsonify([personal_slot(s, held, bookings) for s in open_slots_base()
                    if not exam_id or s["examination_id"] == exam_id])


@student_bp.post("/bookings")
@student_only
def book_slot():
    slot = get_or_404(ExaminationSlot, need_int(body(), "slot_id", "Slot"), "Slot")
    bookings = my_bookings()
    ok, reason = slot_state(slot_base(slot), held_by_exam(bookings), bookings)
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
