from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.examiner import examiner_bp
from routes.dashboards import dashboards_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(examiner_bp, url_prefix="/api/examiner")
    app.register_blueprint(dashboards_bp, url_prefix="/api")
