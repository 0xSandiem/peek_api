import cv2
import numpy as np
from PIL import Image

from app.analyzers.color_analyzer import ColorAnalyzer
from app.analyzers.face_detector import FaceDetector
from app.analyzers.quality_analyzer import QualityAnalyzer
from app.analyzers.scene_detector import SceneDetector
from app.analyzers.text_extractor import TextExtractor


class CVService:
    @staticmethod
    def process_image(filepath):
        try:
            pil_image = Image.open(filepath)
            img_array = np.array(pil_image.convert("RGB"))

            color_results = ColorAnalyzer.analyze(img_array)
            face_results = FaceDetector.detect(img_array)
            quality_results = QualityAnalyzer.analyze(img_array)
            scene_results = SceneDetector.detect(img_array)
            text_results = TextExtractor.extract(img_array)

            insights = {
                **color_results,
                **face_results,
                **quality_results,
                **scene_results,
                **text_results,
            }

            return insights

        except Exception as e:
            return {"error": str(e)}
