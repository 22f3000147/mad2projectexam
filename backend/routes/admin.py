"""All admin APIs in one file. Sections: dashboard, courses, exams, rubrics,
examiners, students, slots, bookings, search."""
import secrets
from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from extensions import db
from models import (User, ExaminerProfile, Course, Examination, ExaminationRubric,
                    ExaminationSlot, Booking, EvaluationScore)
from models.constants import *
from utils.auth import roles_required
from utils.helpers import (ApiError, body, need_text, need_int, opt_dt, need_date, need_time,
                           show_dt, get_or_404, refresh_slot, count_booked)
from utils.mail import send_mail
from utils.validators import EMAIL_RE

admin_bp = Blueprint("admin", __name__)
admin_only = roles_required(ROLE_ADMIN)

TRANSITIONS = {
    EXAM_DRAFT: [(EXAM_SLOT_CREATION, "Open slot creation")],
    EXAM_SLOT_CREATION: [(EXAM_BOOKING_OPEN, "Close slot creation & open booking"),
                         (EXAM_DRAFT, "Close slot creation")],
    EXAM_BOOKING_OPEN: [(EXAM_CLOSED, "Close booking")],
    EXAM_CLOSED: [(EXAM_BOOKING_OPEN, "Reopen booking"), (EXAM_COMPLETED, "Mark completed")],
    EXAM_COMPLETED: [],
}


def course_dict(c):
    return {"id": c.id, "code": c.code, "name": c.name, "description": c.description,
            "status": c.status, "exam_count": len(c.examinations)}


def exam_dict(e):
    return {
        "id": e.id, "course_id": e.course_id, "course_code": e.course.code,
        "course_name": e.course.name, "name": e.name, "exam_type": e.exam_type,
        "duration_minutes": e.duration_minutes, "max_marks": e.max_marks,
        "instructions": e.instructions,
        "slot_creation_start": show_dt(e.slot_creation_start),
        "slot_creation_end": show_dt(e.slot_creation_end),
        "booking_start": show_dt(e.booking_start), "booking_end": show_dt(e.booking_end),
        "status": e.status,
        "next": [{"to": to, "label": label} for to, label in TRANSITIONS[e.status]],
        "examiners": [{"id": u.id, "name": u.full_name} for u in e.examiners],
        "rubric_count": len(e.rubrics), "rubric_total": sum(r.max_marks for r in e.rubrics),
        "slot_count": len(e.slots),
        "booking_count": Booking.query.filter_by(examination_id=e.id).count(),
    }


def rubric_dict(r):
    return {"id": r.id, "examination_id": r.examination_id, "criterion_name": r.criterion_name,
            "max_marks": r.max_marks, "weightage": r.weightage, "description": r.description}


def examiner_dict(u):
    p = u.examiner_profile
    return {"id": u.id, "name": p.name, "email": u.email, "contact_details": p.contact_details,
            "department": p.department, "status": p.status,
            "slot_count": ExaminationSlot.query.filter_by(examiner_id=u.id).count(),
            "exam_count": len(u.assigned_examinations)}


def student_dict(u):
    return {"id": u.id, "name": u.full_name, "email": u.email, "phone": u.phone,
            "department": u.department, "is_active": u.is_active}


def slot_dict(s):
    return {"id": s.id, "examination_id": s.examination_id, "exam_name": s.examination.name,
            "course_code": s.examination.course.code, "examiner_id": s.examiner_id,
            "examiner_name": s.examiner.full_name, "date": s.date.isoformat(),
            "start_time": s.start_time.strftime("%H:%M"), "end_time": s.end_time.strftime("%H:%M"),
            "max_capacity": s.max_capacity, "available_seats": s.available_seats,
            "status": s.status, "meeting_link": s.meeting_link}


