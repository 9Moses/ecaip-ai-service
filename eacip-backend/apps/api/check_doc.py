import asyncio
from app.core.db import async_session_factory
from app.models.document import Document
from sqlalchemy import select


async def check():
    async with async_session_factory() as db:
        doc = await db.scalar(
            select(Document).where(Document.id == "0e806787-babf-4609-8aac-7b5fb5b392a6")
        )
        if doc is None:
            print("status: not found")
        else:
            print("status:", doc.status)
            print("raw_text len:", len(doc.raw_text) if doc.raw_text else 0)


asyncio.run(check())
