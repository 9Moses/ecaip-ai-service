import uuid
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.bi.base import BIQueryResult
from app.services.bi.factory import get_power_bi_bridge, get_tableau_bridge
from app.services.rag.retrieval import RetrievedChunk, retrieve_relevant_chunks
from app.services.rag.router import QueryCategory, RoutingDecision, classify_query


@dataclass
class AssembledContext:
    category: QueryCategory
    chunks: list[RetrievedChunk] = field(default_factory=list)
    bi_results: list[BIQueryResult] = field(default_factory=list)
    notice: str | None = None
    """A note to surface to the user, e.g. when BI routing isn't available yet."""


async def assemble_context(
    question: str, owner_id: uuid.UUID, db: AsyncSession
) -> AssembledContext:
    routing: RoutingDecision = await classify_query(question)

    if routing.category == QueryCategory.BI:
        bi_results = await _query_all_bi_sources(question, db)
        return AssembledContext(category=QueryCategory.BI, bi_results=bi_results)

    if routing.category == QueryCategory.HYBRID:
        chunks = retrieve_relevant_chunks(question, owner_id)
        bi_results = await _query_all_bi_sources(question, db)
        return AssembledContext(
            category=QueryCategory.HYBRID,
            chunks=chunks,
            bi_results=bi_results,
        )

    # DOCUMENT
    chunks = retrieve_relevant_chunks(question, owner_id)
    return AssembledContext(category=QueryCategory.DOCUMENT, chunks=chunks)


async def _query_all_bi_sources(question: str, db: AsyncSession) -> list[BIQueryResult]:
    power_bi_bridge = await get_power_bi_bridge(db)
    tableau_bridge = await get_tableau_bridge(db)

    results: list[BIQueryResult] = []
    for bridge in (power_bi_bridge, tableau_bridge):
        try:
            results.append(await bridge.query(question))
        except Exception:
            # A single BI source failing shouldn't
            # take down the whole answer —
            # the other source (or the mock fallback)
            # can still provide something useful.
            continue

    return results
