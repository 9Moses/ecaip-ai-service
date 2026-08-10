"""
Usage: python app/api/scripts/test_chunking.py <document_id>
"""

import asyncio
import sys
import uuid

from sqlalchemy import select

from app.core.db import async_session_factory
from app.models.document import Document
from app.services.rag.chunker import chunk_text


async def main() -> None:
    document_id = uuid.UUID(sys.argv[1])
    async with async_session_factory() as db:
        document = await db.scalar(select(Document).where(Document.id == document_id))
        if document is None or not document.raw_text:
            print("Document not found or has no raw_text.")
            sys.exit(1)

        chunks = chunk_text(document.raw_text)
        print(f"Produced {len(chunks)} chunks from {len(document.raw_text)} characters.\n")
        for chunk in chunks:
            print(f"--- Chunk {chunk.chunk_index} (~{len(chunk.text.split())} words) ---")
            print(chunk.text[:200] + ("..." if len(chunk.text) > 200 else ""))
            print()


if __name__ == "__main__":
    asyncio.run(main())
