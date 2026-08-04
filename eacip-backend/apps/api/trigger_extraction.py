import asyncio
import sys
import uuid
from app.core.queue import publish_extraction_job


async def main(doc_id_str):
    doc_id = uuid.UUID(doc_id_str)
    print(f"Publishing extraction job for {doc_id}")
    await publish_extraction_job(doc_id)
    print("Done")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
