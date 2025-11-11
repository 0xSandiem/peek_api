import logging
import time
import uuid
from datetime import datetime
from io import BytesIO

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError, EndpointConnectionError
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

logger = logging.getLogger(__name__)


class StorageService:
    MAX_RETRIES = 3
    RETRY_DELAY = 1

    @staticmethod
    def _retry_with_backoff(func, *args, **kwargs):
        """Execute function with exponential backoff retry logic."""
        for attempt in range(StorageService.MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except (ClientError, EndpointConnectionError) as e:
                if attempt == StorageService.MAX_RETRIES - 1:
                    raise

                delay = StorageService.RETRY_DELAY * (2**attempt)
                logger.warning(
                    f"R2 operation failed (attempt {attempt + 1}/{StorageService.MAX_RETRIES}): {str(e)}. "
                    f"Retrying in {delay}s..."
                )
                time.sleep(delay)

    @staticmethod
    def _get_r2_client():
        account_id = current_app.config.get("R2_ACCOUNT_ID")
        access_key = current_app.config.get("R2_ACCESS_KEY_ID")
        secret_key = current_app.config.get("R2_SECRET_ACCESS_KEY")
        region = current_app.config.get("R2_REGION", "auto")

        if not all([account_id, access_key, secret_key]):
            logger.error("R2 credentials not configured properly")
            raise ValueError("R2 credentials not configured")

        endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

        return boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
            region_name=region,
        )

    @staticmethod
    def save_file(file_storage):
        try:
            filename = sanitize_filename(file_storage.filename)

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            ext = filename.rsplit(".", 1)[1].lower()
            unique_filename = f"{timestamp}_{unique_id}.{ext}"

            object_key = f"images/{unique_filename}"

            s3_client = StorageService._get_r2_client()
            bucket_name = current_app.config.get("R2_BUCKET_NAME", "peek")

            file_storage.seek(0)

            logger.info(f"Uploading file to R2: {object_key}")

            def _upload():
                s3_client.upload_fileobj(
                    file_storage,
                    bucket_name,
                    object_key,
                    ExtraArgs={
                        "ContentType": f"image/{ext}",
                        "CacheControl": "public, max-age=31536000",
                    },
                )

            StorageService._retry_with_backoff(_upload)

            logger.info(f"Successfully uploaded file to R2: {object_key}")
            return object_key

        except ClientError as e:
            error_msg = f"Failed to upload to R2: {str(e)}"
            logger.error(error_msg)
            raise IOError(error_msg)
        except Exception as e:
            error_msg = f"Failed to save file: {str(e)}"
            logger.error(error_msg)
            raise IOError(error_msg)

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

            s3_client = StorageService._get_r2_client()
            bucket_name = current_app.config.get("R2_BUCKET_NAME", "peek")

            response = s3_client.get_object(Bucket=bucket_name, Key=image.filepath)
            data = response["Body"].read()

            mimetype_map = {
                "JPEG": "image/jpeg",
                "PNG": "image/png",
                "GIF": "image/gif",
                "BMP": "image/bmp",
                "WEBP": "image/webp",
            }
            mimetype = mimetype_map.get(image.format, "application/octet-stream")

            return (data, mimetype)

        except ClientError:
            return (None, None)
        except Exception:
            return (None, None)

    @staticmethod
    def get_public_url(image_id, expiration=86400):
        try:
            if not isinstance(image_id, int):
                image_id = int(image_id)

            image = db.session.get(Image, image_id)
            if not image:
                return None

            custom_domain = current_app.config.get("R2_PUBLIC_DOMAIN")
            if custom_domain:
                return f"{custom_domain.rstrip('/')}/{image.filepath}"

            s3_client = StorageService._get_r2_client()
            bucket_name = current_app.config.get("R2_BUCKET_NAME", "peek")

            url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": image.filepath},
                ExpiresIn=expiration,
            )
            return url

        except Exception:
            return None

    @staticmethod
    def get_annotated_image(image_id):
        try:
            if not isinstance(image_id, int):
                image_id = int(image_id)

            image = db.session.get(Image, image_id)
            if not image:
                return (None, None)

            base_key = image.filepath.rsplit(".", 1)[0]
            ext = image.filepath.rsplit(".", 1)[1]
            annotated_key = f"{base_key}_annotated.{ext}"

            s3_client = StorageService._get_r2_client()
            bucket_name = current_app.config.get("R2_BUCKET_NAME", "peek")

            try:
                response = s3_client.get_object(Bucket=bucket_name, Key=annotated_key)
                data = response["Body"].read()
            except ClientError:
                return StorageService.get_image(image_id)

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
    def upload_file_to_r2(file_data, object_key, content_type="image/jpeg"):
        try:
            s3_client = StorageService._get_r2_client()
            bucket_name = current_app.config.get("R2_BUCKET_NAME", "peek")

            if isinstance(file_data, str):
                with open(file_data, "rb") as f:
                    s3_client.upload_fileobj(
                        f,
                        bucket_name,
                        object_key,
                        ExtraArgs={
                            "ContentType": content_type,
                            "CacheControl": "public, max-age=31536000",
                        },
                    )
            else:
                file_obj = (
                    BytesIO(file_data) if isinstance(file_data, bytes) else file_data
                )
                s3_client.upload_fileobj(
                    file_obj,
                    bucket_name,
                    object_key,
                    ExtraArgs={
                        "ContentType": content_type,
                        "CacheControl": "public, max-age=31536000",
                    },
                )

            return object_key

        except ClientError as e:
            raise IOError(f"Failed to upload to R2: {str(e)}")
        except Exception as e:
            raise IOError(f"Failed to upload: {str(e)}")

    @staticmethod
    def download_from_r2(object_key):
        try:
            s3_client = StorageService._get_r2_client()
            bucket_name = current_app.config.get("R2_BUCKET_NAME", "peek")

            response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
            return response["Body"].read()

        except ClientError as e:
            raise IOError(f"Failed to download from R2: {str(e)}")
        except Exception as e:
            raise IOError(f"Failed to download: {str(e)}")

    @staticmethod
    def get_image_dimensions(file_storage_or_data):
        try:
            if hasattr(file_storage_or_data, "seek"):
                file_storage_or_data.seek(0)
                with PILImage.open(file_storage_or_data) as img:
                    dimensions = img.size
                file_storage_or_data.seek(0)
                return dimensions
            else:
                with PILImage.open(BytesIO(file_storage_or_data)) as img:
                    return img.size
        except Exception:
            return (None, None)

    @staticmethod
    def get_image_format(file_storage_or_data):
        try:
            if hasattr(file_storage_or_data, "seek"):
                file_storage_or_data.seek(0)
                with PILImage.open(file_storage_or_data) as img:
                    fmt = img.format
                file_storage_or_data.seek(0)
                return fmt
            else:
                with PILImage.open(BytesIO(file_storage_or_data)) as img:
                    return img.format
        except Exception:
            return None
