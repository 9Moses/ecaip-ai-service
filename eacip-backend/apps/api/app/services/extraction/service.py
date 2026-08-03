from dataclasses import dataclass

from app.services.extraction.ocr_extractor import (
    extract_text_via_ocr_from_image,
    extract_text_via_ocr_from_pdf,
)
from app.services.extraction.pdf_extractor import extract_native_pdf_text


@dataclass
class ExtractionResult:
    text: str
    method: str
    page_count: int


def extract_document_text(content: bytes, mime_type: str) -> ExtractionResult:
    if mime_type == "application/pdf":
        text, page_count, has_sufficient_text = extract_native_pdf_text(content)
        if has_sufficient_text:
            return ExtractionResult(text=text, method="native_pdf", page_count=page_count)

        # Scanned/image-only PDF — fall back to OCR
        ocr_text, ocr_page_count = extract_text_via_ocr_from_pdf(content)
        return ExtractionResult(text=ocr_text, method="ocr", page_count=ocr_page_count)
    if mime_type in {"image/jpeg", "image/png", "image/tiff"}:
        text = extract_text_via_ocr_from_image(content)
        return ExtractionResult(text=text, method="ocr", page_count=1)

    raise ValueError(f"Unsupported mime type for extraction: {mime_type}")
