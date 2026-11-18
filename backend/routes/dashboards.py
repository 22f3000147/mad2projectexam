"""Role-gated dashboard endpoints. Real data is added in Milestones 3-5."""
from flask import Blueprint, jsonify, g
from utils.auth import roles_required
from models.constants import ROLE_EXAMINER, ROLE_STUDENT

dashboards_bp = Blueprint("dashboards", __name__)


@dashboards_bp.get("/examiner/dashboard")
@roles_required(ROLE_EXAMINER)
def examiner_dashboard():
    return jsonify(message=f"Welcome Examiner {g.current_user.full_name}")


@dashboards_bp.get("/student/dashboard")
@roles_required(ROLE_STUDENT)
def student_dashboard():
    return jsonify(message=f"Welcome Student {g.current_user.full_name}")
