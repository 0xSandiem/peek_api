import os
import uuid
from datetime import datetime

from flask import current_app
from PIL import Image as PILImage

from app import db
from app.models import Image
from app.utils.validators import (
    sanitize_filename,
    validate_file_extension,
    validate_file_size,
    validate_image_content,
)


class StorageService:
    @staticmethod
    def save_file(file_storage):
        try:
            filename = sanitize_filename(file_storage.filename)

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            ext = filename.rsplit(".", 1)[1].lower()
            unique_filename = f"{timestamp}_{unique_id}.{ext}"

            upload_folder = current_app.config["UPLOAD_FOLDER"]

            if not os.path.isabs(upload_folder):
                upload_folder = os.path.join(os.getcwd(), upload_folder)

            os.makedirs(upload_folder, exist_ok=True)

            filepath = os.path.join(upload_folder, unique_filename)

            if ".." in filepath or not filepath.startswith(upload_folder):
                raise ValueError("Invalid filepath detected")

            file_storage.save(filepath)

            os.chmod(filepath, 0o644)

            return filepath

        except Exception as e:
            raise IOError(f"Failed to save file: {str(e)}")

    @staticmethod
    def validate_file(file_storage):
        try:
            allowed_extensions = current_app.config["ALLOWED_EXTENSIONS"]
            max_size = current_app.config["MAX_FILE_SIZE"]

            if not validate_file_extension(file_storage.filename, allowed_extensions):
                return False

            if not validate_file_size(file_storage, max_size):
                return False

            if not validate_image_content(file_storage):
                return False

            return True

        except Exception:
            return False

    @staticmethod
    def get_image(image_id):
        try:
            if not isinstance(image_id, int):
                image_id = int(image_id)

            image = db.session.get(Image, image_id)

            if not image:
                return (None, None)

            if not os.path.exists(image.filepath):
                return (None, None)

            with open(image.filepath, "rb") as f:
                data = f.read()

            mimetype_map = {
                "JPEG": "image/jpeg",
                "PNG": "image/png",
                "GIF": "image/gif",
                "BMP": "image/bmp",
                "WEBP": "image/webp",
            }

            mimetype = mimetype_map.get(image.format, "application/octet-stream")

            return (data, mimetype)

        except Exception:
            return (None, None)

    @staticmethod
    def get_annotated_image(image_id):
        try:
            if not isinstance(image_id, int):
                image_id = int(image_id)

            image = db.session.get(Image, image_id)

            if not image:
                return (None, None)

            annotated_path = (
                image.filepath.rsplit(".", 1)[0]
                + "_annotated."
                + image.filepath.rsplit(".", 1)[1]
            )

            if os.path.exists(annotated_path):
                with open(annotated_path, "rb") as f:
                    data = f.read()

                mimetype_map = {
                    "JPEG": "image/jpeg",
                    "PNG": "image/png",
                    "GIF": "image/gif",
                    "BMP": "image/bmp",
                    "WEBP": "image/webp",
                }

                mimetype = mimetype_map.get(image.format, "application/octet-stream")

                return (data, mimetype)
            else:
                return StorageService.get_image(image_id)

        except Exception:
            return (None, None)

    @staticmethod
    def get_image_dimensions(filepath):
        try:
            with PILImage.open(filepath) as img:
                return img.size
        except Exception:
            return (None, None)

    @staticmethod
    def get_image_format(filepath):
        try:
            with PILImage.open(filepath) as img:
                return img.format
        except Exception:
            return None
