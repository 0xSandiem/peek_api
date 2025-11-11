import os
from io import BytesIO

from PIL import Image as PILImage


def validate_file_extension(filename, allowed_extensions):
    if not filename:
        return False

    if "." not in filename:
        return False

    ext = filename.rsplit(".", 1)[1].lower()
    return ext in allowed_extensions


def validate_file_size(file_storage, max_size):
    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)

    return file_size <= max_size


def validate_image_content(file_storage):
    try:
        file_storage.seek(0)
        img = PILImage.open(file_storage)
        img.verify()
        file_storage.seek(0)
        return True
    except Exception:
        file_storage.seek(0)
        return False


def sanitize_filename(filename):
    if not filename or not filename.strip():
        raise ValueError("Filename cannot be empty")

    if "\x00" in filename:
        raise ValueError("Null byte in filename")

    filename = os.path.basename(filename)

    if not filename or not filename.strip():
        raise ValueError("Invalid filename after sanitization")

    invalid_chars = ["..", "/", "\\"]
    for char in invalid_chars:
        if char in filename:
            filename = filename.replace(char, "")

    if not filename or not filename.strip():
        raise ValueError("Filename contains only invalid characters")

    return filename.strip()
