import os

from celery import Celery
from flask import Flask

from app import db
from app.models import Image, Insights
from app.services.annotation_service import AnnotationService
from app.services.cv_service import CVService
from config import config_by_name


def make_celery(app=None):
    if app is None:
        app = Flask(__name__)
        config_name = os.environ.get("FLASK_ENV", "development")
        app.config.from_object(config_by_name[config_name])

        with app.app_context():
            db.init_app(app)

    celery = Celery(
        app.import_name,
        broker=app.config["CELERY_BROKER_URL"],
        backend=app.config["CELERY_RESULT_BACKEND"],
    )

    celery.conf.update(app.config)
    celery.flask_app = app

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery()


@celery.task(name="tasks.celery_tasks.process_image_async")
def process_image_async(image_id):
    image = db.session.get(Image, image_id)

    if not image:
        return {"error": "Image not found"}

    insights_data = CVService.process_image(image.filepath)

    if "error" in insights_data:
        image.processed = True
        db.session.commit()
        return {"error": insights_data["error"]}

    existing_insights = db.session.query(Insights).filter_by(image_id=image_id).first()

    if existing_insights:
        for key, value in insights_data.items():
            setattr(existing_insights, key, value)
    else:
        insights = Insights(image_id=image_id, **insights_data)
        db.session.add(insights)

    image.processed = True
    db.session.commit()

    if insights_data.get("faces_detected", 0) > 0:
        try:
            face_locations = insights_data.get("face_locations", [])
            AnnotationService.create_annotated_image(image.filepath, face_locations)
        except Exception:
            pass

    return {"image_id": image_id, "status": "completed"}
