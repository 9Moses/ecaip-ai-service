from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from app.core.config import get_settings

settings = get_settings()


@lru_cache
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url)


def ensure_collection_exists() -> None:
    client = get_qdrant_client()
    existing = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection in existing:
        return

    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=qdrant_models.VectorParams(
            size=settings.embedding_dimensions,
            distance=qdrant_models.Distance.COSINE,
        ),
    )