def booking_dict(b):
    s = b.slot
    return {"id": b.id, "student_id": b.student_id, "student_name": b.student.full_name,
            "student_email": b.student.email, "examination_id": b.examination_id,
            "exam_name": b.examination.name, "course_code": b.examination.course.code,
            "slot_id": s.id, "slot_date": s.date.isoformat(),
            "slot_start": s.start_time.strftime("%H:%M"), "slot_end": s.end_time.strftime("%H:%M"),
            "examiner_name": s.examiner.full_name, "booking_date": show_dt(b.booking_date),
            "status": b.status, "evaluated": b.evaluation is not None}


@admin_bp.get("/dashboard")
@admin_only
def dashboard():
    return jsonify(
        courses=Course.query.count(),
        examinations=Examination.query.count(),
        examiners=User.query.filter_by(role=ROLE_EXAMINER).count(),
        students=User.query.filter_by(role=ROLE_STUDENT).count(),
        slots=ExaminationSlot.query.count(),
        bookings=Booking.query.count(),
    )


def fill_course(course, data):
    code = need_text(data, "code", "Course code").upper()
    name = need_text(data, "name", "Course name")
    status = data.get("status") or COURSE_ACTIVE
    if status not in (COURSE_ACTIVE, COURSE_INACTIVE):
        raise ApiError("Invalid status")
    same = Course.query.filter(Course.code == code, Course.id != (course.id or 0)).first()
    if same:
        raise ApiError("Course code already exists", 409)
    course.code, course.name, course.status = code, name, status
    course.description = (data.get("description") or "").strip() or None


@admin_bp.get("/courses")
@admin_only
def list_courses():
    return jsonify([course_dict(c) for c in Course.query.order_by(Course.id).all()])


@admin_bp.post("/courses")
@admin_only
def create_course():
    course = Course()
    fill_course(course, body())
    db.session.add(course)
    db.session.commit()
    return jsonify(course_dict(course)), 201


@admin_bp.put("/courses/<int:course_id>")
@admin_only
def update_course(course_id):
    course = get_or_404(Course, course_id, "Course")
    fill_course(course, body())
    db.session.commit()
    return jsonify(course_dict(course))


@admin_bp.delete("/courses/<int:course_id>")
@admin_only
def delete_course(course_id):
    course = get_or_404(Course, course_id, "Course")
    has_bookings = Booking.query.join(Examination, Booking.examination_id == Examination.id) \
        .filter(Examination.course_id == course.id).first()
    if has_bookings:
        raise ApiError("This course has exam bookings. Mark it Inactive instead of deleting.", 409)
    db.session.delete(course)     
    db.session.commit()
    return jsonify(message="Course deleted")


def fill_exam(exam, data):
    course = get_or_404(Course, need_int(data, "course_id", "Course"), "Course")
    name = need_text(data, "name", "Exam name")
    exam_type = data.get("exam_type")
    if exam_type not in EXAM_TYPES:
        raise ApiError("Pick a valid exam type")
    duration = need_int(data, "duration_minutes", "Duration")
    max_marks = need_int(data, "max_marks", "Max marks")
    if exam.id and max_marks < sum(r.max_marks for r in exam.rubrics):
        raise ApiError("Max marks is lower than the total of the rubric marks")

    sc_start = opt_dt(data, "slot_creation_start", "Slot creation start")
    sc_end = opt_dt(data, "slot_creation_end", "Slot creation end")
    bk_start = opt_dt(data, "booking_start", "Booking start")
    bk_end = opt_dt(data, "booking_end", "Booking end")
    if sc_start and sc_end and sc_end <= sc_start:
        raise ApiError("Slot creation end must be after its start")
    if bk_start and bk_end and bk_end <= bk_start:
        raise ApiError("Booking end must be after its start")
    if sc_start and bk_start and bk_start < sc_start:
        raise ApiError("Booking cannot start before slot creation starts")

    exam.course_id, exam.name, exam.exam_type = course.id, name, exam_type
    exam.duration_minutes, exam.max_marks = duration, max_marks
    exam.instructions = (data.get("instructions") or "").strip() or None
    exam.slot_creation_start, exam.slot_creation_end = sc_start, sc_end
    exam.booking_start, exam.booking_end = bk_start, bk_end


