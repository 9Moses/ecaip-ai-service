"""
Manual test script — not part of the automated test suite.
Usage: python scripts/test_extraction.py /path/to/file.pdf
"""

import sys

import magic

from app.services.extraction.service import extract_document_text


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/test_extraction.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    with open(file_path, "rb") as f:
        content = f.read()

    mime_type = magic.from_buffer(content, mime=True)
    print(f"Detected MIME type: {mime_type}")

    result = extract_document_text(content, mime_type)
    print(f"Extraction method: {result.method}")
    print(f"Page count: {result.page_count}")
    print(f"Extracted text ({len(result.text)} chars):\n")
    print(result.text[:2000])
    if len(result.text) > 2000:
        print(f"\n... [{len(result.text) - 2000} more characters truncated]")


if __name__ == "__main__":
    main()
