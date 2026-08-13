from datetime import date
from typing import Any

from app.models.document import Document
from app.models.document_extraction import DocumentExtraction
from app.models.fraud_flag import FraudFlag


def _parse_date(value: str | date | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


def build_export_record(
    document: Document,
    extraction: DocumentExtraction,
    fraud_flag: FraudFlag | None,
) -> dict[str, Any]:
    fields = extraction.extracted_fields or {}

    return {
        "document_id": document.id,
        "claim_number": fields.get("claim_number"),
        "policy_number": fields.get("policy_number"),
        "document_type": document.document_type,
        "incident_date": _parse_date(fields.get("incident_date")),
        "filing_date": _parse_date(fields.get("filing_date")),
        "claimed_amount": fields.get("claimed_amount"),
        "fraud_score": float(fraud_flag.score) if fraud_flag else None,
        "fraud_status": fraud_flag.status if fraud_flag else None,
        "inconsistency_count": len(extraction.inconsistencies or []),
        "confirmed_by": extraction.confirmed_by,
        "confirmed_at": extraction.confirmed_at,
    }