@admin_bp.get("/exams")
@admin_only
def list_exams():
    return jsonify([exam_dict(e) for e in Examination.query.order_by(Examination.id).all()])


@admin_bp.post("/exams")
@admin_only
def create_exam():
    exam = Examination()
    fill_exam(exam, body())
    db.session.add(exam)
    db.session.commit()
    return jsonify(exam_dict(exam)), 201


@admin_bp.put("/exams/<int:exam_id>")
@admin_only
def update_exam(exam_id):
    exam = get_or_404(Examination, exam_id, "Examination")
    fill_exam(exam, body())
    db.session.commit()
    return jsonify(exam_dict(exam))


@admin_bp.delete("/exams/<int:exam_id>")
@admin_only
def delete_exam(exam_id):
    exam = get_or_404(Examination, exam_id, "Examination")
    if Booking.query.filter_by(examination_id=exam.id).first():
        raise ApiError("This exam already has bookings, so it cannot be deleted.", 409)
    db.session.delete(exam)
    db.session.commit()
    return jsonify(message="Examination deleted")


@admin_bp.post("/exams/<int:exam_id>/status")
@admin_only
def change_exam_status(exam_id):
    """Open/close slot creation and student booking = moving the exam status."""
    exam = get_or_404(Examination, exam_id, "Examination")
    new_status = body().get("status")
    if new_status not in [to for to, _ in TRANSITIONS[exam.status]]:
        raise ApiError(f"Cannot move from {exam.status} to {new_status}")
    if new_status == EXAM_SLOT_CREATION and not exam.examiners:
        raise ApiError("Assign at least one examiner before opening slot creation")
    if new_status == EXAM_BOOKING_OPEN and not any(s.status == SLOT_AVAILABLE for s in exam.slots):
        raise ApiError("Create at least one available slot before opening booking")
    exam.status = new_status
    db.session.commit()
    return jsonify(exam_dict(exam))


@admin_bp.put("/exams/<int:exam_id>/examiners")
@admin_only
def assign_examiners(exam_id):
    exam = get_or_404(Examination, exam_id, "Examination")
    ids = set(body().get("examiner_ids") or [])
    chosen = []
    for uid in ids:
        u = db.session.get(User, uid)
        if not u or u.role != ROLE_EXAMINER or u.examiner_profile.status != EXAMINER_APPROVED:
            raise ApiError("Only approved examiners can be assigned")
        chosen.append(u)
    for u in exam.examiners:
        if u.id not in ids and ExaminationSlot.query.filter_by(examination_id=exam.id, examiner_id=u.id).first():
            raise ApiError(f"{u.full_name} already has slots in this exam. Change the slot examiner first.", 409)
    exam.examiners = chosen
    db.session.commit()
    return jsonify(exam_dict(exam))


def fill_rubric(rubric, exam, data):
    name = need_text(data, "criterion_name", "Criteria name")
    marks = need_int(data, "max_marks", "Max marks")
    try:
        weight = float(data.get("weightage") or 1)
    except ValueError:
        raise ApiError("Weightage must be a number")
    if weight <= 0:
        raise ApiError("Weightage must be above 0")
    others = sum(r.max_marks for r in exam.rubrics if r.id != rubric.id)
    if others + marks > exam.max_marks:
        raise ApiError(f"Rubric marks would be {others + marks}, but the exam max is {exam.max_marks}")
    rubric.criterion_name, rubric.max_marks, rubric.weightage = name, marks, weight
    rubric.description = (data.get("description") or "").strip() or None


@admin_bp.get("/exams/<int:exam_id>/rubrics")
@admin_only
def list_rubrics(exam_id):
    exam = get_or_404(Examination, exam_id, "Examination")
    return jsonify(rubrics=[rubric_dict(r) for r in exam.rubrics],
                   total=sum(r.max_marks for r in exam.rubrics), exam_max=exam.max_marks)


