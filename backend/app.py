import os
from flask import Flask
from config import Config
from extensions import db, jwt
from seed import create_admin


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

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
