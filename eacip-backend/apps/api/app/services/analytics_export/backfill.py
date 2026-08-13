import logging

from sqlalchemy import select

from app.core.db import async_session_factory
from app.models.claims_analytics_export import ClaimsAnalyticsExport
from app.models.document_extraction import DocumentExtraction
from app.services.analytics_export.service import export_document

logger = logging.getLogger("analytics_export_backfill")


async def run_backfill() -> int:
    """
    Finds confirmed extractions with no export record (or a stale one — confirmed
    more recently than the last export) and exports them. Returns the count exported.
    """
    async with async_session_factory() as db:
        result = await db.execute(
            select(DocumentExtraction.document_id, DocumentExtraction.confirmed_at).where(
                DocumentExtraction.confirmed_at.is_not(None)
            )
        )
        confirmed = result.all()

        existing_exports = await db.execute(
            select(ClaimsAnalyticsExport.document_id, ClaimsAnalyticsExport.exported_at)
        )
        export_status = {row.document_id: row.exported_at for row in existing_exports.all()}

        to_export = [
            document_id
            for document_id, confirmed_at in confirmed
            if document_id not in export_status or export_status[document_id] < confirmed_at
        ]

        exported_count = 0
        for document_id in to_export:
            try:
                if await export_document(db, document_id):
                    exported_count += 1
            except Exception:
                logger.exception("Backfill export failed for document %s", document_id)

        if exported_count:
            logger.info("Backfill exported %d document(s)", exported_count)
        return exported_count
