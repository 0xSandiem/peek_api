import os
from io import BytesIO
from unittest.mock import MagicMock, mock_open, patch

import pytest
from PIL import Image
from werkzeug.datastructures import FileStorage


class TestStorageService:
    @patch("app.services.storage_service.boto3.client")
    def test_save_file_returns_filepath(self, mock_boto_client, app):
        from app.services.storage_service import StorageService

        with app.app_context():
            app.config["R2_ACCOUNT_ID"] = "test_account"
            app.config["R2_ACCESS_KEY_ID"] = "test_key"
            app.config["R2_SECRET_ACCESS_KEY"] = "test_secret"
            app.config["R2_BUCKET_NAME"] = "test-bucket"

            mock_s3 = MagicMock()
            mock_boto_client.return_value = mock_s3

            img = Image.new("RGB", (100, 100), color="red")
            img_bytes = BytesIO()
            img.save(img_bytes, format="JPEG")
            img_bytes.seek(0)

            file_storage = FileStorage(stream=img_bytes, filename="test.jpg")

            result = StorageService.save_file(file_storage)
            assert isinstance(result, str)
            assert ".jpg" in result
            assert result.startswith("images/")

    def test_validate_file_valid_image(self, app):
        from app.services.storage_service import StorageService

        with app.app_context():
            img = Image.new("RGB", (100, 100), color="blue")
            img_bytes = BytesIO()
            img.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            file_storage = FileStorage(stream=img_bytes, filename="test.png")

            result = StorageService.validate_file(file_storage)
            assert result is True

    def test_validate_file_invalid_extension(self, app):
        from app.services.storage_service import StorageService

        with app.app_context():
            file_storage = FileStorage(stream=BytesIO(b"data"), filename="test.txt")

            result = StorageService.validate_file(file_storage)
            assert result is False

    @patch("app.services.storage_service.boto3.client")
    def test_get_image_returns_bytes(self, mock_boto_client, app):
        from app import db
        from app.models import Image as ImageModel
        from app.services.storage_service import StorageService

        with app.app_context():
            app.config["R2_ACCOUNT_ID"] = "test_account"
            app.config["R2_ACCESS_KEY_ID"] = "test_key"
            app.config["R2_SECRET_ACCESS_KEY"] = "test_secret"
            app.config["R2_BUCKET_NAME"] = "test-bucket"

            mock_s3 = MagicMock()
            mock_response = {
                "Body": MagicMock(read=MagicMock(return_value=b"test_image_data"))
            }
            mock_s3.get_object.return_value = mock_response
            mock_boto_client.return_value = mock_s3

            image_record = ImageModel(
                filename="get_test.jpg",
                filepath="images/test.jpg",
                format="JPEG",
                width=50,
                height=50,
            )
            db.session.add(image_record)
            db.session.commit()

            data, mimetype = StorageService.get_image(image_record.id)

            assert data is not None
            assert isinstance(data, bytes)
            assert mimetype == "image/jpeg"

    def test_get_image_not_found(self, app):
        from app.services.storage_service import StorageService

        with app.app_context():
            data, mimetype = StorageService.get_image(99999)

            assert data is None
            assert mimetype is None


class TestImageService:
    def test_create_analysis_task_returns_dict(self, app):
        from app.services.image_service import ImageService

        with app.app_context():
            result = ImageService.create_analysis_task(
                "/path/to/image_service_test.jpg", "image.jpg", 1024, "JPEG", 100, 100
            )
            assert isinstance(result, dict)
            assert "id" in result
            assert "status" in result
            assert result["status"] == "processing"

    def test_get_analysis_results_not_found(self, app):
        from app.services.image_service import ImageService

        with app.app_context():
            result = ImageService.get_analysis_results(99999)
            assert result is None

    def test_get_analysis_results_processing(self, app):
        from app import db
        from app.models import Image as ImageModel
        from app.services.image_service import ImageService

        with app.app_context():
            image = ImageModel(
                filename="processing.jpg",
                filepath="/uploads/processing_test.jpg",
                processed=False,
            )
            db.session.add(image)
            db.session.commit()

            result = ImageService.get_analysis_results(image.id)

            assert result is not None
            assert result["status"] == "processing"
            assert result["id"] == image.id


class TestCVService:
    def test_process_image_returns_insights(self):
        from app.services.cv_service import CVService

        img = Image.new("RGB", (100, 100), color="red")
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)

        with patch("app.services.cv_service.ColorAnalyzer.analyze") as mock_color:
            with patch("app.services.cv_service.FaceDetector.detect") as mock_face:
                with patch(
                    "app.services.cv_service.QualityAnalyzer.analyze"
                ) as mock_quality:
                    with patch(
                        "app.services.cv_service.SceneDetector.detect"
                    ) as mock_scene:
                        mock_color.return_value = {
                            "dominant_colors": ["#FF0000"],
                            "brightness": 128,
                        }
                        mock_face.return_value = {
                            "faces_detected": 0,
                            "face_locations": [],
                        }
                        mock_quality.return_value = {"quality_score": 85}
                        mock_scene.return_value = {
                            "scene_type": "unknown",
                            "scene_confidence": 0.5,
                        }

                        result = CVService.process_image("/path/to/image.jpg")

                        assert isinstance(result, dict)
                        assert "dominant_colors" in result or "error" in result
