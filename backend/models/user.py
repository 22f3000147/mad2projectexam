from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models.constants import ROLES, EXAMINER_PENDING


class User(db.Model):
    """Unified user model: role column differentiates admin / examiner / student."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    examiner_profile = db.relationship("ExaminerProfile", back_populates="user",
                                       uselist=False, cascade="all, delete-orphan")
    bookings = db.relationship("Booking", back_populates="student")

    __table_args__ = (db.CheckConstraint(f"role IN {tuple(ROLES)}", name="ck_user_role"),)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    def to_dict(self):
        return {"id": self.id, "email": self.email, "full_name": self.full_name,
                "role": self.role, "phone": self.phone, "department": self.department,
                "is_active": self.is_active}


class ExaminerProfile(db.Model):
    __tablename__ = "examiner_profiles"

    id = db.Column(db.Integer, primary_key=True)  
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                        unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    contact_details = db.Column(db.String(120))
    department = db.Column(db.String(100))
    status = db.Column(db.String(20), default=EXAMINER_PENDING, nullable=False)

    user = db.relationship("User", back_populates="examiner_profile")
