import fitz
import pytest

from app.services.extraction.service import extract_document_text


def _make_native_bytes(text: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_native_pdf_uses_direct_text_extraction():
    pdf_bytes = _make_native_bytes("Claim Number: EACIP-TEST-0001\nPolicyholder: Jane Doe")
    result = extract_document_text(pdf_bytes, "application/pdf")

    assert result.method == "native_pdf"
    assert "EACIP-TEST-0001" in result.text
    assert result.page_count == 1


def test_unsupported_mime_type_raises():
    with pytest.raises(ValueError):
        extract_document_text(b"irrelevant", "application/zip")
