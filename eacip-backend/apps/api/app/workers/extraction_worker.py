import uuid as uuid_module
import asyncio
import json
import logging

import aio_pika
from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import async_session_factory
from app.core.storage import download_file
from app.models.document import Document
from app.services.extraction.service import extract_document_text
from app.core.queue import publish_ai_extraction_job, publish_indexing_job
from app.models.document_extraction import DocumentExtraction
from app.services.ai_extraction.service import extract_structured_fields
from app.services.ai_extraction.service import (
    detect_inconsistencies,
    summarize_document,
)
from app.services.rag.indexing import index_document

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("extraction_worker")

settings = get_settings()


async def process_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    async with message.process():
        payload = json.loads(message.body.decode())
        document_id = payload["document_id"]
        logger.info("Processing document %s", document_id)

        async with async_session_factory() as db:
            document = await db.scalar(select(Document).where(Document.id == document_id))
            if document is None:
                logger.warning("Document %s not found - skipping", document_id)
                return

            document.status = "processing"
            await db.commit()

            extraction_succeeded = False
            try:
                content = download_file(document.storage_path)
                result = extract_document_text(content, document.mime_type)

                document.raw_text = result.text
                document.extraction_method = result.method
                document.page_count = result.page_count
                document.status = "extracted"
                document.error_message = None
                extraction_succeeded = True
                logger.info(
                    "Extracted document %s via %s (%d chars, %d pages)",
                    document_id,
                    result.method,
                    len(result.text),
                    result.page_count,
                )
            except Exception as exc:
                logger.exception("Extraction failed for document %s", document_id)
                document.status = "failed"
                document.error_message = str(exc)

            await db.commit()

            # Only publish downstream jobs when extraction actually produced text.
            # Publishing on failure would silently enqueue jobs that skip due to
            # missing raw_text, leaving the vector store empty and the chatbot
            # with no document context.
            if extraction_succeeded:
                await publish_ai_extraction_job(document.id)
                await publish_indexing_job(document.id)
            else:
                logger.warning(
                    "Skipping AI extraction and indexing for document %s due to extraction failure",
                    document_id,
                )

            return


async def process_ai_extraction_message(
    message: aio_pika.abc.AbstractIncomingMessage,
) -> None:
    async with message.process():
        payload = json.loads(message.body.decode())
        document_id = uuid_module.UUID(payload["document_id"])
        logger.info("Running structure AI extraction for document %s", document_id)

        async with async_session_factory() as db:
            document = await db.scalar(select(Document).where(Document.id == document_id))
            if document is None or not document.raw_text:
                logger.warning(
                    """
                Document %s missing or has no raw_text - skipping AI extraction
                """,
                    document_id,
                )
                return

            extraction = await db.scalar(
                select(DocumentExtraction).where(DocumentExtraction.document_id == document_id)
            )
            if extraction is None:
                extraction = DocumentExtraction(document_id=document_id, status="processing")
                db.add(extraction)
            else:
                extraction.status = "processing"
            await db.commit()

            result = await extract_structured_fields(document.document_type, document.raw_text)

            extraction.status = result.status
            extraction.extracted_fields = result.extracted_fields
            extraction.raw_llm_output = result.raw_llm_output
            extraction.error_message = result.error_message

            if result.status == "completed":
                extraction.summary = await summarize_document(document.raw_text)
                extraction.inconsistencies = await detect_inconsistencies(
                    document.document_type, result.extracted_fields, document.raw_text
                )

            await db.commit()

            logger.info(
                "AI extraction from document %s finished with status %s", document_id, result.status
            )


async def process_indexing_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    async with message.process():
        payload = json.loads(message.body.decode())
        document_id = uuid_module.UUID(payload["document_id"])
        logger.info("Indexing document %s into Qdrant", document_id)

        async with async_session_factory() as db:
            document = await db.scalar(select(Document).where(Document.id == document_id))
            if document is None or not document.raw_text:
                logger.warning(
                    """
                    Document %s missing or has no raw_text —
                    skipping indexing
                    """,
                    document_id,
                )
                return

            try:
                chunk_count = index_document(
                    document_id=document.id,
                    owner_id=document.owner_id,
                    document_type=document.document_type,
                    raw_text=document.raw_text,
                )
                logger.info("Indexed %d chunks for document %s", chunk_count, document_id)
            except Exception:
                logger.exception("Indexing failed for document %s — message will be nacked for retry", document_id)
                raise  # re-raise so aio_pika nacks the message and retries


async def main() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=2)
        # process up to 2 documents concurrently per worker

        ocr_queue = await channel.declare_queue(settings.document_extraction_queue, durable=True)
        ai_queue = await channel.declare_queue(settings.ai_extraction_queue, durable=True)
        indexing_queue = await channel.declare_queue(settings.indexing_queue, durable=True)

        logger.info("Worker started,consuming OCR and AI extraction queues...")

        await ocr_queue.consume(process_message)
        await ai_queue.consume(process_ai_extraction_message)
        await indexing_queue.consume(process_indexing_message)

        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
