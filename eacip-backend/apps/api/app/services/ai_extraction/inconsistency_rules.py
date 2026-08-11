from datetime import date
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_extraction import DocumentExtraction

FindingList = list[dict[str, Any]]


def _finding(field: str, message: str, severity: str = "medium") -> dict[str, Any]:
    return {"source": "rule", "field": field, "message": message, "severity": severity}


def check_claim_form(fields: dict[str, Any]) -> FindingList:
    findings: FindingList = []

    incident_date = _parse_date(fields.get("incident_date"))
    filing_date = _parse_date(fields.get("filing_date"))

    if incident_date and filing_date and incident_date > filing_date:
        findings.append(
            _finding(
                "incident_date",
                """
                Incident date is after the filing date — dates may be
                transposed or misread.
                """,
                severity="high",
            )
        )

    if incident_date and incident_date > date.today():
        findings.append(
            _finding("incident_date", "Incident date is in the future.", severity="high")
        )

    claimed_amount = fields.get("claimed_amount")
    if claimed_amount is not None and claimed_amount < 0:
        findings.append(_finding("claimed_amount", "Claimed amount is negative.", severity="high"))

    if not fields.get("claim_number"):
        findings.append(
            _finding("claim_number", "No claim number was found in the document.", severity="low")
        )

    return findings


def check_invoice(fields: dict[str, Any]) -> FindingList:
    findings: FindingList = []
    total_amount = fields.get("total_amount")
    if total_amount is not None and total_amount < 0:
        findings.append(_finding("total_amount", "Invoice total is negative.", severity="high"))
    if not fields.get("invoice_number"):
        findings.append(_finding("invoice_number", "No invoice number was found.", severity="low"))
    return findings


def check_policy(fields: dict[str, Any]) -> FindingList:
    findings: FindingList = []
    start = _parse_date(fields.get("coverage_start_date"))
    end = _parse_date(fields.get("coverage_end_date"))
    if start and end and start > end:
        findings.append(
            _finding(
                "coverage_start_date",
                "Coverage start date is after the coverage end date.",
                severity="high",
            )
        )
    return findings


RULE_CHECKS = {
    "claim_form": check_claim_form,
    "invoice": check_invoice,
    "policy": check_policy,
}


def run_rule_based_checks(document_type: str, extracted_fields: dict[str, Any]) -> FindingList:
    check_fn = RULE_CHECKS.get(document_type)
    if check_fn is None:
        return []
    return check_fn(extracted_fields)


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value) if hasattr(date, "fromisoformat") else None
    except (ValueError, TypeError):
        return None


async def check_duplicate_claim_number(
    db: AsyncSession,
    owner_id: object,
    current_document_id: object,
    claim_number: str | None,
) -> FindingList:
    if not claim_number:
        return []

    result = await db.execute(
        select(DocumentExtraction.document_id, DocumentExtraction.extracted_fields).where(
            DocumentExtraction.document_id != current_document_id
        )
    )
    duplicates = [
        str(doc_id) for doc_id, fields in result.all() if fields.get("claim_number") == claim_number
    ]

    if not duplicates:
        return []

    return [
        _finding(
            "claim_number",
            f"""
            Claim number '{claim_number}' also appears in
            {len(duplicates)} other document(s):
            {', '.join(duplicates)}
            """,
            severity="high",
        )
    ]
