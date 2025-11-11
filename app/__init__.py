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

    allowed_origins = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:8000').split(',')
    CORS(
        app,
        origins=allowed_origins,
        supports_credentials=True,
        allow_headers=['Content-Type', 'Authorization'],
        methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    )

    with app.app_context():
        from app import models
        from app.routes import api

        app.register_blueprint(api.bp)

    return app
