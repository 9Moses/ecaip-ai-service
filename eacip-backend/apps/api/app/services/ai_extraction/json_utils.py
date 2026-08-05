import json
import re
from typing import Any, cast


def extract_json_from_llm_response(raw_response: str) -> dict[str, Any]:
    """
    Defensively parses a JSON object out of an LLM response, tolerating
    markdown code fences or minor surrounding text the model added despite
    instructions not to.
    Raises ValueError if no valid JSON object can be extracted.
    """
    cleaned = raw_response.strip()

    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1)
    else:
        brace_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if brace_match:
            cleaned = brace_match.group(0)

    try:
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise ValueError(f"Expected a JSON object, but got {type(parsed).__name__}")
        # Defensive unwrap: the model sometimes echoes the JSON Schema
        # structure back, wrapping all field values inside a "properties"
        # key (e.g. {"properties": {"patient_name": null, ...}}).
        # When that happens every field validates as null — unwrap it.
        if set(parsed.keys()) == {"properties"} and isinstance(parsed["properties"], dict):
            parsed = parsed["properties"]
        return cast(dict[str, Any], parsed)
    except json.JSONDecodeError as exc:
        context = cleaned[:500]
        error_msg = (
            f"Failed to parse JSON from LLM response. "
            f"Raw response preview: {context!r}... "
            "Please check the response for formatting errors."
        )
        raise ValueError(error_msg) from exc
