import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claims_analytics_export import ClaimsAnalyticsExport
from app.models.document import Document
from app.models.document_extraction import DocumentExtraction
from app.models.fraud_flag import FraudFlag
from app.services.analytics_export.transform import build_export_record

logger = logging.getLogger("analytics_export")


async def export_document(db: AsyncSession, document_id: uuid.UUID) -> bool:
    """
    Builds/refreshes the analytics export record for a single document.
    Returns True if a record was written, False if the document isn't
    eligible yet (e.g., extraction not confirmed).
    """
    document = await db.scalar(select(Document).where(Document.id == document_id))
    extraction = await db.scalar(
        select(DocumentExtraction).where(DocumentExtraction.document_id == document_id)
    )

    if document is None or extraction is None or extraction.confirmed_at is None:
        # Only confirmed (human-reviewed) data is exported downstream — matches this
        # system's human-in-the-loop principle: unconfirmed LLM output shouldn't feed
        # a reserve estimation model as if it were verified fact.
        return False

    try:
        fraud_flag = await db.scalar(select(FraudFlag).where(FraudFlag.document_id == document_id))
        record_data = build_export_record(document, extraction, fraud_flag)

        existing = await db.scalar(
            select(ClaimsAnalyticsExport).where(ClaimsAnalyticsExport.document_id == document_id)
        )
        if existing is None:
            db.add(ClaimsAnalyticsExport(**record_data))
        else:
            for key, value in record_data.items():
                setattr(existing, key, value)
    except Exception as e:
        logger.error(
            "Failed to export document %s to analytics table: %s",
            document_id,
            e,
        )  # non-fatal

    await db.commit()
    logger.info("Exported analytics record for document %s", document_id)
    return True
