from io import BytesIO

from flask import Blueprint, current_app, jsonify, request, send_file
from werkzeug.utils import secure_filename

from app import db
from app.services.image_service import ImageService
from app.services.storage_service import StorageService

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/health", methods=["GET"])
def health_check():
    health_status = {"status": "ok"}

    try:
        db.session.execute(db.text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception:
        health_status["database"] = "disconnected"
        health_status["status"] = "degraded"

    try:
        from celery import current_app as celery_app

        celery_app.connection().ensure_connection(max_retries=1)
        health_status["redis"] = "connected"
    except Exception:
        health_status["redis"] = "disconnected"
        health_status["status"] = "degraded"

    status_code = 200 if health_status["status"] == "ok" else 503
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

        filepath = StorageService.save_file(file)

        width, height = StorageService.get_image_dimensions(filepath)
        format = StorageService.get_image_format(filepath)

        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)

        result = ImageService.create_analysis_task(
            filepath, secure_filename(file.filename), file_size, format, width, height
        )

        return jsonify(result), 202

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
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