@admin_bp.post("/exams/<int:exam_id>/rubrics")
@admin_only
def create_rubric(exam_id):
    exam = get_or_404(Examination, exam_id, "Examination")
    rubric = ExaminationRubric(examination_id=exam.id)
    fill_rubric(rubric, exam, body())
    db.session.add(rubric)
    db.session.commit()
    return jsonify(rubric_dict(rubric)), 201


@admin_bp.put("/rubrics/<int:rubric_id>")
@admin_only
def update_rubric(rubric_id):
    rubric = get_or_404(ExaminationRubric, rubric_id, "Rubric")
    fill_rubric(rubric, rubric.examination, body())
    db.session.commit()
    return jsonify(rubric_dict(rubric))


@admin_bp.delete("/rubrics/<int:rubric_id>")
@admin_only
def delete_rubric(rubric_id):
    rubric = get_or_404(ExaminationRubric, rubric_id, "Rubric")
    if EvaluationScore.query.filter_by(rubric_id=rubric.id).first():
        raise ApiError("Marks were already given using this rubric", 409)
    db.session.delete(rubric)
    db.session.commit()
    return jsonify(message="Rubric deleted")


def give_credentials(user):
    """New temporary password + mail it. If mail isn't set up, return it to the admin."""
    password = secrets.token_urlsafe(8)
    user.set_password(password)
    text = (f"Hello {user.full_name},\n\nYour examiner account for the Examination Management "
            f"Portal is ready.\nLogin: {user.email}\nTemporary password: {password}\n")
    sent = send_mail(user.email, "Your EMP examiner account", text)
    return {"mail_sent": sent, "temp_password": None if sent else password}


def read_examiner_status(data):
    status = data.get("status") or EXAMINER_APPROVED
    if status not in (EXAMINER_PENDING, EXAMINER_APPROVED, EXAMINER_DEACTIVATED):
        raise ApiError("Invalid status")
    return status


@admin_bp.get("/examiners")
@admin_only
def list_examiners():
    users = User.query.filter_by(role=ROLE_EXAMINER).order_by(User.id).all()
    return jsonify([examiner_dict(u) for u in users])


@admin_bp.post("/examiners")
@admin_only
def create_examiner():
    data = body()
    name = need_text(data, "name", "Name")
    email = need_text(data, "email", "Email").lower()
    if not EMAIL_RE.match(email):
        raise ApiError("Enter a valid email")
    if User.query.filter_by(email=email).first():
        raise ApiError("Email is already in use", 409)
    status = read_examiner_status(data)

    user = User(email=email, full_name=name, role=ROLE_EXAMINER,
                department=(data.get("department") or "").strip() or None)
    user.set_password(secrets.token_urlsafe(12))     
    user.examiner_profile = ExaminerProfile(
        name=name, status=status, department=user.department,
        contact_details=(data.get("contact_details") or "").strip() or None)
    db.session.add(user)
    db.session.flush()
    creds = give_credentials(user) if status == EXAMINER_APPROVED else None
    db.session.commit()
    return jsonify(examiner=examiner_dict(user), credentials=creds), 201


@admin_bp.put("/examiners/<int:user_id>")
@admin_only
def update_examiner(user_id):
    user = get_or_404(User, user_id, "Examiner")
    if user.role != ROLE_EXAMINER:
        raise ApiError("Examiner not found", 404)
    data = body()
    profile = user.examiner_profile
    old_status = profile.status
    profile.name = user.full_name = need_text(data, "name", "Name")
    profile.contact_details = (data.get("contact_details") or "").strip() or None
    profile.department = user.department = (data.get("department") or "").strip() or None
    profile.status = read_examiner_status(data)
    creds = None
    if profile.status == EXAMINER_APPROVED and old_status != EXAMINER_APPROVED:
        creds = give_credentials(user)
    db.session.commit()
    return jsonify(examiner=examiner_dict(user), credentials=creds)


