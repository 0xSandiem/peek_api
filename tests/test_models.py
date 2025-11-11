import pytest

from app import db
from app.models import Image, Insights


class TestImageModel:
    def test_image_model_creation(self, app):
        with app.app_context():
            image = Image(
                filename="test.jpg",
                filepath="/uploads/test_unique.jpg",
                file_size=1024,
                format="JPEG",
                width=800,
                height=600,
            )
            db.session.add(image)
            db.session.commit()

            assert image.id is not None
            assert image.filename == "test.jpg"
            assert image.processed is False
            assert image.uploaded_at is not None

    def test_image_model_to_dict(self, app):
        with app.app_context():
            image = Image(
                filename="test.jpg",
                filepath="/uploads/test_dict.jpg",
                file_size=2048,
                format="PNG",
                width=1024,
                height=768,
                processed=True,
                processing_time=1.5,
            )
            db.session.add(image)
            db.session.commit()

            data = image.to_dict()

            assert isinstance(data, dict)
            assert data["filename"] == "test.jpg"
            assert data["processed"] is True
            assert data["processing_time"] == 1.5
            assert "id" in data

    def test_filepath_uniqueness(self, app):
        with app.app_context():
            image1 = Image(filename="test1.jpg", filepath="/uploads/same.jpg")
            db.session.add(image1)
            db.session.commit()

            image2 = Image(filename="test2.jpg", filepath="/uploads/same.jpg")
            db.session.add(image2)

            with pytest.raises(Exception):
                db.session.commit()

    def test_filename_max_length(self, app):
        with app.app_context():
            long_filename = "a" * 256

            with pytest.raises(ValueError):
                Image(
                    filename=long_filename, filepath="/uploads/long.jpg"
                )  # noqa: F841


class TestImageModelSecurity:
    def test_path_traversal_prevention(self, app):
        with app.app_context():
            with pytest.raises(ValueError):
                Image(
                    filename="test.jpg", filepath="/uploads/../../../etc/passwd"
                )  # noqa: F841

    def test_filename_sanitization(self, app):
        with app.app_context():
            image = Image(filename="../../etc/passwd", filepath="/uploads/safe.jpg")
            assert image.filename == "passwd"
            assert ".." not in image.filename

    def test_null_byte_injection_prevention(self, app):
        with app.app_context():
            with pytest.raises(ValueError):
                Image(
                    filename="test\x00.jpg", filepath="/uploads/test.jpg"
                )  # noqa: F841

    def test_error_message_sanitization(self, app):
        with app.app_context():
            error_with_traceback = (
                'Traceback (most recent call last): File "test.py", line 10'
            )
            image = Image(
                filename="test.jpg",
                filepath="/uploads/error.jpg",
                error_message=error_with_traceback,
            )
            assert image.error_message == "Processing error occurred"

    def test_error_message_truncation(self, app):
        with app.app_context():
            long_error = "A" * 2000
            image = Image(
                filename="test.jpg",
                filepath="/uploads/error_long.jpg",
                error_message=long_error,
            )
            assert len(image.error_message) <= 1000


class TestInsightsModel:
    def test_insights_model_creation(self, app):
        with app.app_context():
            image = Image(filename="test.jpg", filepath="/uploads/insights_test.jpg")
            db.session.add(image)
            db.session.commit()

            insights = Insights(
                image_id=image.id,
                dominant_colors=["#FF0000", "#00FF00"],
                brightness=128,
                faces_detected=2,
                face_locations=[{"x": 10, "y": 20, "w": 30, "h": 40}],
                text_found=True,
                extracted_text="Hello World",
                word_count=2,
                sharpness_score=0.85,
                blur_level="low",
                contrast_score=0.75,
                quality_score=85,
                scene_type="outdoor",
                scene_confidence=0.92,
            )
            db.session.add(insights)
            db.session.commit()

            assert insights.id is not None
            assert insights.image_id == image.id
            assert insights.brightness == 128
            assert insights.faces_detected == 2

    def test_insights_model_to_dict(self, app):
        with app.app_context():
            image = Image(filename="test.jpg", filepath="/uploads/insights_dict.jpg")
            db.session.add(image)
            db.session.commit()

            insights = Insights(
                image_id=image.id,
                dominant_colors=["#FF0000"],
                brightness=100,
                quality_score=90,
            )
            db.session.add(insights)
            db.session.commit()

            data = insights.to_dict()

            assert isinstance(data, dict)
            assert data["dominant_colors"] == ["#FF0000"]
            assert data["brightness"] == 100
            assert data["quality_score"] == 90
            assert "id" in data

    def test_cascade_delete(self, app):
        with app.app_context():
            image = Image(filename="test.jpg", filepath="/uploads/cascade.jpg")
            db.session.add(image)
            db.session.commit()

            insights = Insights(image_id=image.id, brightness=128)
            db.session.add(insights)
            db.session.commit()

            insights_id = insights.id

            db.session.delete(image)
            db.session.commit()

            deleted_insights = db.session.get(Insights, insights_id)
            assert deleted_insights is None

    def test_relationship(self, app):
        with app.app_context():
            image = Image(filename="test.jpg", filepath="/uploads/relationship.jpg")
            db.session.add(image)
            db.session.commit()

            insights = Insights(image_id=image.id, brightness=128)
            db.session.add(insights)
            db.session.commit()

            assert image.insights is not None
            assert len(image.insights) == 1
            assert image.insights[0].brightness == 128
            assert insights.image.filename == "test.jpg"


class TestInsightsModelValidation:
    def test_brightness_validation_max(self, app):
        with app.app_context():
            image = Image(filename="test.jpg", filepath="/uploads/brightness_max.jpg")
            db.session.add(image)
            db.session.commit()

            with pytest.raises(ValueError):
                Insights(image_id=image.id, brightness=256)  # noqa: F841

    def test_brightness_validation_min(self, app):
        with app.app_context():
            image = Image(filename="test.jpg", filepath="/uploads/brightness_min.jpg")
            db.session.add(image)
            db.session.commit()

            with pytest.raises(ValueError):
                Insights(image_id=image.id, brightness=-1)  # noqa: F841

    def test_quality_score_validation_max(self, app):
        with app.app_context():
            image = Image(filename="test.jpg", filepath="/uploads/quality_max.jpg")
            db.session.add(image)
            db.session.commit()

            with pytest.raises(ValueError):
                Insights(image_id=image.id, quality_score=101)  # noqa: F841

    def test_quality_score_validation_min(self, app):
        with app.app_context():
            image = Image(filename="test.jpg", filepath="/uploads/quality_min.jpg")
            db.session.add(image)
            db.session.commit()

            with pytest.raises(ValueError):
                Insights(image_id=image.id, quality_score=-1)  # noqa: F841

    def test_scene_confidence_validation_max(self, app):
        with app.app_context():
            image = Image(filename="test.jpg", filepath="/uploads/confidence_max.jpg")
            db.session.add(image)
            db.session.commit()

            with pytest.raises(ValueError):
                Insights(image_id=image.id, scene_confidence=1.1)  # noqa: F841

    def test_scene_confidence_validation_min(self, app):
        with app.app_context():
            image = Image(filename="test.jpg", filepath="/uploads/confidence_min.jpg")
            db.session.add(image)
            db.session.commit()

            with pytest.raises(ValueError):
                Insights(image_id=image.id, scene_confidence=-0.1)  # noqa: F841
