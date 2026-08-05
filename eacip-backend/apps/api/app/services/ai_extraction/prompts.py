import json

from app.schemas.extraction_fields import get_extraction_schema

EXTRACTION_PROMPT_VERSION = "v1"

_SYSTEM_PROMPT_TEMPLATE = """You are a document intelligence system
for an insurance claims platform.
You will be given the raw text extracted from a document
(via OCR or direct PDF parsing — it may
contain minor OCR errors, especially in numbers and names).

Your task: extract structured information into JSON matching
EXACTLY this schema:

{schema_json}

Rules:
- Respond with ONLY valid JSON. No markdown code fences,
 no explanation, no preamble.
- If a field's value isn't present in the text, use null —
do not guess or invent values.
- For dates, use ISO format (YYYY-MM-DD). If a date is ambiguous
or partial, use null.
- For monetary amounts, extract only the numeric value
(no currency symbols).
- Prompt version: {prompt_version}
"""


def build_extraction_prompt(
    document_type: str,
    raw_text: str,
) -> tuple[str, str]:
    schema_cls = get_extraction_schema(document_type)
    # Build a simple {field_name: description_or_type} dict so the model
    # sees plain field names — NOT the full JSON Schema object, which has
    # a top-level "properties" key that causes the model to echo it back
    # as a wrapper (e.g. {"properties": {"patient_name": ...}}).
    raw_schema = schema_cls.model_json_schema()
    fields_only = {
        field: (meta.get("description") or meta.get("type", "string"))
        for field, meta in raw_schema.get("properties", {}).items()
    }
    schema_json = json.dumps(fields_only, indent=2)

    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        schema_json=schema_json,
        prompt_version=EXTRACTION_PROMPT_VERSION,
    )
    user_prompt = f"Document text:\n\n{raw_text}"
    # Truncated to ~12k chars to stay well within free-tier
    # context limits across providers;
    # revisit with chunking (doc 05 §5.2's chunking approach)
    # if longer documents become common.

    return system_prompt, user_prompt


def build_retry_prompt(
    original_response: str,
    validation_error: str,
) -> str:
    return (
        """Your previous response could not be
        parsed as valid JSON matching the required schema.\n\n"""
        f"Your previous response was:\n{original_response}\n\n"
        f"The validation error was:\n{validation_error}\n\n"
        """Respond again with ONLY corrected valid JSON
        matching the schema. No markdown, no explanation."""
    )
