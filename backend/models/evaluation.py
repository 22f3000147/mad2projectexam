from datetime import datetime
from extensions import db
from models.constants import EVAL_DRAFT


class Evaluation(db.Model):
    __tablename__ = "evaluations"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), unique=True, nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    total_marks = db.Column(db.Float, default=0)
    remarks = db.Column(db.Text)
    evaluation_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default=EVAL_DRAFT, nullable=False)

    booking = db.relationship("Booking", back_populates="evaluation")
    student = db.relationship("User", foreign_keys=[student_id])
    examiner = db.relationship("User", foreign_keys=[examiner_id])
    scores = db.relationship("EvaluationScore", back_populates="evaluation", cascade="all, delete-orphan")


class EvaluationScore(db.Model):
    """Marks awarded per rubric criterion."""
    __tablename__ = "evaluation_scores"

    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False)
    rubric_id = db.Column(db.Integer, db.ForeignKey("examination_rubrics.id"), nullable=False)
    awarded_marks = db.Column(db.Float, nullable=False, default=0)

    evaluation = db.relationship("Evaluation", back_populates="scores")
    rubric = db.relationship("ExaminationRubric")

    __table_args__ = (db.UniqueConstraint("evaluation_id", "rubric_id", name="uq_eval_rubric"),)
