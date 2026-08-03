import io

import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image


def extract_text_via_ocr_from_image(content: bytes) -> str:
    image = Image.open(io.BytesIO(content))
    return str(pytesseract.image_to_string(image)).strip()


def extract_text_via_ocr_from_pdf(content: bytes) -> tuple[str, int]:
    """
    Rasterizes each PDF page to an image, then OCRs each one.
    Returns (combined_text, page_count).
    """
    images = convert_from_bytes(content, dpi=300)
    page_text = [str(pytesseract.image_to_string(img)).strip() for img in images]
    return "\n\n".join(page_text), len(images)
