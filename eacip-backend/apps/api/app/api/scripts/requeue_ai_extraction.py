import asyncio
import sys
import uuid

from app.core.queue import publish_ai_extraction_job


async def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m app.api.scripts.requeue_ai_extraction <document_id>")
        sys.exit(1)

    document_id = uuid.UUID(sys.argv[1])
    await publish_ai_extraction_job(document_id)
    print(f"Requeued AI extraction for document {document_id}")


if __name__ == "__main__":
    asyncio.run(main())
