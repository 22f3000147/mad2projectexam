import os
from flask import Flask, render_template, jsonify, request
from config import Config
from extensions import db, jwt
from seed import create_admin
from utils.helpers import ApiError, close_expired_bookings


def create_app(config_class=Config):
    app = Flask(__name__, static_folder="../frontend", static_url_path="/static",
                template_folder="templates")
    app.config.from_object(config_class)
    os.makedirs(os.path.join(os.path.dirname(__file__), "instance"), exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)

    import models 
    with app.app_context():
        db.create_all()         
        create_admin(app)

    from routes import register_blueprints
    register_blueprints(app)

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.before_request
    def keep_exam_status_updated():
        if request.path.startswith("/api/") and not request.path.startswith("/api/auth/"):
            close_expired_bookings()

    @app.errorhandler(ApiError)
    def api_error(err):
        return jsonify(error=err.message), err.status

    @app.errorhandler(404)
    def not_found(_):
        return jsonify(error="Not found"), 404

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
