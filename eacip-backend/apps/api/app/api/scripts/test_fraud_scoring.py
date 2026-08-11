"""
Usage: python -m app.api.scripts.test_fraud_scoring <document_id>
Requires the document to already have confirmed/extracted structured fields.
"""

import asyncio
import sys
import uuid

from sqlalchemy import select

from app.core.db import async_session_factory
from app.models.document import Document
from app.models.document_extraction import DocumentExtraction
from app.services.fraud.service import assess_fraud_risk


async def main() -> None:
    document_id = uuid.UUID(sys.argv[1])

    async with async_session_factory() as db:
        document = await db.scalar(select(Document).where(Document.id == document_id))
        extraction = await db.scalar(
            select(DocumentExtraction).where(DocumentExtraction.document_id == document_id)
        )
        if document is None or extraction is None:
            print("Document or its AI extraction not found.")
            sys.exit(1)

        assessment = await assess_fraud_risk(
            db=db,
            document_id=document.id,
            owner_id=document.owner_id,
            document_type=document.document_type,
            extracted_fields=extraction.extracted_fields,
            raw_text=document.raw_text or "",
        )

        print(f"Score: {assessment.score}")
        print(f"Should flag: {assessment.should_flag}")
        print(f"Evidence ({len(assessment.evidence)} findings):")
        for e in assessment.evidence:
            print(f"  - [{e['severity']}] {e['field']}: {e['message']}")
        if assessment.rationale:
            print(f"\nRationale:\n{assessment.rationale}")


if __name__ == "__main__":
    asyncio.run(main())
