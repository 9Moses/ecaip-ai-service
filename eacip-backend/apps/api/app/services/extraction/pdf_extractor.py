import fitz

MIN_CHARS_PER_PAGE_TO_SKIP_OCR = 20
"""
If a PDF page yields fewer than this many characters via direct extraction,
treat it as image-only (scanned) and hand it off to OCR instead — a native
PDF with an actual text layer will always yield far more than this per page.
"""


def extract_native_pdf_text(content: bytes) -> tuple[str, int, bool]:
    """
    Returns (text, page_count, has_sufficient_text).
    has_sufficient_text is False if the PDF appears to be scanned/image-only,
    signaling the caller should fall back to OCR instead.
    """
    doc = fitz.open(stream=content, filetype="pdf")
    page_count = doc.page_count
    pages_text: list[str] = []
    sparse_pages = 0

    for page in doc:
        page_text = page.get_text("text")
        pages_text.append(page_text)
        if len(page_text.strip()) < MIN_CHARS_PER_PAGE_TO_SKIP_OCR:
            sparse_pages += 1

    doc.close()

    full_text = "\n\n".join(pages_text).strip()
    # If most pages are sparse, this PDF is very likely scanned images, not native text.
    has_sufficient_text = sparse_pages < page_count / 2 if page_count else False

    return full_text, page_count, has_sufficient_text
