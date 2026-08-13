from datetime import UTC, datetime
import uuid

from app.models.document import Document
from app.models.document_extraction import DocumentExtraction
from app.models.fraud_flag import FraudFlag
from app.services.analytics_export.transform import build_export_record


def test_build_export_record_with_fraud_flag():
    document = Document(
        id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        file_name="test.pdf",
        file_hash="abc123",
        mime_type="application/pdf",
        document_type="claim_form",
        storage_path="test/path.pdf",
    )
    extraction = DocumentExtraction(
        document_id=document.id,
        extracted_fields={
            "claim_number": "C-1001",
            "policy_number": "P-500",
            "incident_date": "2026-01-01",
            "filing_date": "2026-01-05",
            "claimed_amount": 1200.50,
        },
        inconsistencies=[{"severity": "high", "field": "x", "message": "y", "source": "rule"}],
        confirmed_by=uuid.uuid4(),
        confirmed_at=datetime.now(UTC),
    )
    fraud_flag = FraudFlag(document_id=document.id, score=0.65, rationale="test", status="open")

    record = build_export_record(document, extraction, fraud_flag)

    assert record["claim_number"] == "C-1001"
    assert record["claimed_amount"] == 1200.50
    assert record["fraud_score"] == 0.65
    assert record["inconsistency_count"] == 1


def test_build_export_record_without_fraud_flag():
    document = Document(
        id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        file_name="t.pdf",
        file_hash="x",
        mime_type="application/pdf",
        document_type="invoice",
        storage_path="t.pdf",
    )
    extraction = DocumentExtraction(
        document_id=document.id, extracted_fields={}, inconsistencies=[]
    )

    record = build_export_record(document, extraction, None)

    assert record["fraud_score"] is None
    assert record["fraud_status"] is None
    assert record["inconsistency_count"] == 0
