"""Background jobs: daily reminders, monthly report, CSV export."""
import csv
import html
import os
from collections import Counter
from datetime import date, datetime, timedelta
from celery_app import celery
from config import Config
from models import User, Booking, ExaminationSlot, Evaluation
from models.constants import (ROLE_ADMIN, BOOKING_BOOKED, BOOKING_COMPLETED, BOOKING_CANCELLED,
                              EVAL_SUBMITTED, EVAL_PUBLISHED)
from utils.mail import send_mail
from utils.notify import post_webhook


def reminder_text(booking):
    slot, exam = booking.slot, booking.examination
    lines = [f"Hello {booking.student.full_name},", "",
             "This is a reminder for your upcoming examination.",
             f"Examination: {exam.name} ({exam.course.code})",
             f"Date and time: {slot.date} {slot.start_time:%H:%M} - {slot.end_time:%H:%M}",
             f"Examiner: {slot.examiner.full_name}",
             f"Instructions: {exam.instructions or 'None'}"]
    if slot.meeting_link:
        lines.append(f"Meeting link: {slot.meeting_link}")
    return "\n".join(lines)


@celery.task(name="tasks.send_daily_reminders")
def send_daily_reminders():
    """Remind every student who has a booked exam today (not started yet) or tomorrow."""
    now = datetime.now()
    days = (now.date(), now.date() + timedelta(days=1))
    bookings = (Booking.query.join(ExaminationSlot, Booking.slot_id == ExaminationSlot.id)
                .filter(Booking.status == BOOKING_BOOKED, ExaminationSlot.date.in_(days)).all())
    reminders = emailed = webhooks = 0
    for b in bookings:
        if datetime.combine(b.slot.date, b.slot.start_time) <= now:
            continue
        text = reminder_text(b)
        if send_mail(b.student.email, f"Reminder: {b.examination.name} on {b.slot.date}", text):
            emailed += 1
        if post_webhook(Config.GCHAT_WEBHOOK_URL, text):
            webhooks += 1
        reminders += 1
    return {"reminders": reminders, "emailed": emailed, "webhooks": webhooks}


def month_bounds(year, month):
    first = date(year, month, 1)
    return first, date(year + (month == 12), month % 12 + 1, 1)


def collect_stats(first, next_first):
    in_month = (ExaminationSlot.date >= first, ExaminationSlot.date < next_first)
    rows = Booking.query.join(ExaminationSlot, Booking.slot_id == ExaminationSlot.id).filter(*in_month)
    completed = rows.filter(Booking.status == BOOKING_COMPLETED).all()
    evals = (Evaluation.query.join(Booking, Evaluation.booking_id == Booking.id)
             .join(ExaminationSlot, Booking.slot_id == ExaminationSlot.id)
             .filter(*in_month, Evaluation.status.in_((EVAL_SUBMITTED, EVAL_PUBLISHED))).all())
    top = Counter(ev.examiner.full_name for ev in evals).most_common(5)
    return {
        "exams_conducted": len({b.examination_id for b in completed}),
        "participants": len({b.student_id for b in completed}),
        "examiners_involved": len({b.slot.examiner_id for b in completed}),
        "students_evaluated": len(evals),
        "completed_bookings": len(completed),
        "pending_evaluations": rows.filter(Booking.status == BOOKING_BOOKED).count(),
        "cancelled_bookings": rows.filter(Booking.status == BOOKING_CANCELLED).count(),
        "top_examiners": [{"name": n, "evaluations": c} for n, c in top],
    }


def report_html(label, stats):
    e = html.escape
    items = [("Examinations conducted", stats["exams_conducted"]), ("Participating students", stats["participants"]),
             ("Examiners involved", stats["examiners_involved"]), ("Students evaluated", stats["students_evaluated"]),
             ("Completed bookings", stats["completed_bookings"]), ("Pending evaluations", stats["pending_evaluations"]),
             ("Cancelled bookings", stats["cancelled_bookings"])]
    rows = "".join(f"<tr><td style='padding:6px 12px;border:1px solid #ddd'>{e(k)}</td>"
                   f"<td style='padding:6px 12px;border:1px solid #ddd'><b>{v}</b></td></tr>" for k, v in items)
    top = "".join(f"<li>{e(t['name'])} - {t['evaluations']} evaluations</li>" for t in stats["top_examiners"]) \
        or "<li>No evaluations this month</li>"
    return (f"<html><body style='font-family:Arial,sans-serif'><h2>Examination report - {e(label)}</h2>"
            f"<table style='border-collapse:collapse'>{rows}</table><h3>Most active examiners</h3><ul>{top}</ul>"
            f"<p style='color:#777'>Generated {datetime.now():%d %b %Y %H:%M}</p></body></html>")


@celery.task(name="tasks.send_monthly_report")
def send_monthly_report(month=None):
    """month = 'YYYY-MM'. Default (scheduled run): the month that just ended."""
    if month:
        year, mon = int(month[:4]), int(month[5:7])
    else:
        last = date.today().replace(day=1) - timedelta(days=1)
        year, mon = last.year, last.month
    first, next_first = month_bounds(year, mon)
    stats = collect_stats(first, next_first)
    label = f"{first:%B %Y}"
    page = report_html(label, stats)

    os.makedirs(Config.REPORT_DIR, exist_ok=True)
    filename = f"monthly_{year}_{mon:02d}.html"
    with open(os.path.join(Config.REPORT_DIR, filename), "w", encoding="utf-8") as f:
        f.write(page)
    admin = User.query.filter_by(role=ROLE_ADMIN).first()
    mailed = send_mail(admin.email, f"Monthly examination report - {label}",
                       f"Examination report for {label}: see the HTML version.", html=page)
    return {"month": f"{year}-{mon:02d}", "label": label, "file": filename, "emailed": mailed, "stats": stats}


def safe_cell(value):
    """Stop spreadsheet formula injection (cells starting with = + - @)."""
    text = "" if value is None else str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@") else text


@celery.task(bind=True, name="tasks.export_history_csv")
def export_history_csv(self, student_id):
    student = User.query.get(student_id)
    bookings = (Booking.query.join(ExaminationSlot, Booking.slot_id == ExaminationSlot.id)
                .filter(Booking.student_id == student_id)
                .order_by(ExaminationSlot.date, ExaminationSlot.start_time).all())
    os.makedirs(Config.EXPORT_DIR, exist_ok=True)
    filename = f"student_{student_id}_{self.request.id}.csv"
    with open(os.path.join(Config.EXPORT_DIR, filename), "w", newline="", encoding="utf-8") as f:
        out = csv.writer(f)
        out.writerow(["Student ID", "Examination Name", "Course", "Examination Date", "Examiner",
                      "Marks Obtained", "Booking Status"])
        for b in bookings:
            ev = b.evaluation
            marks = ev.total_marks if ev and ev.status == EVAL_PUBLISHED else ""     
            out.writerow([student_id, safe_cell(b.examination.name), safe_cell(b.examination.course.name),
                          f"{b.slot.date} {b.slot.start_time:%H:%M}", safe_cell(b.slot.examiner.full_name),
                          marks, b.status])
    send_mail(student.email, "Your exam history export is ready",
              f"Hello {student.full_name},\n\nYour examination history CSV ({len(bookings)} rows) is ready. "
              "Open your dashboard to download it.")
    return {"file": filename, "rows": len(bookings)}
