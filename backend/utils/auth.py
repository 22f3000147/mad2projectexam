from functools import wraps
from flask import jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models import User
from models.constants import ROLE_EXAMINER, EXAMINER_APPROVED


def login_allowed(user):
    """Return (ok, message). Deactivated users / unapproved examiners can't log in."""
    if not user.is_active:
        return False, "Account is deactivated. Contact admin."
    if user.role == ROLE_EXAMINER:
        prof = user.examiner_profile
        if not prof or prof.status != EXAMINER_APPROVED:
            return False, "Examiner account is not approved by admin."
    return True, ""


def roles_required(*roles):
    """JWT + role check. Sets g.current_user."""
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            user = db.session.get(User, int(get_jwt_identity()))
            if not user:
                return jsonify(error="User not found"), 401
            ok, msg = login_allowed(user)
            if not ok:
                return jsonify(error=msg), 403
            if roles and user.role not in roles:
                return jsonify(error="Forbidden: insufficient role"), 403
            g.current_user = user
            return fn(*args, **kwargs)
        return jwt_required()(decorated)
    return wrapper
