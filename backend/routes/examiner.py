"""Examiner APIs: assigned exams, own slots, booked students, evaluation (rubric marks)."""
from datetime import datetime
from flask import Blueprint, jsonify, request, g
from sqlalchemy import or_
from extensions import db
from models import User, Examination, ExaminationSlot, Booking, Evaluation, EvaluationScore
from models.constants import *
from utils.auth import roles_required
from utils.helpers import (ApiError, body, need_int, need_date, need_time, show_dt,
                           get_or_404, refresh_slot, count_booked, finish_exam)
from routes.admin import slot_dict, overlaps

examiner_bp = Blueprint("examiner", __name__)
examiner_only = roles_required(ROLE_EXAMINER)


def my_exam(exam_id):
    exam = get_or_404(Examination, exam_id, "Examination")
    if g.current_user not in exam.examiners:
        raise ApiError("This exam is not assigned to you", 403)
    return exam


def my_slot(slot_id):
    slot = get_or_404(ExaminationSlot, slot_id, "Slot")
    if slot.examiner_id != g.current_user.id:
        raise ApiError("This is not your slot", 403)
    return slot


def my_booking(booking_id):
    booking = get_or_404(Booking, booking_id, "Booking")
    if booking.slot.examiner_id != g.current_user.id:
        raise ApiError("This student is not booked in your slot", 403)
    return booking


def creation_state(exam):
    """Can the examiner create slots right now? -> (True/False, reason)"""
    if exam.status != EXAM_SLOT_CREATION:
        return False, "Slot creation is not open"
    now = datetime.now()          # admin enters timelines in local time
    if exam.slot_creation_start and now < exam.slot_creation_start:
        return False, f"Slot creation opens {exam.slot_creation_start:%d %b %H:%M}"
    if exam.slot_creation_end and now > exam.slot_creation_end:
        return False, f"Slot creation closed {exam.slot_creation_end:%d %b %H:%M}"
    return True, ""


def edit_state(slot):
    """Slots can be changed/removed only before student booking starts."""
    if slot.examination.status not in (EXAM_DRAFT, EXAM_SLOT_CREATION):
        return False, "Student booking has started, slot is locked"
    if Booking.query.filter_by(slot_id=slot.id).first():
        return False, "Students are already booked in this slot"
    return True, ""


def my_bookings_query():
    return (Booking.query
            .join(ExaminationSlot, Booking.slot_id == ExaminationSlot.id)
            .join(User, Booking.student_id == User.id)
            .filter(ExaminationSlot.examiner_id == g.current_user.id))


def exam_dict(e):
    me = g.current_user
    can_create, note = creation_state(e)
    mine = [s for s in e.slots if s.examiner_id == me.id]
    bookings = [b for s in mine for b in s.bookings]
    return {
        "id": e.id, "course_code": e.course.code, "course_name": e.course.name, "name": e.name,
        "exam_type": e.exam_type, "duration_minutes": e.duration_minutes, "max_marks": e.max_marks,
        "instructions": e.instructions, "status": e.status, "rubric_count": len(e.rubrics),
        "slot_creation_start": show_dt(e.slot_creation_start), "slot_creation_end": show_dt(e.slot_creation_end),
        "booking_start": show_dt(e.booking_start), "booking_end": show_dt(e.booking_end),
        "can_create_slots": can_create, "slot_note": note,
        "my_slots": len(mine),
        "my_students": len([b for b in bookings if b.status in (BOOKING_BOOKED, BOOKING_COMPLETED)]),
        "pending": len([b for b in bookings if b.status == BOOKING_BOOKED]),
    }


def my_slot_dict(s):
    d = slot_dict(s)
    d["booked"] = count_booked(s)
    d["can_edit"], d["lock_reason"] = edit_state(s)
    return d


def my_booking_dict(b):
    s = b.slot
    ev = b.evaluation
    return {"id": b.id, "slot_id": s.id, "student_id": b.student_id, "student_name": b.student.full_name,
            "student_email": b.student.email, "examination_id": b.examination_id,
            "exam_name": b.examination.name, "course_code": b.examination.course.code,
            "slot_date": s.date.isoformat(), "slot_start": s.start_time.strftime("%H:%M"),
            "slot_end": s.end_time.strftime("%H:%M"), "status": b.status,
            "eval_status": ev.status if ev else "Pending",
            "marks": ev.total_marks if ev and ev.status != EVAL_DRAFT else None}


