from routes.auth import auth_bp
from routes.dashboards import dashboards_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(dashboards_bp, url_prefix="/api")
