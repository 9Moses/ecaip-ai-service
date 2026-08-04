from datetime import date

from pydantic import BaseModel, Field


class ClaimFormFields(BaseModel):
    claim_number: str | None = Field(None, description="The claim reference number")
    policy_number: str | None = None
    policyholder_name: str | None = None
    incident_date: date | None = None
    filing_date: date | None = None
    claimed_amount: float | None = Field(
        None, description="Total amount claimed, in the document's currency"
    )
    incident_location: str | None = None


class PolicyDocumentFields(BaseModel):
    policy_number: str | None = None
    policyholder_name: str | None = None
    coverage_type: str | None = None
    coverage_start_date: date | None = None
    coverage_end_date: date | None = None
    premium_amount: float | None = None
    coverage_limit: float | None = None


class MedicalReportFields(BaseModel):
    patient_name: str | None = None
    report_date: date | None = None
    provider_name: str | None = None
    diagnosis_summary: str | None = None
    treatment_summary: str | None = None
    related_claim_number: str | None = None


class InvoiceFields(BaseModel):
    invoice_number: str | None = None
    vendor_name: str | None = None
    invoice_date: date | None = None
    total_amount: float | None = None
    line_items_summary: str | None = Field(
        None,
        description="""
            Brief plain-text summary of billed items/services —
            full line-item parsing is a future enhancement
        """,
    )
    related_claim_number: str | None = None


class OtherDocumentFields(BaseModel):
    document_summary: str | None = None
    notable_entities: list[str] = Field(
        default_factory=list,
        description="""
            Names, ID numbers, or other notable identifiers found
        """,
    )


EXTRACTION_SCHEMA_REGISTRY: dict[str, type[BaseModel]] = {
    "claim_form": ClaimFormFields,
    "policy": PolicyDocumentFields,
    "medical_report": MedicalReportFields,
    "invoice": InvoiceFields,
    "other": OtherDocumentFields,
}


def get_extraction_schema(document_type: str) -> type[BaseModel]:
    return EXTRACTION_SCHEMA_REGISTRY.get(document_type, OtherDocumentFields)
