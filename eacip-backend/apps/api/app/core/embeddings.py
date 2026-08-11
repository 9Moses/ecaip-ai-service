import litellm

from app.core.config import get_settings

settings = get_settings()


class EmbeddingError(Exception):
    """Raised when the embedding provider call fails."""


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not settings.gemini_api_key:
        raise EmbeddingError(
            """GEMINI_API_KEY is not set. Embeddings use Gemini's
             embedding endpoint via LiteLLM """
            """and require a Gemini key even if your chat-completion """
            """fallback chain relies on other providers — Groq/Cerebras """
            """don't currently offer an embeddings API """
            """through LiteLLM the way Gemini does."""
        )

    try:
        response = litellm.embedding(
            model=settings.embedding_model_name,
            input=texts,
            dimensions=settings.embedding_dimensions,
        )
    except Exception as exc:
        raise EmbeddingError(str(exc)) from exc

    return [item["embedding"] for item in response.data]


def embed_query(query: str) -> list[float]:
    return embed_texts([query])[0]