@admin_bp.delete("/examiners/<int:user_id>")
@admin_only
def delete_examiner(user_id):
    user = get_or_404(User, user_id, "Examiner")
    if user.role != ROLE_EXAMINER:
        raise ApiError("Examiner not found", 404)
    if ExaminationSlot.query.filter_by(examiner_id=user.id).first():
        raise ApiError("This examiner has slots. Deactivate the examiner instead.", 409)
    user.assigned_examinations = []
    db.session.delete(user)
    db.session.commit()
    return jsonify(message="Examiner removed")


@admin_bp.get("/students")
@admin_only
def list_students():
    query = User.query.filter_by(role=ROLE_STUDENT)
    q = request.args.get("q", "").strip()
    if q:
        conditions = [User.full_name.ilike(f"%{q}%"), User.email.ilike(f"%{q}%")]
        if q.isdigit():
            conditions.append(User.id == int(q))
        query = query.filter(or_(*conditions))
    return jsonify([student_dict(u) for u in query.order_by(User.id).all()])


@admin_bp.put("/students/<int:user_id>/active")
@admin_only
def set_student_active(user_id):
    user = get_or_404(User, user_id, "Student")
    if user.role != ROLE_STUDENT:
        raise ApiError("Student not found", 404)
    user.is_active = bool(body().get("is_active"))
    db.session.commit()
    return jsonify(student_dict(user))


def overlaps(slot_id, examiner_id, day, start, end):
    others = ExaminationSlot.query.filter(
        ExaminationSlot.examiner_id == examiner_id, ExaminationSlot.date == day,
        ExaminationSlot.status != SLOT_CANCELLED, ExaminationSlot.id != (slot_id or 0)).all()
    return any(start < o.end_time and end > o.start_time for o in others)


def fill_slot(slot, data):
    new = slot.id is None
    if new:
        exam = get_or_404(Examination, need_int(data, "examination_id", "Exam"), "Examination")
    else:
        exam = slot.examination
        if slot.status == SLOT_COMPLETED:
            raise ApiError("Completed slots cannot be edited")

    examiner_id = need_int(data, "examiner_id", "Examiner")
    if examiner_id not in [u.id for u in exam.examiners]:
        raise ApiError("This examiner is not assigned to the exam")
    day = need_date(data, "date", "Date")
    start = need_time(data, "start_time", "Start time")
    end = need_time(data, "end_time", "End time")
    if end <= start:
        raise ApiError("End time must be after start time")
    capacity = need_int(data, "max_capacity", "Max capacity")
    if overlaps(slot.id, examiner_id, day, start, end):
        raise ApiError("This examiner already has a slot at that time", 409)

    booked = count_booked(slot)
    if capacity < booked:
        raise ApiError(f"{booked} students are already booked, so capacity cannot be lower")
    status = data.get("status") or SLOT_AVAILABLE
    if status not in (SLOT_AVAILABLE, SLOT_CANCELLED):
        raise ApiError("Status can only be Available or Cancelled")
    if status == SLOT_CANCELLED and booked:
        raise ApiError("Reschedule the booked students before cancelling this slot")

    slot.examination_id, slot.examiner_id = exam.id, examiner_id
    slot.date, slot.start_time, slot.end_time = day, start, end
    slot.max_capacity = capacity
    slot.meeting_link = (data.get("meeting_link") or "").strip() or None
    slot.status = status
    refresh_slot(slot)


@admin_bp.get("/slots")
@admin_only
def list_slots():
    query = ExaminationSlot.query
    if request.args.get("exam_id"):
        query = query.filter_by(examination_id=int(request.args["exam_id"]))
    if request.args.get("open"):
        query = query.filter(ExaminationSlot.status == SLOT_AVAILABLE, ExaminationSlot.available_seats > 0)
    slots = query.order_by(ExaminationSlot.date, ExaminationSlot.start_time).all()
    return jsonify([slot_dict(s) for s in slots])


