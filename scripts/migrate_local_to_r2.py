#!/usr/bin/env python3
"""
Migration script to upload existing local files to Cloudflare R2.

This script:
1. Reads all Image records from the database
2. Uploads local files from the uploads/ directory to R2
3. Updates database records with R2 object keys
4. Supports dry-run mode for safety

Usage:
    python scripts/migrate_local_to_r2.py [--dry-run] [--verbose]
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from dotenv import load_dotenv

from app import create_app, db
from app.models import Image

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_r2_client(app):
    """Create and return an R2 client."""
    account_id = app.config.get("R2_ACCOUNT_ID")
    access_key = app.config.get("R2_ACCESS_KEY_ID")
    secret_key = app.config.get("R2_SECRET_ACCESS_KEY")
    region = app.config.get("R2_REGION", "auto")

    if not all([account_id, access_key, secret_key]):
        raise ValueError("R2 credentials not configured. Check your .env file.")

    endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version="s3v4"),
        region_name=region,
    )


def verify_bucket_exists(s3_client, bucket_name):
    """Verify that the R2 bucket exists."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        logger.info(f"✓ Bucket '{bucket_name}' exists and is accessible")
        return True
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "404":
            logger.error(f"✗ Bucket '{bucket_name}' does not exist")
        elif error_code == "403":
            logger.error(f"✗ Access denied to bucket '{bucket_name}'")
        else:
            logger.error(f"✗ Error accessing bucket: {error_code}")
        return False


def migrate_file(s3_client, bucket_name, image_record, dry_run=False):
    """
    Migrate a single file from local storage to R2.

    Returns:
        tuple: (success: bool, new_key: str or None)
    """
    filepath = image_record.filepath

    # Check if file exists locally
    if not os.path.exists(filepath):
        logger.warning(f"✗ File not found: {filepath} (Image ID: {image_record.id})")
        return (False, None)

    # Check if already migrated (filepath looks like R2 key)
    if filepath.startswith("images/"):
        logger.info(f"⊘ Already migrated: {filepath} (Image ID: {image_record.id})")
        return (True, filepath)

    # Generate R2 object key based on filename
    filename = os.path.basename(filepath)
    object_key = f"images/{filename}"

    # Check for annotated version
    annotated_path = (
        filepath.rsplit(".", 1)[0] + "_annotated." + filepath.rsplit(".", 1)[1]
    )
    has_annotated = os.path.exists(annotated_path)

    if dry_run:
        logger.info(f"[DRY RUN] Would upload: {filepath} -> {object_key}")
        if has_annotated:
            annotated_key = (
                object_key.rsplit(".", 1)[0]
                + "_annotated."
                + object_key.rsplit(".", 1)[1]
            )
            logger.info(f"[DRY RUN] Would upload: {annotated_path} -> {annotated_key}")
        return (True, object_key)

    try:
        # Upload original file
        ext = filename.rsplit(".", 1)[1].lower() if "." in filename else "jpg"

        with open(filepath, "rb") as f:
            s3_client.upload_fileobj(
                f,
                bucket_name,
                object_key,
                ExtraArgs={
                    "ContentType": f"image/{ext}",
                    "CacheControl": "public, max-age=31536000",
                },
            )

        logger.info(f"✓ Uploaded: {filepath} -> {object_key}")

        # Upload annotated file if it exists
        if has_annotated:
            annotated_key = (
                object_key.rsplit(".", 1)[0]
                + "_annotated."
                + object_key.rsplit(".", 1)[1]
            )
            with open(annotated_path, "rb") as f:
                s3_client.upload_fileobj(
                    f,
                    bucket_name,
                    annotated_key,
                    ExtraArgs={
                        "ContentType": f"image/{ext}",
                        "CacheControl": "public, max-age=31536000",
                    },
                )
            logger.info(f"✓ Uploaded annotated: {annotated_path} -> {annotated_key}")

        return (True, object_key)

    except ClientError as e:
        logger.error(f"✗ Upload failed for {filepath}: {str(e)}")
        return (False, None)
    except Exception as e:
        logger.error(f"✗ Unexpected error for {filepath}: {str(e)}")
        return (False, None)


def update_database_record(image_record, new_key, dry_run=False):
    """Update database record with new R2 object key."""
    if dry_run:
        logger.info(
            f"[DRY RUN] Would update DB: Image {image_record.id} filepath: {image_record.filepath} -> {new_key}"
        )
        return True

    try:
        image_record.filepath = new_key
        db.session.commit()
        logger.info(f"✓ Updated DB: Image {image_record.id} -> {new_key}")
        return True
    except Exception as e:
        logger.error(f"✗ DB update failed for Image {image_record.id}: {str(e)}")
        db.session.rollback()
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Migrate local image files to Cloudflare R2"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.dry_run:
        logger.info("=" * 60)
        logger.info("DRY RUN MODE - No changes will be made")
        logger.info("=" * 60)

    # Create Flask app context
    app = create_app()

    with app.app_context():
        try:
            # Setup R2 client
            logger.info("Setting up R2 connection...")
            s3_client = get_r2_client(app)
            bucket_name = app.config.get("R2_BUCKET_NAME", "peek")

            # Verify bucket exists
            if not verify_bucket_exists(s3_client, bucket_name):
                logger.error("Cannot proceed without valid bucket access")
                sys.exit(1)

            # Get all images from database
            logger.info("Fetching image records from database...")
            images = Image.query.all()
            total_images = len(images)

            if total_images == 0:
                logger.info("No images found in database")
                sys.exit(0)

            logger.info(f"Found {total_images} image records")
            logger.info("=" * 60)

            # Track statistics
            stats = {
                "total": total_images,
                "uploaded": 0,
                "skipped": 0,
                "failed": 0,
                "db_updated": 0,
            }

            # Process each image
            for idx, image in enumerate(images, 1):
                logger.info(f"Processing {idx}/{total_images}: Image ID {image.id}")

                success, new_key = migrate_file(
                    s3_client, bucket_name, image, args.dry_run
                )

                if success and new_key:
                    if new_key != image.filepath:
                        # Update database
                        if update_database_record(image, new_key, args.dry_run):
                            stats["uploaded"] += 1
                            stats["db_updated"] += 1
                        else:
                            stats["failed"] += 1
                    else:
                        stats["skipped"] += 1
                else:
                    stats["failed"] += 1

                logger.info("")  # Blank line for readability

            # Print summary
            logger.info("=" * 60)
            logger.info("MIGRATION SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Total images:        {stats['total']}")
            logger.info(f"Successfully uploaded: {stats['uploaded']}")
            logger.info(f"Already migrated:    {stats['skipped']}")
            logger.info(f"Failed:              {stats['failed']}")
            logger.info(f"DB records updated:  {stats['db_updated']}")
            logger.info("=" * 60)

            if args.dry_run:
                logger.info(
                    "\nThis was a DRY RUN. Run without --dry-run to perform migration."
                )
            elif stats["failed"] > 0:
                logger.warning(f"\nMigration completed with {stats['failed']} failures")
                sys.exit(1)
            else:
                logger.info("\n✓ Migration completed successfully!")

        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    main()
