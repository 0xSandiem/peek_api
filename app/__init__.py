import logging
import os

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from config import config_by_name

db = SQLAlchemy()
logger = logging.getLogger(__name__)


def validate_r2_config(app):
    """Validate R2 configuration on startup."""
    required_vars = [
        "R2_ACCOUNT_ID",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_BUCKET_NAME",
    ]

    missing_vars = [var for var in required_vars if not app.config.get(var)]

    if missing_vars:
        logger.warning(
            f"R2 storage is not fully configured. Missing: {', '.join(missing_vars)}. "
            "Image upload functionality may not work properly."
        )
        return False

    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError

        s3_client = boto3.client(
            "s3",
            endpoint_url=f"https://{app.config['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
            aws_access_key_id=app.config["R2_ACCESS_KEY_ID"],
            aws_secret_access_key=app.config["R2_SECRET_ACCESS_KEY"],
            region_name=app.config.get("R2_REGION", "auto"),
        )

        s3_client.head_bucket(Bucket=app.config["R2_BUCKET_NAME"])
        logger.info(
            f"R2 storage configured successfully. Bucket: {app.config['R2_BUCKET_NAME']}"
        )
        return True

    except NoCredentialsError:
        logger.error(
            "R2 credentials are invalid. Please check R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY."
        )
        return False
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "404":
            logger.error(
                f"R2 bucket '{app.config['R2_BUCKET_NAME']}' does not exist. Please create it first."
            )
        elif error_code == "403":
            logger.error(
                f"Access denied to R2 bucket '{app.config['R2_BUCKET_NAME']}'. Check permissions."
            )
        else:
            logger.error(f"R2 connection error: {error_code} - {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error validating R2 configuration: {str(e)}")
        return False


def create_app(config_name=None):
    app = Flask(__name__)

    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    db.init_app(app)

    allowed_origins = os.environ.get(
        "CORS_ALLOWED_ORIGINS", "http://localhost:8000,https://peek.cx"
    ).split(",")
    CORS(
        app,
        origins=allowed_origins,
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    with app.app_context():
        from app import models  # noqa: F401
        from app.routes import api

        app.register_blueprint(api.bp)

        validate_r2_config(app)

    return app
