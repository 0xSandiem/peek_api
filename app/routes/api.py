import logging
from io import BytesIO

from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename

from app import db
from app.services.image_service import ImageService
from app.services.storage_service import StorageService

bp = Blueprint("api", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)


@bp.route("/health", methods=["GET"])
def health_check():
    health_status = {"status": "ok"}
    critical_failure = False

    try:
        db.session.execute(db.text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception:
        health_status["database"] = "disconnected"
        health_status["status"] = "degraded"
        critical_failure = True

    try:
        from celery import current_app as celery_app

        celery_app.connection().ensure_connection(max_retries=1)
        health_status["redis"] = "connected"
    except Exception:
        health_status["redis"] = "disconnected"

    status_code = 503 if critical_failure else 200
    return jsonify(health_status), status_code


@bp.route("/analyze", methods=["POST"])
def analyze_image():
    try:
        if "image" not in request.files:
            return jsonify({"error": "No image file provided"}), 400

        file = request.files["image"]

        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        if not StorageService.validate_file(file):
            return jsonify({"error": "Invalid file type or size"}), 400

        file.seek(0)
        width, height = StorageService.get_image_dimensions(file)
        file.seek(0)
        format = StorageService.get_image_format(file)
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)

        filepath = StorageService.save_file(file)

        result = ImageService.create_analysis_task(
            filepath, secure_filename(file.filename), file_size, format, width, height
        )

        public_url = StorageService.get_public_url(result["id"], expiration=86400)
        result["public_url"] = public_url

        return jsonify(result), 202

    except ValueError as e:
        logger.error(f"Validation error in analyze_image: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception(f"Error in analyze_image: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/results/<int:image_id>", methods=["GET"])
def get_results(image_id):
    try:
        result = ImageService.get_analysis_results(image_id)

        if result is None:
            return jsonify({"error": "Image not found"}), 404

        if result["status"] == "processing":
            return jsonify(result), 202

        return jsonify(result), 200

    except ValueError:
        return jsonify({"error": "Invalid image ID"}), 400
    except Exception:
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/image/<int:image_id>/original", methods=["GET"])
def get_original_image(image_id):
    try:
        data, mimetype = StorageService.get_image(image_id)

        if data is None:
            return jsonify({"error": "Image not found"}), 404

        return send_file(BytesIO(data), mimetype=mimetype, as_attachment=False)

    except ValueError:
        return jsonify({"error": "Invalid image ID"}), 400
    except Exception:
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/image/<int:image_id>/annotated", methods=["GET"])
def get_annotated_image(image_id):
    try:
        data, mimetype = StorageService.get_annotated_image(image_id)

        if data is None:
            return jsonify({"error": "Image not found"}), 404

        return send_file(BytesIO(data), mimetype=mimetype, as_attachment=False)

    except ValueError:
        return jsonify({"error": "Invalid image ID"}), 400
    except Exception:
        return jsonify({"error": "Internal server error"}), 500


@bp.route("/image/<int:image_id>/url", methods=["GET"])
def get_image_url(image_id):
    try:
        expiration = request.args.get("expiration", 86400, type=int)

        if expiration < 60 or expiration > 604800:
            return (
                jsonify({"error": "Expiration must be between 60 and 604800 seconds"}),
                400,
            )

        public_url = StorageService.get_public_url(image_id, expiration=expiration)

        if public_url is None:
            return jsonify({"error": "Image not found"}), 404

        return (
            jsonify(
                {"image_id": image_id, "url": public_url, "expires_in": expiration}
            ),
            200,
        )

    except ValueError:
        return jsonify({"error": "Invalid image ID"}), 400
    except Exception:
        return jsonify({"error": "Internal server error"}), 500
