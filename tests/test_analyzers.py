from io import BytesIO
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from PIL import Image


class TestColorAnalyzer:
    def test_analyze_returns_dominant_colors(self):
        from app.analyzers.color_analyzer import ColorAnalyzer

        img = Image.new("RGB", (100, 100), color="red")
        img_array = np.array(img)

        result = ColorAnalyzer.analyze(img_array)

        assert "dominant_colors" in result
        assert "brightness" in result
        assert isinstance(result["dominant_colors"], list)
        assert isinstance(result["brightness"], (int, float))

    def test_analyze_brightness_range(self):
        from app.analyzers.color_analyzer import ColorAnalyzer

        img = Image.new("RGB", (100, 100), color="white")
        img_array = np.array(img)

        result = ColorAnalyzer.analyze(img_array)

        assert 0 <= result["brightness"] <= 255


class TestFaceDetector:
    def test_detect_faces_returns_count(self):
        from app.analyzers.face_detector import FaceDetector

        img = Image.new("RGB", (200, 200), color="white")
        img_array = np.array(img)

        result = FaceDetector.detect(img_array)

        assert "faces_detected" in result
        assert "face_locations" in result
        assert isinstance(result["faces_detected"], int)
        assert isinstance(result["face_locations"], list)

    def test_detect_no_faces(self):
        from app.analyzers.face_detector import FaceDetector

        img = Image.new("RGB", (100, 100), color="blue")
        img_array = np.array(img)

        result = FaceDetector.detect(img_array)

        assert result["faces_detected"] == 0
        assert result["face_locations"] == []


class TestQualityAnalyzer:
    def test_analyze_returns_quality_metrics(self):
        from app.analyzers.quality_analyzer import QualityAnalyzer

        img = Image.new("RGB", (100, 100), color="green")
        img_array = np.array(img)

        result = QualityAnalyzer.analyze(img_array)

        assert "sharpness_score" in result
        assert "blur_level" in result
        assert "contrast_score" in result
        assert "quality_score" in result

    def test_quality_score_in_range(self):
        from app.analyzers.quality_analyzer import QualityAnalyzer

        img = Image.new("RGB", (100, 100), color="yellow")
        img_array = np.array(img)

        result = QualityAnalyzer.analyze(img_array)

        assert 0 <= result["quality_score"] <= 100


class TestSceneDetector:
    def test_detect_scene_returns_type(self):
        from app.analyzers.scene_detector import SceneDetector

        img = Image.new("RGB", (300, 200), color="skyblue")
        img_array = np.array(img)

        result = SceneDetector.detect(img_array)

        assert "scene_type" in result
        assert "scene_confidence" in result
        assert isinstance(result["scene_type"], str)
        assert isinstance(result["scene_confidence"], float)

    def test_scene_confidence_in_range(self):
        from app.analyzers.scene_detector import SceneDetector

        img = Image.new("RGB", (200, 200), color="green")
        img_array = np.array(img)

        result = SceneDetector.detect(img_array)

        assert 0.0 <= result["scene_confidence"] <= 1.0


class TestTextExtractor:
    def test_extract_text_returns_result(self):
        from app.analyzers.text_extractor import TextExtractor

        img = Image.new("RGB", (200, 100), color="white")
        img_array = np.array(img)

        result = TextExtractor.extract(img_array)

        assert "text_found" in result
        assert "extracted_text" in result
        assert "word_count" in result
        assert isinstance(result["text_found"], bool)
        assert isinstance(result["word_count"], int)
