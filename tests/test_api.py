import json
from unittest.mock import MagicMock, patch

import pytest


class TestHealthEndpoint:
    def test_health_check_returns_ok(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json == {"status": "ok"}


class TestImageUpload:
    def test_upload_image_success(self, client, sample_image):
        response = client.post(
            "/api/analyze",
            data={"image": (sample_image, "test.jpg")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 202
        data = response.json
        assert "id" in data
        assert data["status"] == "processing"

    def test_upload_without_image_fails(self, client):
        response = client.post("/api/analyze")
        assert response.status_code == 400
        assert "error" in response.json

    def test_upload_invalid_file_type_fails(self, client, invalid_file):
        response = client.post(
            "/api/analyze",
            data={"image": (invalid_file, "test.txt")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        assert "error" in response.json

    def test_upload_file_too_large_fails(self, client, large_image):
        with patch(
            "app.services.storage_service.StorageService.validate_file"
        ) as mock_validate:
            mock_validate.return_value = False
            response = client.post(
                "/api/analyze",
                data={"image": (large_image, "large.jpg")},
                content_type="multipart/form-data",
            )
            assert response.status_code == 400


class TestResultsRetrieval:
    def test_get_results_processing(self, client):
        response = client.get("/api/results/1")
        assert response.status_code in [200, 202, 404]

    def test_get_results_completed(self, client):
        with patch("app.routes.api.ImageService.get_analysis_results") as mock_service:
            mock_service.return_value = {
                "id": 1,
                "status": "completed",
                "insights": {
                    "dominant_colors": ["#FF0000", "#00FF00"],
                    "brightness": 128,
                    "faces_detected": 2,
                    "quality_score": 85,
                },
            }
            response = client.get("/api/results/1")
            assert response.status_code == 200
            data = response.json
            assert data["status"] == "completed"
            assert "insights" in data

    def test_get_results_not_found(self, client):
        with patch("app.routes.api.ImageService.get_analysis_results") as mock_service:
            mock_service.return_value = None
            response = client.get("/api/results/999")
            assert response.status_code == 404


class TestImageRetrieval:
    def test_get_original_image(self, client):
        with patch("app.routes.api.StorageService.get_image") as mock_storage:
            mock_storage.return_value = (b"fake_image_data", "image/jpeg")
            response = client.get("/api/image/1/original")
            assert response.status_code == 200
            assert response.content_type == "image/jpeg"

    def test_get_original_image_not_found(self, client):
        with patch("app.routes.api.StorageService.get_image") as mock_storage:
            mock_storage.return_value = (None, None)
            response = client.get("/api/image/999/original")
            assert response.status_code == 404

    def test_get_annotated_image(self, client):
        with patch("app.routes.api.StorageService.get_annotated_image") as mock_storage:
            mock_storage.return_value = (b"fake_annotated_data", "image/jpeg")
            response = client.get("/api/image/1/annotated")
            assert response.status_code == 200
            assert response.content_type == "image/jpeg"
