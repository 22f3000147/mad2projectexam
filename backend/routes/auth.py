from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import create_access_token
from extensions import db
from models import User
from models.constants import ROLE_STUDENT, ROLE_ADMIN
from utils.auth import roles_required, login_allowed
from utils.validators import validate_registration

auth_bp = Blueprint("auth", __name__)

DASHBOARD_PATH = {"admin": "/admin", "examiner": "/examiner", "student": "/student"}


@auth_bp.post("/register")
def register():
    """Student self-registration ONLY. Role is forced server-side."""
    data = request.get_json(silent=True) or {}
    errors = validate_registration(data)
    if errors:
        return jsonify(error="Validation failed", fields=errors), 400
    email = data["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        return jsonify(error="Validation failed", fields={"email": "Email already registered"}), 409

    user = User(email=email, full_name=data["full_name"].strip(), role=ROLE_STUDENT,
                phone=(data.get("phone") or "").strip() or None,
                department=(data.get("department") or "").strip() or None)
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()
    return jsonify(message="Registered successfully. Please log in.", user=user.to_dict()), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(data.get("password") or ""):
        return jsonify(error="Invalid email or password"), 401
    ok, msg = login_allowed(user)
    if not ok:
        return jsonify(error=msg), 403
    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify(token=token, user=user.to_dict(), redirect=DASHBOARD_PATH[user.role])


@auth_bp.get("/me")
@roles_required()         
def me():
    return jsonify(user=g.current_user.to_dict())
