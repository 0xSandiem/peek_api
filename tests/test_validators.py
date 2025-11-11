from io import BytesIO

import pytest
from PIL import Image
from werkzeug.datastructures import FileStorage


class TestFileExtensionValidation:
    def test_valid_extensions(self):
        from app.utils.validators import validate_file_extension

        allowed = {"jpg", "png", "gif"}

        assert validate_file_extension("test.jpg", allowed) is True
        assert validate_file_extension("test.png", allowed) is True
        assert validate_file_extension("test.gif", allowed) is True
        assert validate_file_extension("TEST.JPG", allowed) is True

    def test_invalid_extensions(self):
        from app.utils.validators import validate_file_extension

        allowed = {"jpg", "png"}

        assert validate_file_extension("test.txt", allowed) is False
        assert validate_file_extension("test.exe", allowed) is False
        assert validate_file_extension("test.php", allowed) is False

    def test_no_extension(self):
        from app.utils.validators import validate_file_extension

        allowed = {"jpg"}

        assert validate_file_extension("test", allowed) is False
        assert validate_file_extension("", allowed) is False


class TestFileSizeValidation:
    def test_file_within_limit(self):
        from app.utils.validators import validate_file_size

        small_file = BytesIO(b"a" * 100)
        file_storage = FileStorage(stream=small_file, filename="test.jpg")

        assert validate_file_size(file_storage, 1024) is True

    def test_file_exceeds_limit(self):
        from app.utils.validators import validate_file_size

        large_file = BytesIO(b"a" * 2000)
        file_storage = FileStorage(stream=large_file, filename="test.jpg")

        assert validate_file_size(file_storage, 1024) is False

    def test_file_exact_limit(self):
        from app.utils.validators import validate_file_size

        exact_file = BytesIO(b"a" * 1024)
        file_storage = FileStorage(stream=exact_file, filename="test.jpg")

        assert validate_file_size(file_storage, 1024) is True


class TestImageContentValidation:
    def test_valid_jpeg_magic_bytes(self):
        from app.utils.validators import validate_image_content

        img = Image.new("RGB", (10, 10), color="red")
        img_bytes = BytesIO()
        img.save(img_bytes, format="JPEG")
        img_bytes.seek(0)

        file_storage = FileStorage(stream=img_bytes, filename="test.jpg")

        assert validate_image_content(file_storage) is True

    def test_valid_png_magic_bytes(self):
        from app.utils.validators import validate_image_content

        img = Image.new("RGB", (10, 10), color="blue")
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        file_storage = FileStorage(stream=img_bytes, filename="test.png")

        assert validate_image_content(file_storage) is True

    def test_invalid_image_content(self):
        from app.utils.validators import validate_image_content

        fake_image = BytesIO(b"not an image")
        file_storage = FileStorage(stream=fake_image, filename="test.jpg")

        assert validate_image_content(file_storage) is False


class TestFilenameSanitization:
    def test_sanitize_basic_filename(self):
        from app.utils.validators import sanitize_filename

        result = sanitize_filename("test.jpg")
        assert result == "test.jpg"

    def test_sanitize_path_traversal(self):
        from app.utils.validators import sanitize_filename

        result = sanitize_filename("../../etc/passwd")
        assert ".." not in result
        assert "/" not in result
        assert result == "passwd"

    def test_sanitize_special_characters(self):
        from app.utils.validators import sanitize_filename

        result = sanitize_filename("test/../file.jpg")
        assert ".." not in result
        assert result == "file.jpg"

    def test_sanitize_null_bytes(self):
        from app.utils.validators import sanitize_filename

        with pytest.raises(ValueError):
            sanitize_filename("test\x00.jpg")

    def test_sanitize_empty_filename(self):
        from app.utils.validators import sanitize_filename

        with pytest.raises(ValueError):
            sanitize_filename("")

    def test_sanitize_whitespace_only(self):
        from app.utils.validators import sanitize_filename

        with pytest.raises(ValueError):
            sanitize_filename("   ")
