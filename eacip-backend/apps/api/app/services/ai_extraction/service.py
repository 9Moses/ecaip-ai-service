import logging
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.llm_gateway import LLMGatewayError, complete
from app.schemas.extraction_fields import get_extraction_schema
from app.services.ai_extraction.json_utils import extract_json_from_llm_response
from app.services.ai_extraction.prompts import build_extraction_prompt, build_retry_prompt

logger = logging.getLogger("ai_extraction")


@dataclass
class StructuredExtractionResult:
    status: str  # "completed" | "needs_review" | "failed"
    extracted_fields: dict[str, Any]
    raw_llm_output: str
    error_message: str | None = None


async def extract_structured_fields(
    document_type: str, raw_text: str
) -> StructuredExtractionResult:
    schema_cls = get_extraction_schema(document_type)
    system_prompt, user_prompt = build_extraction_prompt(document_type, raw_text)

    try:
        response_text = await complete(system_prompt, user_prompt)
    except LLMGatewayError as exc:
        logger.error("LLM Gateway failed during extraction: %s", exc)
        return StructuredExtractionResult(
            status="failed", extracted_fields={}, raw_llm_output="", error_message=str(exc)
        )

    validated = _try_parse_and_validate(response_text, schema_cls)
    if validated is not None:
        return StructuredExtractionResult(
            status="completed", extracted_fields=validated, raw_llm_output=response_text
        )

    # One retry, feeding the specific error back to the model
    logger.warning("First extraction attempt failed validation — retrying once")
    try:
        first_error = _last_validation_error(response_text, schema_cls)
        retry_prompt = build_retry_prompt(response_text, first_error)
        retry_response_text = await complete(system_prompt, retry_prompt)
    except LLMGatewayError as exc:
        return StructuredExtractionResult(
            status="failed",
            extracted_fields={},
            raw_llm_output=response_text,
            error_message=str(exc),
        )

    retried_validated = _try_parse_and_validate(retry_response_text, schema_cls)
    if retried_validated is not None:
        return StructuredExtractionResult(
            status="completed",
            extracted_fields=retried_validated,
            raw_llm_output=retry_response_text,
        )

    # Gave the model one honest second chance — beyond that,
    # this needs a human, not more retries
    return StructuredExtractionResult(
        status="needs_review",
        extracted_fields={},
        raw_llm_output=retry_response_text,
        error_message="LLM output did not match the expected schema " "after one retry.",
    )


def _try_parse_and_validate(
    response_text: str,
    schema_cls: type[BaseModel],
) -> dict[str, Any] | None:
    try:
        raw_json = extract_json_from_llm_response(response_text)
        validated = schema_cls.model_validate(raw_json)
        return validated.model_dump(mode="json")
    except (ValueError, ValidationError):
        return None


def _last_validation_error(response_text: str, schema_cls: type[BaseModel]) -> str:
    try:
        raw_json = extract_json_from_llm_response(response_text)
        schema_cls.model_validate(raw_json)
        return "Unknown validation error"
    except ValueError as exc:
        return f"JSON parse error: {exc}"
    except ValidationError as exc:
        return str(exc)