@examiner_bp.get("/dashboard")
@examiner_only
def dashboard():
    me = g.current_user
    holding = my_bookings_query().filter(Booking.status.in_((BOOKING_BOOKED, BOOKING_COMPLETED)))
    return jsonify(
        assigned_exams=len(me.assigned_examinations),
        slots=ExaminationSlot.query.filter_by(examiner_id=me.id).count(),
        students_booked=holding.count(),
        pending_evaluations=my_bookings_query().filter(Booking.status == BOOKING_BOOKED).count(),
    )


@examiner_bp.get("/exams")
@examiner_only
def list_exams():
    exams = sorted(g.current_user.assigned_examinations, key=lambda e: e.id)
    return jsonify([exam_dict(e) for e in exams])


@examiner_bp.post("/exams/<int:exam_id>/complete")
@examiner_only
def complete_exam(exam_id):
    exam = my_exam(exam_id)
    if exam.status != EXAM_CLOSED:
        raise ApiError("The exam can be completed only after booking is closed")
    finish_exam(exam)
    db.session.commit()
    return jsonify(exam_dict(exam))


def fill_my_slot(slot, exam, data):
    day = need_date(data, "date", "Date")
    start = need_time(data, "start_time", "Start time")
    end = need_time(data, "end_time", "End time")
    if end <= start:
        raise ApiError("End time must be after start time")
    capacity = need_int(data, "max_capacity", "Max capacity")
    if overlaps(slot.id, g.current_user.id, day, start, end):
        raise ApiError("You already have a slot at that time", 409)
    booked = count_booked(slot)
    if capacity < booked:
        raise ApiError(f"{booked} students are already booked, capacity cannot be lower")
    slot.examination_id, slot.examiner_id = exam.id, g.current_user.id
    slot.date, slot.start_time, slot.end_time, slot.max_capacity = day, start, end, capacity
    slot.meeting_link = (data.get("meeting_link") or "").strip() or None
    slot.status = SLOT_AVAILABLE
    refresh_slot(slot)


@examiner_bp.get("/slots")
@examiner_only
def list_slots():
    query = ExaminationSlot.query.filter_by(examiner_id=g.current_user.id)
    if request.args.get("exam_id"):
        query = query.filter_by(examination_id=int(request.args["exam_id"]))
    slots = query.order_by(ExaminationSlot.date, ExaminationSlot.start_time).all()
    return jsonify([my_slot_dict(s) for s in slots])


@examiner_bp.post("/slots")
@examiner_only
def create_slot():
    data = body()
    exam = my_exam(need_int(data, "examination_id", "Exam"))
    ok, reason = creation_state(exam)
    if not ok:
        raise ApiError(reason, 403)
    slot = ExaminationSlot(available_seats=0)
    fill_my_slot(slot, exam, data)
    db.session.add(slot)
    db.session.commit()
    return jsonify(my_slot_dict(slot)), 201


@examiner_bp.put("/slots/<int:slot_id>")
@examiner_only
def update_slot(slot_id):
    slot = my_slot(slot_id)
    ok, reason = edit_state(slot)
    if not ok:
        raise ApiError(reason, 403)
    fill_my_slot(slot, slot.examination, body())
    db.session.commit()
    return jsonify(my_slot_dict(slot))


@examiner_bp.delete("/slots/<int:slot_id>")
@examiner_only
def delete_slot(slot_id):
    slot = my_slot(slot_id)
    ok, reason = edit_state(slot)
    if not ok:
        raise ApiError(reason, 403)
    db.session.delete(slot)
    db.session.commit()
    return jsonify(message="Slot removed")


@examiner_bp.get("/bookings")
@examiner_only
def list_bookings():
    query = my_bookings_query().filter(Booking.status != BOOKING_CANCELLED)
    if request.args.get("exam_id"):
        query = query.filter(Booking.examination_id == int(request.args["exam_id"]))
    q = request.args.get("q", "").strip()
    if q:
        conditions = [User.full_name.ilike(f"%{q}%"), User.email.ilike(f"%{q}%")]
        if q.isdigit():
            conditions.append(User.id == int(q))
        query = query.filter(or_(*conditions))
    rows = query.order_by(ExaminationSlot.date, ExaminationSlot.start_time, Booking.id).all()
    return jsonify([my_booking_dict(b) for b in rows])


