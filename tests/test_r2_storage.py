"""
Tests for R2 storage service functionality.
"""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError, EndpointConnectionError
from PIL import Image as PILImage
from werkzeug.datastructures import FileStorage

from app import db


class TestR2StorageService:
    """Test R2-specific storage service methods."""

    @patch("app.services.storage_service.boto3.client")
    def test_get_r2_client_with_valid_credentials(self, mock_boto_client, app):
        """Test R2 client creation with valid credentials."""
        from app.services.storage_service import StorageService

        with app.app_context():
            app.config["R2_ACCOUNT_ID"] = "test_account"
            app.config["R2_ACCESS_KEY_ID"] = "test_key"
            app.config["R2_SECRET_ACCESS_KEY"] = "test_secret"
            app.config["R2_REGION"] = "auto"

            StorageService._get_r2_client()  # noqa: F841

            mock_boto_client.assert_called_once()
            call_kwargs = mock_boto_client.call_args[1]
            assert "test_account" in call_kwargs["endpoint_url"]
            assert call_kwargs["aws_access_key_id"] == "test_key"
            assert call_kwargs["aws_secret_access_key"] == "test_secret"

    @patch("app.services.storage_service.boto3.client")
    def test_get_r2_client_missing_credentials(self, mock_boto_client, app):
        """Test R2 client creation fails with missing credentials."""
        from app.services.storage_service import StorageService

        with app.app_context():
            app.config["R2_ACCOUNT_ID"] = None
            app.config["R2_ACCESS_KEY_ID"] = None
            app.config["R2_SECRET_ACCESS_KEY"] = None

            with pytest.raises(ValueError, match="R2 credentials not configured"):
                StorageService._get_r2_client()

    @patch("app.services.storage_service.boto3.client")
    def test_save_file_uploads_to_r2(self, mock_boto_client, app):
        """Test file upload to R2."""
        from app.services.storage_service import StorageService

        with app.app_context():
            app.config["R2_ACCOUNT_ID"] = "test_account"
            app.config["R2_ACCESS_KEY_ID"] = "test_key"
            app.config["R2_SECRET_ACCESS_KEY"] = "test_secret"
            app.config["R2_BUCKET_NAME"] = "test-bucket"

            mock_s3 = MagicMock()
            mock_boto_client.return_value = mock_s3

            img = PILImage.new("RGB", (100, 100), color="red")
            img_bytes = BytesIO()
            img.save(img_bytes, format="JPEG")
            img_bytes.seek(0)

            file_storage = FileStorage(stream=img_bytes, filename="test.jpg")

            result = StorageService.save_file(file_storage)

            assert result.startswith("images/")
            assert result.endswith(".jpg")
            mock_s3.upload_fileobj.assert_called_once()

    @patch("app.services.storage_service.boto3.client")
    def test_save_file_retry_on_failure(self, mock_boto_client, app):
        """Test retry logic when upload fails."""
        from app.services.storage_service import StorageService

        with app.app_context():
            app.config["R2_ACCOUNT_ID"] = "test_account"
            app.config["R2_ACCESS_KEY_ID"] = "test_key"
            app.config["R2_SECRET_ACCESS_KEY"] = "test_secret"
            app.config["R2_BUCKET_NAME"] = "test-bucket"

            mock_s3 = MagicMock()
            mock_s3.upload_fileobj.side_effect = [
                EndpointConnectionError(endpoint_url="test"),
                EndpointConnectionError(endpoint_url="test"),
                None,
            ]
            mock_boto_client.return_value = mock_s3

            img = PILImage.new("RGB", (100, 100), color="blue")
            img_bytes = BytesIO()
            img.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            file_storage = FileStorage(stream=img_bytes, filename="test.png")

            with patch("time.sleep"):
                result = StorageService.save_file(file_storage)

            assert result.startswith("images/")
            assert mock_s3.upload_fileobj.call_count == 3

    @patch("app.services.storage_service.boto3.client")
    def test_save_file_max_retries_exceeded(self, mock_boto_client, app):
        """Test failure after max retries."""
        from app.services.storage_service import StorageService

        with app.app_context():
            app.config["R2_ACCOUNT_ID"] = "test_account"
            app.config["R2_ACCESS_KEY_ID"] = "test_key"
            app.config["R2_SECRET_ACCESS_KEY"] = "test_secret"
            app.config["R2_BUCKET_NAME"] = "test-bucket"

            mock_s3 = MagicMock()
            mock_s3.upload_fileobj.side_effect = EndpointConnectionError(
                endpoint_url="test"
            )
            mock_boto_client.return_value = mock_s3

            img = PILImage.new("RGB", (100, 100), color="green")
            img_bytes = BytesIO()
            img.save(img_bytes, format="JPEG")
            img_bytes.seek(0)

            file_storage = FileStorage(stream=img_bytes, filename="test.jpg")

            with patch("time.sleep"):
                with pytest.raises(IOError, match="Failed to save file"):
                    StorageService.save_file(file_storage)

            assert mock_s3.upload_fileobj.call_count == 3

    @patch("app.services.storage_service.boto3.client")
    def test_get_image_from_r2(self, mock_boto_client, app):
        """Test retrieving image from R2."""
        from app.models import Image
        from app.services.storage_service import StorageService

        with app.app_context():
            app.config["R2_ACCOUNT_ID"] = "test_account"
            app.config["R2_ACCESS_KEY_ID"] = "test_key"
            app.config["R2_SECRET_ACCESS_KEY"] = "test_secret"
            app.config["R2_BUCKET_NAME"] = "test-bucket"

            img_record = Image(
                filename="test.jpg",
                filepath="images/20250101_12345678.jpg",
                file_size=1024,
                format="JPEG",
                width=100,
                height=100,
                processed=True,
            )
            db.session.add(img_record)
            db.session.commit()

            mock_s3 = MagicMock()
            mock_response = {
                "Body": MagicMock(read=MagicMock(return_value=b"fake_image_data"))
            }
            mock_s3.get_object.return_value = mock_response
            mock_boto_client.return_value = mock_s3

            data, mimetype = StorageService.get_image(img_record.id)

            assert data == b"fake_image_data"
            assert mimetype == "image/jpeg"
            mock_s3.get_object.assert_called_once_with(
                Bucket="test-bucket", Key="images/20250101_12345678.jpg"
            )

    @patch("app.services.storage_service.boto3.client")
    def test_get_public_url_with_presigned(self, mock_boto_client, app):
        """Test generating presigned URL."""
        from app.models import Image
        from app.services.storage_service import StorageService

        with app.app_context():
            app.config["R2_ACCOUNT_ID"] = "test_account"
            app.config["R2_ACCESS_KEY_ID"] = "test_key"
            app.config["R2_SECRET_ACCESS_KEY"] = "test_secret"
            app.config["R2_BUCKET_NAME"] = "test-bucket"
            app.config["R2_PUBLIC_DOMAIN"] = None

            img_record = Image(
                filename="test.jpg",
                filepath="images/20250101_12345678.jpg",
                file_size=1024,
                format="JPEG",
                width=100,
                height=100,
                processed=True,
            )
            db.session.add(img_record)
            db.session.commit()

            mock_s3 = MagicMock()
            mock_s3.generate_presigned_url.return_value = (
                "https://presigned.url/image.jpg"
            )
            mock_boto_client.return_value = mock_s3

            url = StorageService.get_public_url(img_record.id, expiration=3600)

            assert url == "https://presigned.url/image.jpg"
            mock_s3.generate_presigned_url.assert_called_once()

    @patch("app.services.storage_service.boto3.client")
    def test_get_public_url_with_custom_domain(self, mock_boto_client, app):
        """Test public URL with custom domain."""
        from app.models import Image
        from app.services.storage_service import StorageService

        with app.app_context():
            app.config["R2_ACCOUNT_ID"] = "test_account"
            app.config["R2_ACCESS_KEY_ID"] = "test_key"
            app.config["R2_SECRET_ACCESS_KEY"] = "test_secret"
            app.config["R2_BUCKET_NAME"] = "test-bucket"
            app.config["R2_PUBLIC_DOMAIN"] = "https://images.example.com"

            img_record = Image(
                filename="test.jpg",
                filepath="images/20250101_12345678.jpg",
                file_size=1024,
                format="JPEG",
                width=100,
                height=100,
                processed=True,
            )
            db.session.add(img_record)
            db.session.commit()

            mock_s3 = MagicMock()
            mock_boto_client.return_value = mock_s3

            url = StorageService.get_public_url(img_record.id)

            assert url == "https://images.example.com/images/20250101_12345678.jpg"
            mock_s3.generate_presigned_url.assert_not_called()

    @patch("app.services.storage_service.boto3.client")
    def test_upload_file_to_r2_with_bytes(self, mock_boto_client, app):
        """Test uploading bytes data to R2."""
        from app.services.storage_service import StorageService

        with app.app_context():
            app.config["R2_ACCOUNT_ID"] = "test_account"
            app.config["R2_ACCESS_KEY_ID"] = "test_key"
            app.config["R2_SECRET_ACCESS_KEY"] = "test_secret"
            app.config["R2_BUCKET_NAME"] = "test-bucket"

            mock_s3 = MagicMock()
            mock_boto_client.return_value = mock_s3

            test_data = b"test_image_bytes"
            object_key = "images/test.jpg"

            result = StorageService.upload_file_to_r2(
                test_data, object_key, content_type="image/jpeg"
            )

            assert result == object_key
            mock_s3.upload_fileobj.assert_called_once()

    @patch("app.services.storage_service.boto3.client")
    def test_download_from_r2(self, mock_boto_client, app):
        """Test downloading file from R2."""
        from app.services.storage_service import StorageService

        with app.app_context():
            app.config["R2_ACCOUNT_ID"] = "test_account"
            app.config["R2_ACCESS_KEY_ID"] = "test_key"
            app.config["R2_SECRET_ACCESS_KEY"] = "test_secret"
            app.config["R2_BUCKET_NAME"] = "test-bucket"

            mock_s3 = MagicMock()
            mock_response = {
                "Body": MagicMock(read=MagicMock(return_value=b"downloaded_data"))
            }
            mock_s3.get_object.return_value = mock_response
            mock_boto_client.return_value = mock_s3

            data = StorageService.download_from_r2("images/test.jpg")

            assert data == b"downloaded_data"
            mock_s3.get_object.assert_called_once_with(
                Bucket="test-bucket", Key="images/test.jpg"
            )

    @patch("app.services.storage_service.boto3.client")
    def test_get_annotated_image_falls_back_to_original(self, mock_boto_client, app):
        """Test annotated image fallback when annotation doesn't exist."""
        from app.models import Image
        from app.services.storage_service import StorageService

        with app.app_context():
            app.config["R2_ACCOUNT_ID"] = "test_account"
            app.config["R2_ACCESS_KEY_ID"] = "test_key"
            app.config["R2_SECRET_ACCESS_KEY"] = "test_secret"
            app.config["R2_BUCKET_NAME"] = "test-bucket"

            img_record = Image(
                filename="test.jpg",
                filepath="images/20250101_12345678.jpg",
                file_size=1024,
                format="JPEG",
                width=100,
                height=100,
                processed=True,
            )
            db.session.add(img_record)
            db.session.commit()

            mock_s3 = MagicMock()

            def get_object_side_effect(Bucket, Key):
                if "_annotated" in Key:
                    error_response = {"Error": {"Code": "404"}}
                    raise ClientError(error_response, "GetObject")
                else:
                    return {
                        "Body": MagicMock(
                            read=MagicMock(return_value=b"original_image")
                        )
                    }

            mock_s3.get_object.side_effect = get_object_side_effect
            mock_boto_client.return_value = mock_s3

            data, mimetype = StorageService.get_annotated_image(img_record.id)

            assert data == b"original_image"
            assert mimetype == "image/jpeg"
            assert mock_s3.get_object.call_count == 2
