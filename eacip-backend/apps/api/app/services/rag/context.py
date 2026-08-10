import uuid
from dataclasses import dataclass, field

from app.services.rag.retrieval import RetrievedChunk, retrieve_relevant_chunks
from app.services.rag.router import QueryCategory, RoutingDecision, classify_query


@dataclass
class AssembledContext:
    category: QueryCategory
    chunks: list[RetrievedChunk] = field(default_factory=list)
    notice: str | None = None
    """A note to surface to the user, e.g. when BI routing isn't available yet."""


async def assemble_context(question: str, owner_id: uuid.UUID) -> AssembledContext:
    routing: RoutingDecision = await classify_query(question)

    if routing.category == QueryCategory.BI:
        return AssembledContext(
            category=QueryCategory.BI,
            chunks=[],
            notice=(
                "This looks like a business-metrics question. Power BI/Tableau integration "
                "isn't connected yet (coming in a later build step) — try asking about a "
                "specific uploaded document instead for now."
            ),
        )

    # DOCUMENT or HYBRID: run document retrieval either way — for HYBRID, this is the
    # document half; the BI half is a documented no-op until Step 7 exists.
    chunks = retrieve_relevant_chunks(question, owner_id)

    notice = None
    if routing.category == QueryCategory.HYBRID:
        notice = (
            "This question would benefit from business-metrics data too, which isn't "
            "connected yet — the answer below is based only on your uploaded documents."
        )

    return AssembledContext(category=routing.category, chunks=chunks, notice=notice)
