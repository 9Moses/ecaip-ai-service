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

            try:
                content = download_file(document.storage_path)
                result = extract_document_text(content, document.mime_type)

                document.raw_text = result.text
                document.extraction_method = result.method
                document.page_count = result.page_count
                document.status = "extracted"
                document.error_message = None
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


async def main() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=2)  # process up to 2 documents concurrently per worker
        queue = await channel.declare_queue(settings.document_extraction_queue, durable=True)

        logger.info(
            "Worker started, waiting for extraction jobs on '%s'...",
            settings.document_extraction_queue,
        )

        await queue.consume(process_message, no_ack=False)

        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
