"""
Usage: python app/api/scripts/test_structured_extraction.py <document_id>
Runs structured extraction against an already-OCR'd document's raw_text.
"""

import asyncio
import sys
import uuid

from sqlalchemy import select

from app.core.db import async_session_factory
from app.models.document import Document
from app.services.ai_extraction.service import extract_structured_fields


async def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python app/api/scripts/test_structured_extraction.py <document_id>")
        sys.exit(1)

    document_id = uuid.UUID(sys.argv[1])

    async with async_session_factory() as db:
        document = await db.scalar(select(Document).where(Document.id == document_id))
        if document is None or not document.raw_text:
            print("Document not found or has no extracted raw_text yet.")
            sys.exit(1)

        result = await extract_structured_fields(document.document_type, document.raw_text)

        print(f"Status: {result.status}")
        print(f"Extracted fields:\n{result.extracted_fields}")
        if result.error_message:
            print(f"Error: {result.error_message}")


if __name__ == "__main__":
    asyncio.run(main())
