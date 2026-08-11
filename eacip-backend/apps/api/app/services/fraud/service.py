import uuid
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_extraction.inconsistency_rules import (
    check_duplicate_claim_number,
    run_rule_based_checks,
)
from app.services.ai_extraction.service import find_llm_inconsistencies
from app.services.fraud.rationale import generate_fraud_rationale
from app.services.fraud.scoring import compute_fraud_score, should_flag


@dataclass
class FraudAssessment:
    score: float
    should_flag: bool
    rationale: str
    evidence: list[dict[str, str]] = field(default_factory=list)


async def assess_fraud_risk(
    db: AsyncSession,
    document_id: uuid.UUID,
    owner_id: uuid.UUID,
    document_type: str,
    extracted_fields: dict[str, object],
    raw_text: str,
) -> FraudAssessment:
    rule_findings = run_rule_based_checks(document_type, extracted_fields)

    duplicate_findings = await check_duplicate_claim_number(
        db,
        owner_id,
        document_id,
        str(claim_number) if (claim_number := extracted_fields.get("claim_number")) else None,
    )

    llm_findings = await find_llm_inconsistencies(extracted_fields, raw_text)

    all_findings = rule_findings + duplicate_findings + llm_findings
    score = compute_fraud_score(all_findings)
    flag = should_flag(score)

    rationale = ""
    if flag:
        rationale = await generate_fraud_rationale(all_findings)

    return FraudAssessment(
        score=score, should_flag=flag, rationale=rationale, evidence=all_findings
    )
