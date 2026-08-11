import json
from typing import Any

from app.schemas.extraction_fields import get_extraction_schema

EXTRACTION_PROMPT_VERSION = "v1"
SUMMARIZATION_PROMPT_VERSION = "v1"
INCONSISTENCY_PROMPT_VERSION = "v1"
FRAUD_RATIONALE_PROMPT_VERSION = "v1"

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

_SUMMARY_SYSTEM_PROMPT = """You are a document summarization assistant for
an insurance claims platform.
Summarize the following document in 2-4 concise sentences,
written in plain English for a claims
manager who has not read the full document. Focus on: what
type of document this is, the key facts
(amounts, dates, parties involved), and anything that seems
operationally important (missing
information, unusual amounts, urgent language). Do not speculate
beyond what's in the text.
Prompt version: {prompt_version}
"""

_INCONSISTENCY_SYSTEM_PROMPT = """You are a document consistency reviewer
for an insurance claims platform.
You will be given extracted structured fields and the original
document text. Identify any semantic
inconsistencies, contradictions, or suspicious patterns that
would not be caught by simple field
validation — for example: a narrative that contradicts a stated
amount or date, mismatched names,
or claims that seem internally contradictory.

Respond with ONLY a JSON array (no markdown, no explanation)
of objects, each with:
- "field": the relevant field name, or "general" if not field-specific
- "message": a plain-English description of the issue
- "severity": one of "low", "medium", "high"

If you find no issues, respond with an empty array: []
Prompt version: {prompt_version}
"""

_FRAUD_RATIONALE_SYSTEM_PROMPT = """You are writing a fraud-review summary
for a human Fraud Analyst at an insurance company. You will be given a
list of specific findings
about a claim. Write a concise, neutral, professional paragraph
(3-5 sentences) summarizing
what was found and why it warrants human review. Do NOT state that
raud has occurred — only
that these specific findings warrant investigation. Do not add
findings beyond what's listed.
Prompt version: {prompt_version}
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


def build_summary_prompt(raw_text: str) -> tuple[str, str]:
    system_prompt = _SUMMARY_SYSTEM_PROMPT.format(prompt_version=SUMMARIZATION_PROMPT_VERSION)
    user_prompt = f"Document text:\n\n{raw_text[:12000]}"
    return system_prompt, user_prompt


def build_inconsistency_prompt(extracted_fields: dict[str, Any], raw_text: str) -> tuple[str, str]:
    system_prompt = _INCONSISTENCY_SYSTEM_PROMPT.format(prompt_version=INCONSISTENCY_PROMPT_VERSION)
    user_prompt = (
        f"Extracted fields:\n{extracted_fields}\n\n" f"Original document text:\n{raw_text[:8000]}"
    )
    return system_prompt, user_prompt


def build_fraud_rationale_prompt(findings: list[dict[str, str]]) -> tuple[str, str]:
    system_prompt = _FRAUD_RATIONALE_SYSTEM_PROMPT.format(
        prompt_version=FRAUD_RATIONALE_PROMPT_VERSION
    )
    findings_text = "\n".join(f"- [{f['severity']}] {f['field']}: {f['message']}" for f in findings)
    user_prompt = f"Findings:\n{findings_text}"
    return system_prompt, user_prompt
