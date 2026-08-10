import uuid

from qdrant_client.http import models as qdrant_models

from app.core.embeddings import embed_texts
from app.core.vector_store import ensure_collection_exists, get_qdrant_client
from app.core.config import get_settings
from app.services.rag.chunker import chunk_text

settings = get_settings()


def index_document(
    document_id: uuid.UUID,
    owner_id: uuid.UUID,
    document_type: str,
    raw_text: str,
) -> int:
    """
    Chunks, embeds, and stores a document's text in Qdrant.
    Returns the number of chunks indexed.
    """
    ensure_collection_exists()

    chunks = chunk_text(raw_text)
    if not chunks:
        return 0

    vectors = embed_texts([c.text for c in chunks])

    points = [
        qdrant_models.PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "document_id": str(document_id),
                "owner_id": str(owner_id),
                "document_type": document_type,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
            },
        )
        for chunk, vector in zip(chunks, vectors)
    ]

    client = get_qdrant_client()
    client.upsert(collection_name=settings.qdrant_collection, points=points)

    return len(points)


def delete_document_chunks(document_id: uuid.UUID) -> None:
    """Removes all indexed chunks for a document —
    call this if a document is deleted."""
    client = get_qdrant_client()
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=qdrant_models.FilterSelector(
            filter=qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="document_id",
                        match=qdrant_models.MatchValue(value=str(document_id)),
                    )
                ]
            )
        ),
    )
