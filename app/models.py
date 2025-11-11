import os
from datetime import datetime

from sqlalchemy.dialects.postgresql import JSON

from app import db


class Image(db.Model):
    __tablename__ = "images"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False, index=True)
    filepath = db.Column(db.String(500), nullable=False, unique=True)
    file_size = db.Column(db.Integer)
    format = db.Column(db.String(10))
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    uploaded_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    processed = db.Column(db.Boolean, default=False, nullable=False, index=True)
    processing_time = db.Column(db.Float)
    error_message = db.Column(db.Text)

    insights = db.relationship(
        "Insights", backref="image", lazy=True, cascade="all, delete-orphan"
    )

    def __init__(self, **kwargs):
        if "filename" in kwargs:
            kwargs["filename"] = self._sanitize_filename(kwargs["filename"])
        if "filepath" in kwargs:
            kwargs["filepath"] = self._sanitize_filepath(kwargs["filepath"])
        if "error_message" in kwargs:
            kwargs["error_message"] = self._sanitize_error_message(
                kwargs["error_message"]
            )
        super(Image, self).__init__(**kwargs)

    @staticmethod
    def _sanitize_filename(filename):
        if not filename:
            raise ValueError("Filename cannot be empty")

        filename = os.path.basename(filename)

        if len(filename) > 255:
            raise ValueError("Filename exceeds maximum length of 255 characters")

        invalid_chars = ["..", "/", "\\", "\x00"]
        for char in invalid_chars:
            if char in filename:
                raise ValueError(f"Invalid character in filename: {char}")

        return filename

    @staticmethod
    def _sanitize_filepath(filepath):
        if not filepath:
            raise ValueError("Filepath cannot be empty")

        if len(filepath) > 500:
            raise ValueError("Filepath exceeds maximum length of 500 characters")

        if ".." in filepath:
            raise ValueError("Path traversal detected in filepath")

        return filepath

    @staticmethod
    def _sanitize_error_message(error_message):
        if not error_message:
            return None

        error_message = str(error_message)[:1000]

        sensitive_patterns = ["Traceback", 'File "', "line ", "raise ", "Exception"]
        for pattern in sensitive_patterns:
            if pattern in error_message:
                return "Processing error occurred"

        return error_message

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "filepath": self.filepath,
            "file_size": self.file_size,
            "format": self.format,
            "width": self.width,
            "height": self.height,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "processed": self.processed,
            "processing_time": self.processing_time,
            "error_message": self.error_message,
        }


class Insights(db.Model):
    __tablename__ = "insights"

    id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(
        db.Integer,
        db.ForeignKey("images.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    dominant_colors = db.Column(JSON)
    brightness = db.Column(db.Integer)

    faces_detected = db.Column(db.Integer, default=0)
    face_locations = db.Column(JSON)

    text_found = db.Column(db.Boolean, default=False)
    extracted_text = db.Column(db.Text)
    word_count = db.Column(db.Integer, default=0)

    sharpness_score = db.Column(db.Float)
    blur_level = db.Column(db.String(50))
    contrast_score = db.Column(db.Float)
    quality_score = db.Column(db.Integer)

    scene_type = db.Column(db.String(50))
    scene_confidence = db.Column(db.Float)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __init__(self, **kwargs):
        if "brightness" in kwargs:
            self._validate_brightness(kwargs["brightness"])
        if "quality_score" in kwargs:
            self._validate_quality_score(kwargs["quality_score"])
        if "scene_confidence" in kwargs:
            self._validate_scene_confidence(kwargs["scene_confidence"])
        super(Insights, self).__init__(**kwargs)

    @staticmethod
    def _validate_brightness(value):
        if value is not None and (value < 0 or value > 255):
            raise ValueError("Brightness must be between 0 and 255")

    @staticmethod
    def _validate_quality_score(value):
        if value is not None and (value < 0 or value > 100):
            raise ValueError("Quality score must be between 0 and 100")

    @staticmethod
    def _validate_scene_confidence(value):
        if value is not None and (value < 0.0 or value > 1.0):
            raise ValueError("Scene confidence must be between 0.0 and 1.0")

    def to_dict(self):
        return {
            "id": self.id,
            "image_id": self.image_id,
            "dominant_colors": self.dominant_colors,
            "brightness": self.brightness,
            "faces_detected": self.faces_detected,
            "face_locations": self.face_locations,
            "text_found": self.text_found,
            "extracted_text": self.extracted_text,
            "word_count": self.word_count,
            "sharpness_score": self.sharpness_score,
            "blur_level": self.blur_level,
            "contrast_score": self.contrast_score,
            "quality_score": self.quality_score,
            "scene_type": self.scene_type,
            "scene_confidence": self.scene_confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
