"""Measures API response time with the Redis cache OFF vs ON.

    python benchmark_cache.py          (Redis must be running)

It builds its own temporary database (40 exams, 320 slots, 60 students...), so your real data is untouched.
"""
import os
import random
import time

os.environ["DATABASE_URL"] = "sqlite:////tmp/emp_benchmark.db"
if os.path.exists("/tmp/emp_benchmark.db"):
    os.remove("/tmp/emp_benchmark.db")

from datetime import date, time as dtime, timedelta      
from app import create_app                               
from extensions import db                                
from models import *                                     
from utils import cache                                  

RUNS = 20


def build_data():
    random.seed(1)
    courses = [Course(code=f"C{i}", name=f"Course {i}") for i in range(5)]
    db.session.add_all(courses)
    examiners = []
    for i in range(6):
        u = User(email=f"ex{i}@x.com", full_name=f"Examiner {i}", role="examiner", password_hash="x")
        u.examiner_profile = ExaminerProfile(name=u.full_name, status="Approved")
        examiners.append(u)
    db.session.add_all(examiners)
    db.session.flush()
    exams, slots = [], []
    for i in range(40):
        e = Examination(course_id=courses[i % 5].id, name=f"Exam {i}", exam_type="Viva", duration_minutes=20,
                        max_marks=100, status="Booking Open", instructions="Bring your ID card")
        e.examiners = examiners
        e.rubrics = [ExaminationRubric(criterion_name=f"Criteria {k}", max_marks=25) for k in range(4)]
        exams.append(e)
    db.session.add_all(exams)
    db.session.flush()
    for i, e in enumerate(exams):
        for k in range(8):
            slots.append(ExaminationSlot(examination_id=e.id, examiner_id=examiners[k % 6].id,
                                         date=date.today() + timedelta(days=5 + k), start_time=dtime(9 + i % 8),
                                         end_time=dtime(10 + i % 8), max_capacity=10, available_seats=10))
    db.session.add_all(slots)
    students = [User(email=f"s{i}@x.com", full_name=f"Student {i}", role="student", password_hash="x") for i in range(60)]
    db.session.add_all(students)
    db.session.flush()
    for s in students:
        for e in random.sample(exams, 3):
            slot = random.choice([x for x in slots if x.examination_id == e.id])
            db.session.add(Booking(student_id=s.id, slot_id=slot.id, examination_id=e.id))
            slot.available_seats -= 1
    db.session.commit()


def average_ms(client, path, headers, runs=RUNS):
    start = time.perf_counter()
    for _ in range(runs):
        r = client.get(path, headers=headers)
        assert r.status_code == 200, (path, r.status_code)
    return (time.perf_counter() - start) / runs * 1000


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        build_data()
    c = app.test_client()
    login = lambda email, pw: {"Authorization": "Bearer " + c.post("/api/auth/login", json={"email": email, "password": pw}).get_json()["token"]}
    with app.app_context():
        u = User.query.filter_by(email="s0@x.com").first(); u.set_password("pw1234")
        db.session.commit()
    admin, student = login("admin@emp.com", "Admin@123"), login("s0@x.com", "pw1234")

    tests = [("Student: open exams list", "/api/student/exams", student),
             ("Student: exam schedule (slots)", "/api/student/slots", student),
             ("Student: dashboard counts", "/api/student/dashboard", student),
             ("Student: exam details + rubrics", "/api/student/exams/1", student),
             ("Admin: dashboard counts", "/api/admin/dashboard", admin),
             ("Admin: exam rubrics", "/api/admin/exams/1/rubrics", admin)]

    print(f"{'endpoint':36}{'no cache':>12}{'with cache':>13}{'faster':>9}   (avg of {RUNS} requests)")
    for name, path, headers in tests:
        cache.ENABLED = False
        slow = average_ms(c, path, headers)
        cache.ENABLED = True
        cache.clear_all()
        c.get(path, headers=headers)                      
        fast = average_ms(c, path, headers)
        print(f"{name:36}{slow:9.1f} ms{fast:10.1f} ms{slow / fast:8.1f}x")
    cache.ENABLED = True

    print("\nCache stays correct after data changes:")
    before = c.get("/api/student/slots", headers=student).get_json()
    target = next(s for s in before if s["can_book"])
    r = c.post("/api/student/bookings", json={"slot_id": target["id"]}, headers=student)
    after = c.get("/api/student/slots", headers=student)
    now = next(s for s in after.get_json() if s["id"] == target["id"])
    print(f"  slot {target['id']} seats {target['available_seats']} -> {now['available_seats']} after a booking "
          f"(booking status {r.status_code}, next response X-Cache: {after.headers.get('X-Cache')})")
    print("  cache info:", {k: v for k, v in cache.cache_info().items() if k != "keys"})
