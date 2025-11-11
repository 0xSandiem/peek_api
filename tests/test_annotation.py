import os

import pytest
from PIL import Image

from app.services.annotation_service import AnnotationService


class TestAnnotationService:
    def test_create_annotated_image_with_faces(self, tmp_path):
        img = Image.new("RGB", (200, 200), color="white")
        img_path = tmp_path / "test.jpg"
        img.save(img_path)

        face_locations = [
            {"x": 50, "y": 50, "width": 80, "height": 80},
            {"x": 120, "y": 100, "width": 60, "height": 60},
        ]

        annotated_path = AnnotationService.create_annotated_image(
            str(img_path), face_locations
        )

        assert os.path.exists(annotated_path)
        assert "_annotated" in annotated_path
        assert annotated_path.endswith(".jpg")

    def test_create_annotated_image_no_faces(self, tmp_path):
        img = Image.new("RGB", (100, 100), color="blue")
        img_path = tmp_path / "no_faces.jpg"
        img.save(img_path)

        face_locations = []

        annotated_path = AnnotationService.create_annotated_image(
            str(img_path), face_locations
        )

        assert os.path.exists(annotated_path)
        assert "_annotated" in annotated_path

    def test_create_annotated_image_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            AnnotationService.create_annotated_image("/nonexistent/path.jpg", [])

    def test_create_annotated_image_preserves_extension(self, tmp_path):
        img = Image.new("RGB", (100, 100), color="red")
        img_path = tmp_path / "test.png"
        img.save(img_path)

        face_locations = [{"x": 10, "y": 10, "width": 50, "height": 50}]

        annotated_path = AnnotationService.create_annotated_image(
            str(img_path), face_locations
        )

        assert annotated_path.endswith(".png")
        assert os.path.exists(annotated_path)
