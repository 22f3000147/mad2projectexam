from datetime import datetime
from extensions import db
from models.constants import COURSE_ACTIVE, EXAM_DRAFT

# Examination <-> Examiner (many-to-many: which examiners are assigned to an exam)
exam_examiners = db.Table(
    "exam_examiners",
    db.Column("examination_id", db.Integer, db.ForeignKey("examinations.id", ondelete="CASCADE"), primary_key=True),
    db.Column("examiner_id", db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default=COURSE_ACTIVE, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    examinations = db.relationship("Examination", back_populates="course", cascade="all, delete-orphan")


class Examination(db.Model):
    __tablename__ = "examinations"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    exam_type = db.Column(db.String(30), nullable=False)       # Viva / Practical / Project Demo / Assessment
    duration_minutes = db.Column(db.Integer, nullable=False)
    max_marks = db.Column(db.Integer, nullable=False)
    instructions = db.Column(db.Text)
    slot_creation_start = db.Column(db.DateTime)
    slot_creation_end = db.Column(db.DateTime)
    booking_start = db.Column(db.DateTime)
    booking_end = db.Column(db.DateTime)
    status = db.Column(db.String(20), default=EXAM_DRAFT, nullable=False)
    results_published = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship("Course", back_populates="examinations")
    rubrics = db.relationship("ExaminationRubric", back_populates="examination", cascade="all, delete-orphan")
    slots = db.relationship("ExaminationSlot", back_populates="examination", cascade="all, delete-orphan")
    examiners = db.relationship("User", secondary=exam_examiners, backref="assigned_examinations")


class ExaminationRubric(db.Model):
    __tablename__ = "examination_rubrics"

    id = db.Column(db.Integer, primary_key=True)
    examination_id = db.Column(db.Integer, db.ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False)
    criterion_name = db.Column(db.String(150), nullable=False)
    max_marks = db.Column(db.Integer, nullable=False)
    weightage = db.Column(db.Float, default=1.0)
    description = db.Column(db.Text)

    examination = db.relationship("Examination", back_populates="rubrics")
