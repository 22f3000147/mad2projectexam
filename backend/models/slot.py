from datetime import datetime
from sqlalchemy import text
from extensions import db
from models.constants import SLOT_AVAILABLE, BOOKING_BOOKED


class ExaminationSlot(db.Model):
    __tablename__ = "examination_slots"

    id = db.Column(db.Integer, primary_key=True)
    examination_id = db.Column(db.Integer, db.ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default=SLOT_AVAILABLE, nullable=False)
    meeting_link = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    examination = db.relationship("Examination", back_populates="slots")
    examiner = db.relationship("User", foreign_keys=[examiner_id])
    bookings = db.relationship("Booking", back_populates="slot")

    __table_args__ = (
        db.CheckConstraint("max_capacity > 0", name="ck_slot_capacity_pos"),
        db.CheckConstraint("available_seats >= 0 AND available_seats <= max_capacity", name="ck_slot_seats_range"),
    )


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey("examination_slots.id"), nullable=False)
    
    examination_id = db.Column(db.Integer, db.ForeignKey("examinations.id"), nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default=BOOKING_BOOKED, nullable=False)

    student = db.relationship("User", back_populates="bookings")
    slot = db.relationship("ExaminationSlot", back_populates="bookings")
    examination = db.relationship("Examination")
    evaluation = db.relationship("Evaluation", back_populates="booking", uselist=False)

    __table_args__ = (
       
        db.Index("uq_active_booking", "student_id", "examination_id", unique=True,
                 sqlite_where=text("status = 'Booked'")),
    )
