import logging

from app.core.llm_gateway import LLMGatewayError, complete
from app.services.ai_extraction.prompts import build_fraud_rationale_prompt

logger = logging.getLogger("fraud_rationale")

_FALLBACK_RATIONALE_TEMPLATE = (
    "This claim was flagged for review based on {count} finding(s), including: {summary}. "
    "Automated rationale generation was unavailable; see the evidence list for full details."
)


async def generate_fraud_rationale(findings: list[dict[str, str]]) -> str:
    system_prompt, user_prompt = build_fraud_rationale_prompt(findings)
    try:
        return (await complete(system_prompt, user_prompt)).strip()
    except LLMGatewayError as exc:
        logger.error("Fraud rationale generation failed, using fallback template: %s", exc)
        summary = "; ".join(f["message"] for f in findings[:3])
        return _FALLBACK_RATIONALE_TEMPLATE.format(count=len(findings), summary=summary)
