import cv2
import numpy as np


class QualityAnalyzer:
    @staticmethod
    def analyze(img_array):
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness_score = min(laplacian_var / 10, 100)

        if laplacian_var < 100:
            blur_level = "high"
        elif laplacian_var < 500:
            blur_level = "medium"
        else:
            blur_level = "low"

        rms_contrast = np.sqrt(np.mean((gray - gray.mean()) ** 2))
        contrast_score = min(rms_contrast, 100)

        quality_score = min((sharpness_score * 0.6) + (contrast_score * 0.4), 100)

        return {
            "sharpness_score": round(sharpness_score, 2),
            "blur_level": blur_level,
            "contrast_score": round(contrast_score, 2),
            "quality_score": round(quality_score, 2),
        }
