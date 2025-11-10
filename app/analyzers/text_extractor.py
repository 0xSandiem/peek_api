import numpy as np
import pytesseract
from PIL import Image


class TextExtractor:
    @staticmethod
    def extract(img_array):
        pil_image = Image.fromarray(img_array)

        try:
            extracted_text = pytesseract.image_to_string(pil_image).strip()
        except Exception:
            extracted_text = ""

        word_count = len(extracted_text.split()) if extracted_text else 0
        text_found = word_count > 0

        return {
            "text_found": text_found,
            "extracted_text": extracted_text,
            "word_count": word_count,
        }
