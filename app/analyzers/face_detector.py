import os

import cv2


class FaceDetector:
    @staticmethod
    def detect(img_array):
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

        if not os.path.exists(cascade_path):
            return {"faces_detected": 0, "face_locations": []}

        face_cascade = cv2.CascadeClassifier(cascade_path)

        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )

        face_locations = []
        for x, y, w, h in faces:
            face_locations.append(
                {"x": int(x), "y": int(y), "width": int(w), "height": int(h)}
            )

        return {"faces_detected": len(faces), "face_locations": face_locations}