@admin_bp.post("/slots")
@admin_only
def create_slot():
    slot = ExaminationSlot(available_seats=0)
    fill_slot(slot, body())
    db.session.add(slot)
    db.session.commit()
    return jsonify(slot_dict(slot)), 201


@admin_bp.put("/slots/<int:slot_id>")
@admin_only
def update_slot(slot_id):
    """Also used to change the assigned examiner (examiner_id field)."""
    slot = get_or_404(ExaminationSlot, slot_id, "Slot")
    fill_slot(slot, body())
    db.session.commit()
    return jsonify(slot_dict(slot))


@admin_bp.delete("/slots/<int:slot_id>")
@admin_only
def delete_slot(slot_id):
    slot = get_or_404(ExaminationSlot, slot_id, "Slot")
    if Booking.query.filter_by(slot_id=slot.id).first():
        raise ApiError("This slot has bookings. Cancel the slot instead of deleting it.", 409)
    db.session.delete(slot)
    db.session.commit()
    return jsonify(message="Slot deleted")


@admin_bp.get("/bookings")
@admin_only
def list_bookings():
    query = Booking.query.join(User, Booking.student_id == User.id)
    if request.args.get("exam_id"):
        query = query.filter(Booking.examination_id == int(request.args["exam_id"]))
    q = request.args.get("q", "").strip()
    if q:
        conditions = [User.full_name.ilike(f"%{q}%"), User.email.ilike(f"%{q}%")]
        if q.isdigit():
            conditions.append(User.id == int(q))
        query = query.filter(or_(*conditions))
    return jsonify([booking_dict(b) for b in query.order_by(Booking.id.desc()).all()])


@admin_bp.put("/bookings/<int:booking_id>/reschedule")
@admin_only
def reschedule_booking(booking_id):
    booking = get_or_404(Booking, booking_id, "Booking")
    new_slot = get_or_404(ExaminationSlot, need_int(body(), "slot_id", "New slot"), "Slot")
    if booking.status != BOOKING_BOOKED:
        raise ApiError("Only active bookings can be rescheduled")
    if booking.evaluation:
        raise ApiError("This student is already evaluated")
    if new_slot.id == booking.slot_id:
        raise ApiError("Pick a different slot")
    if new_slot.examination_id != booking.examination_id:
        raise ApiError("The new slot must belong to the same exam")
    if new_slot.status != SLOT_AVAILABLE or new_slot.available_seats < 1:
        raise ApiError("That slot is full or not available")
    old_slot = booking.slot
    booking.slot = new_slot
    db.session.flush()
    refresh_slot(old_slot)
    refresh_slot(new_slot)
    db.session.commit()
    return jsonify(booking_dict(booking))


@admin_bp.get("/search")
@admin_only
def search():
    q = request.args.get("q", "").strip()
    if not q:
        raise ApiError("Type something to search")
    like = f"%{q}%"
    number = int(q) if q.isdigit() else None

    def with_id(conditions, id_column):
        return conditions + ([id_column == number] if number is not None else [])

    students = User.query.filter(User.role == ROLE_STUDENT, or_(*with_id(
        [User.full_name.ilike(like), User.email.ilike(like)], User.id))).limit(20).all()
    examiners = User.query.filter(User.role == ROLE_EXAMINER, or_(*with_id(
        [User.full_name.ilike(like), User.email.ilike(like)], User.id))).limit(20).all()
    exams = Examination.query.join(Course).filter(or_(*with_id(
        [Examination.name.ilike(like), Course.code.ilike(like)], Examination.id))).limit(20).all()
    bookings = Booking.query.join(User, Booking.student_id == User.id).filter(or_(*with_id(
        [User.full_name.ilike(like)], Booking.id))).limit(20).all()
    return jsonify(students=[student_dict(u) for u in students],
                   examiners=[examiner_dict(u) for u in examiners],
                   exams=[exam_dict(e) for e in exams],
                   bookings=[booking_dict(b) for b in bookings])