def evaluation_dict(booking):
    ev = booking.evaluation
    given = {sc.rubric_id: sc.awarded_marks for sc in ev.scores} if ev else {}
    exam = booking.examination
    return {
        "booking": my_booking_dict(booking),
        "exam_max": exam.max_marks,
        "rubrics": [{"id": r.id, "criterion_name": r.criterion_name, "max_marks": r.max_marks,
                     "weightage": r.weightage, "description": r.description,
                     "awarded": given.get(r.id)} for r in exam.rubrics],
        "remarks": ev.remarks if ev else "",
        "status": ev.status if ev else "Pending",
        "total": ev.total_marks if ev else 0,
        "locked": bool(ev and ev.status == EVAL_PUBLISHED) or exam.status not in (EXAM_BOOKING_OPEN, EXAM_CLOSED),
    }


@examiner_bp.get("/bookings/<int:booking_id>/evaluation")
@examiner_only
def get_evaluation(booking_id):
    return jsonify(evaluation_dict(my_booking(booking_id)))


@examiner_bp.put("/bookings/<int:booking_id>/evaluation")
@examiner_only
def save_evaluation(booking_id):
    """Save marks as draft, or submit (submit needs every criteria scored + remarks)."""
    booking = my_booking(booking_id)
    exam = booking.examination
    data = body()
    if booking.status == BOOKING_CANCELLED:
        raise ApiError("This booking was cancelled")
    if exam.status not in (EXAM_BOOKING_OPEN, EXAM_CLOSED):
        raise ApiError("Evaluation is not allowed while the exam is " + exam.status)
    if not exam.rubrics:
        raise ApiError("Admin has not added rubric criteria for this exam yet")

    ev = booking.evaluation
    if ev and ev.status == EVAL_PUBLISHED:
        raise ApiError("Results are already published", 403)
    if not ev:
        ev = Evaluation(booking_id=booking.id, student_id=booking.student_id,
                        examiner_id=g.current_user.id, status=EVAL_DRAFT)
        db.session.add(ev)
    submit = bool(data.get("submit")) or ev.status == EVAL_SUBMITTED

    rubrics = {r.id: r for r in exam.rubrics}
    marks = {}
    for item in data.get("scores") or []:
        raw = item.get("awarded_marks")
        if raw is None or raw == "":
            continue
        rubric = rubrics.get(item.get("rubric_id"))
        if not rubric:
            raise ApiError("Unknown criteria for this exam")
        try:
            value = float(raw)
        except (TypeError, ValueError):
            raise ApiError(f"Marks for {rubric.criterion_name} must be a number")
        if value < 0 or value > rubric.max_marks:
            raise ApiError(f"Marks for {rubric.criterion_name} must be between 0 and {rubric.max_marks}")
        marks[rubric.id] = value

    remarks = (data.get("remarks") or "").strip()
    if submit:
        missing = [r.criterion_name for r in exam.rubrics if r.id not in marks]
        if missing:
            raise ApiError("Give marks for: " + ", ".join(missing))
        if not remarks:
            raise ApiError("Remarks are required to submit")

    existing = {sc.rubric_id: sc for sc in ev.scores}
    for rid, value in marks.items():
        if rid in existing:
            existing[rid].awarded_marks = value
        else:
            ev.scores.append(EvaluationScore(rubric_id=rid, awarded_marks=value))
    for rid, sc in existing.items():          # a cleared box removes that score
        if rid not in marks:
            ev.scores.remove(sc)
    ev.remarks = remarks or None
    ev.total_marks = sum(marks.values())
    ev.evaluation_date = datetime.utcnow()
    if submit:
        ev.status = EVAL_SUBMITTED
        booking.status = BOOKING_COMPLETED
    db.session.commit()
    return jsonify(evaluation_dict(booking))


@examiner_bp.get("/search")
@examiner_only
def search():
    q = request.args.get("q", "").strip()
    if not q:
        raise ApiError("Type something to search")
    low = q.lower()
    exams = [e for e in g.current_user.assigned_examinations
             if low in e.name.lower() or low in e.course.code.lower() or q == str(e.id)]
    slots = [s for s in ExaminationSlot.query.filter_by(examiner_id=g.current_user.id).all()
             if q == str(s.id) or low in s.examination.name.lower() or low in s.date.isoformat()]
    conditions = [User.full_name.ilike(f"%{q}%"), User.email.ilike(f"%{q}%")]
    if q.isdigit():
        conditions.append(User.id == int(q))
        conditions.append(Booking.id == int(q))
    bookings = my_bookings_query().filter(Booking.status != BOOKING_CANCELLED, or_(*conditions)).limit(20).all()
    return jsonify(exams=[exam_dict(e) for e in exams], slots=[my_slot_dict(s) for s in slots[:20]],
                   bookings=[my_booking_dict(b) for b in bookings])
