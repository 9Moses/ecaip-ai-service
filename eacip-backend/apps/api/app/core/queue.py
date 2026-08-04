import json
import uuid

import aio_pika

from app.core.config import get_settings

settings = get_settings()


async def publish_extraction_job(document_id: uuid.UUID) -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.declare_queue(settings.document_extraction_queue, durable=True)
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps({"document_id": str(document_id)}).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=settings.document_extraction_queue,
        )
