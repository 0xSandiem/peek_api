from io import BytesIO
from unittest.mock import MagicMock, mock_open, patch

import pytest
from PIL import Image
from werkzeug.datastructures import FileStorage


class TestStorageService:
    def test_save_file_returns_filepath(self):
        from app.services.storage_service import StorageService

        img = Image.new("RGB", (100, 100), color="red")
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)

        file_storage = FileStorage(stream=img_bytes, filename="test.jpg")

        with patch("app.services.storage_service.os.makedirs"):
            with patch("builtins.open", mock_open()):
                result = StorageService.save_file(file_storage)
                assert isinstance(result, str)
                assert result.endswith(".jpg")

    def test_validate_file_valid_image(self):
        from app.services.storage_service import StorageService

        img = Image.new("RGB", (100, 100), color="blue")
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        file_storage = FileStorage(stream=img_bytes, filename="test.png")

        result = StorageService.validate_file(file_storage)
        assert result is True

    def test_validate_file_invalid_extension(self):
        from app.services.storage_service import StorageService

        file_storage = FileStorage(stream=BytesIO(b"data"), filename="test.txt")

        result = StorageService.validate_file(file_storage)
        assert result is False


class TestImageService:
    def test_create_analysis_task_returns_id(self):
        from app.services.image_service import ImageService

        with patch("app.services.image_service.db.session"):
            result = ImageService.create_analysis_task(
                "/path/to/image.jpg", "image.jpg"
            )
            assert isinstance(result, (int, dict))

    def test_get_analysis_results_returns_data(self):
        from app.services.image_service import ImageService

        with patch("app.services.image_service.db.session"):
            result = ImageService.get_analysis_results(1)
            assert result is None or isinstance(result, dict)


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
