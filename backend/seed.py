
from extensions import db
from models import User
from models.constants import ROLE_ADMIN


def create_admin(app):
    cfg = app.config
    if User.query.filter_by(role=ROLE_ADMIN).first():
        return False
    admin = User(email=cfg["ADMIN_EMAIL"], full_name=cfg["ADMIN_NAME"], role=ROLE_ADMIN)
    admin.set_password(cfg["ADMIN_PASSWORD"])
    db.session.add(admin)
    db.session.commit()
    return True
