import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
    MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", 16 * 1024 * 1024))
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}

    R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID")
    R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID")
    R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")
    R2_BUCKET_NAME = os.environ.get("R2_BUCKET_NAME", "peek")
    R2_REGION = os.environ.get("R2_REGION", "auto")
    R2_PUBLIC_DOMAIN = os.environ.get("R2_PUBLIC_DOMAIN")

    database_url = (
        os.environ.get("DATABASE_URL")
        or "postgresql://peek_user:peek_password@localhost:5432/peek_db"
    )
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = database_url

    PORT = int(os.environ.get("PORT", 5000))

    CELERY_BROKER_URL = (
        os.environ.get("CELERY_BROKER_URL")
        or os.environ.get("REDIS_URL")
        or "redis://localhost:6379/0"
    )
    CELERY_RESULT_BACKEND = (
        os.environ.get("CELERY_RESULT_BACKEND")
        or os.environ.get("REDIS_URL")
        or "redis://localhost:6379/0"
    )

    CELERYD_POOL_RESTARTS = True


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    CELERYD_POOL = os.environ.get("CELERYD_POOL", "solo")


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    CELERYD_POOL = os.environ.get("CELERYD_POOL", "prefork")
    CELERYD_CONCURRENCY = int(os.environ.get("CELERYD_CONCURRENCY", 4))


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = (
        "postgresql://peek_user:peek_password@localhost:5432/peek_test_db"
    )


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
