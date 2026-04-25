import pytesseract
from PIL import Image
import io
import os

class OCRProcessor:
    """Performs OCR on image binaries using Tesseract."""

    def __init__(self):
        # Tesseract is confirmed to be in the PATH on this system
        pass

    def extract_text(self, image_bytes: bytes) -> str:
        """Extracts text from image bytes."""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception as e:
            print(f"OCR Error: {e}")
            return ""

    def process_file(self, image_path: str) -> str:
        """Extracts text from a local image file."""
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception as e:
            print(f"OCR Error processing {image_path}: {e}")
            return ""
