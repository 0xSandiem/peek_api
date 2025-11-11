import cv2
import numpy as np


class SceneDetector:
    @staticmethod
    def detect(img_array):
        hsv = cv2.cvtColor(img_array, cv2.COLOR_RGB2HSV)
        h, s, v = cv2.split(hsv)

        avg_saturation = np.mean(s)
        avg_value = np.mean(v)

        blue_mask = cv2.inRange(hsv, np.array([90, 50, 50]), np.array([130, 255, 255]))
        green_mask = cv2.inRange(hsv, np.array([35, 50, 50]), np.array([85, 255, 255]))

        blue_ratio = np.count_nonzero(blue_mask) / (
            img_array.shape[0] * img_array.shape[1]
        )
        green_ratio = np.count_nonzero(green_mask) / (
            img_array.shape[0] * img_array.shape[1]
        )

        scene_type = "indoor"
        confidence = 0.5

        if blue_ratio > 0.3 and avg_value > 100:
            scene_type = "outdoor"
            confidence = min(0.6 + (blue_ratio * 0.4), 1.0)
        elif green_ratio > 0.3:
            scene_type = "nature"
            confidence = min(0.6 + (green_ratio * 0.4), 1.0)
        elif avg_value < 80:
            scene_type = "indoor"
            confidence = 0.7
        elif avg_saturation < 50:
            scene_type = "indoor"
            confidence = 0.6

        return {"scene_type": scene_type, "scene_confidence": round(confidence, 2)}
