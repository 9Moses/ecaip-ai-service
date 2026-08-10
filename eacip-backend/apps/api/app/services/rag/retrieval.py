import uuid
from dataclasses import dataclass

from qdrant_client.http import models as qdrant_models

from app.core.config import get_settings
from app.core.embeddings import embed_query
from app.core.vector_store import get_qdrant_client

settings = get_settings()

DEFAULT_TOP_K = 5
MIN_RELEVANCE_SCORE = 0.3
# Cosine similarity threshold below which a "match" is probably not actually relevant —
# better to tell the user "I don't have enough information" than force a weak match into
# the answer (matches doc 05 §5.2's fallback-to-clarification principle).


@dataclass
class RetrievedChunk:
    document_id: str
    chunk_index: int
    text: str
    score: float


def retrieve_relevant_chunks(
    query: str,
    owner_id: uuid.UUID,
    top_k: int = DEFAULT_TOP_K,
) -> list[RetrievedChunk]:
    query_vector = embed_query(query)
    client = get_qdrant_client()

    response = client.query_points(
        collection_name=settings.qdrant_collection,
        query=query_vector,
        query_filter=qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(
                    key="owner_id", match=qdrant_models.MatchValue(value=str(owner_id))
                )
            ]
        ),
        limit=top_k,
        score_threshold=MIN_RELEVANCE_SCORE,
        with_payload=True,
    )

    return [
        RetrievedChunk(
            document_id=hit.payload["document_id"],
            chunk_index=hit.payload["chunk_index"],
            text=hit.payload["text"],
            score=hit.score,
        )
        for hit in response.points
    ]
