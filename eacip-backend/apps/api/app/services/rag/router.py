from dataclasses import dataclass
from enum import StrEnum

from app.core.llm_gateway import LLMGatewayError, complete

ROUTER_PROMPT_VERSION = "v1"

_ROUTER_SYSTEM_PROMPT = """You are a query router for an insurance claims AI assistant.
Classify the user's question into exactly one category:

- "document": the question is about specific uploaded documents
(claims, policies, medical
  reports, invoices) — things like extracted fields, document content, or details from a
  specific claim.
- "bi": the question is about aggregate business metrics, trends, or dashboards
(e.g., "what's our average turnaround time", "how many claims were filed last month").
- "hybrid": the question genuinely needs both document-level detail and aggregate
 business data.

Respond with ONLY one word: document, bi, or hybrid. No explanation.
Prompt version: {prompt_version}
"""


class QueryCategory(StrEnum):
    DOCUMENT = "document"
    BI = "bi"
    HYBRID = "hybrid"


@dataclass
class RoutingDecision:
    category: QueryCategory
    reasoning_note: str | None = None


async def classify_query(question: str) -> RoutingDecision:
    system_prompt = _ROUTER_SYSTEM_PROMPT.format(prompt_version=ROUTER_PROMPT_VERSION)
    try:
        response = await complete(system_prompt, question)
    except LLMGatewayError:
        # If the router itself can't reach an LLM, default to the document path —
        # it's the only path that actually works today, and it degrades to "no
        # relevant documents found" gracefully rather than hard-failing the chat.
        return RoutingDecision(
            category=QueryCategory.DOCUMENT,
            reasoning_note="Router LLM call failed; defaulted to document search",
        )

    normalized = response.strip().lower()
    if "bi" in normalized and "hybrid" not in normalized:
        return RoutingDecision(category=QueryCategory.BI)
    if "hybrid" in normalized:
        return RoutingDecision(category=QueryCategory.HYBRID)
    return RoutingDecision(category=QueryCategory.DOCUMENT)
