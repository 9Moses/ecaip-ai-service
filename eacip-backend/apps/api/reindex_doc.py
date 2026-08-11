import asyncio
from app.core.db import async_session_factory
from app.models.document import Document
from app.services.rag.indexing import index_document
from sqlalchemy import select


async def reindex():
    async with async_session_factory() as db:
        doc = await db.scalar(
            select(Document).where(Document.id == "0e806787-babf-4609-8aac-7b5fb5b392a6")
        )
        if doc is None or not doc.raw_text:
            print("Document not found or has no raw text!")
            return

        print(f"Re-indexing document {doc.id} (status: {doc.status}, {len(doc.raw_text)} chars)...")
        chunk_count = index_document(
            document_id=doc.id,
            owner_id=doc.owner_id,
            document_type=doc.document_type,
            raw_text=doc.raw_text,
        )
        print(f"Done! Indexed {chunk_count} chunks into Qdrant.")


asyncio.run(reindex())
