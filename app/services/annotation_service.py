import os

import cv2
import numpy as np
from PIL import Image


class AnnotationService:
    @staticmethod
    def create_annotated_image(image_path, face_locations):
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Failed to load image: {image_path}")

        for face in face_locations:
            x = face.get("x", 0)
            y = face.get("y", 0)
            width = face.get("width", 0)
            height = face.get("height", 0)

            top_left = (x, y)
            bottom_right = (x + width, y + height)

            cv2.rectangle(img, top_left, bottom_right, (0, 255, 0), 2)

        directory = os.path.dirname(image_path)
        filename = os.path.basename(image_path)
        name, ext = os.path.splitext(filename)
        annotated_filename = f"{name}_annotated{ext}"
        annotated_path = os.path.join(directory, annotated_filename)

        cv2.imwrite(annotated_path, img)

        return annotated_path
