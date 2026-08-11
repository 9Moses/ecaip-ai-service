import asyncio
from app.core.db import async_session_factory
from app.models.document import Document
from app.services.rag.indexing import index_document
from sqlalchemy import select

DOC_IDS = [
    "88adb2cb-3585-4d0a-a0a2-3af273acd8c1",
    "f2e236fe-2d03-44f9-803a-2b4008179bc7",
    "376d9fe7-dcb1-401a-b3ae-71b74e0dfa38",
    "2cb3373f-5e06-413c-8b72-65380a0e9ba3",
    "edbb9528-51a0-4377-9985-60fe25c8278c",
    "e9b56fed-36ab-498e-b8b8-c77f1d061be9",
    "4c9b4d32-8224-4843-ab87-1453ed61f5f1",
]


async def reindex_all():
    async with async_session_factory() as db:
        for doc_id in DOC_IDS:
            doc = await db.scalar(select(Document).where(Document.id == doc_id))
            if doc is None:
                print(f"[SKIP] {doc_id} — not found in DB")
                continue
            if not doc.raw_text:
                print(f"[SKIP] {doc.file_name} — no raw text")
                continue
            try:
                chunk_count = index_document(
                    document_id=doc.id,
                    owner_id=doc.owner_id,
                    document_type=doc.document_type,
                    raw_text=doc.raw_text,
                )
                print(f"[OK] {doc.file_name} — {chunk_count} chunk(s)")
            except Exception as e:
                print(f"[ERROR] {doc.file_name} — {e}")


asyncio.run(reindex_all())
