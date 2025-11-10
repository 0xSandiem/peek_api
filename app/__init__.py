import os

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from config import config_by_name

db = SQLAlchemy()


def create_app(config_name=None):
    app = Flask(__name__)

    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    db.init_app(app)
    CORS(app)

    with app.app_context():
        from app import models
        from app.routes import api

        app.register_blueprint(api.bp)

        db.create_all()

    return app
