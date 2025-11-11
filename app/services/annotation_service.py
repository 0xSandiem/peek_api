import os

import cv2
import numpy as np


class AnnotationService:
    @staticmethod
    def create_annotated_image(image_data_or_key, face_locations, storage_service=None):
        if storage_service:
            if isinstance(image_data_or_key, str):
                image_data = storage_service.download_from_r2(image_data_or_key)
            else:
                image_data = image_data_or_key

            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            if not os.path.exists(image_data_or_key):
                raise FileNotFoundError(f"Image file not found: {image_data_or_key}")
            img = cv2.imread(image_data_or_key)

        if img is None:
            raise ValueError("Failed to load image")

        for face in face_locations:
            x = face.get("x", 0)
            y = face.get("y", 0)
            width = face.get("width", 0)
            height = face.get("height", 0)

            top_left = (x, y)
            bottom_right = (x + width, y + height)

            cv2.rectangle(img, top_left, bottom_right, (0, 255, 0), 2)

        success, encoded_img = cv2.imencode(".jpg", img)
        if not success:
            raise ValueError("Failed to encode annotated image")

        annotated_data = encoded_img.tobytes()

        if storage_service:
            if isinstance(image_data_or_key, str):
                base_key = image_data_or_key.rsplit(".", 1)[0]
                ext = image_data_or_key.rsplit(".", 1)[1]
                annotated_key = f"{base_key}_annotated.{ext}"
            else:
                annotated_key = "images/annotated_temp.jpg"

            storage_service.upload_file_to_r2(
                annotated_data, annotated_key, content_type="image/jpeg"
            )
            return annotated_key
        else:
            directory = os.path.dirname(image_data_or_key)
            filename = os.path.basename(image_data_or_key)
            name, ext = os.path.splitext(filename)
            annotated_filename = f"{name}_annotated{ext}"
            annotated_path = os.path.join(directory, annotated_filename)

            cv2.imwrite(annotated_path, img)
            return annotated_path
