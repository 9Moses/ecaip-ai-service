from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "EACIP API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    database_url: str
    redis_url: str
    rabbitmq_url: str
    qdrant_url: str

    jwt_secret_key: str = "CHANGE_ME_TO_A_STRONG_SECRET"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = "http://localhost:8000/api/v1/auth/oauth/google/callback"
    frontend_oauth_success_redirect: str = "http://localhost:3000/auth/callback"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "eacip"
    minio_secret_key: str = "eacip_dev_password"
    minio_bucket: str = "eacip-documents"
    minio_use_ssl: bool = False

    document_extraction_queue: str = "document.extraction"
    ai_extraction_queue: str = "document.ai_extraction"

    gemini_api_key: str = ""
    groq_api_key: str = ""
    cerebras_api_key: str = ""

    # Ordered by preference — the gateway tries these in order, falling back on failure/rate limit
    llm_model_fallback_chain: list[str] = [
        "groq/llama-3.3-70b-versatile",
        "cerebras/llama3.1-70b",
        "gemini/gemini-2.5-flash",
    ]
    llm_request_timeout_seconds: int = 30

    embedding_model_name: str = "all-MiniLM-L6-v2"
    embedding_dimensions: int = 384

    qdrant_collection: str = "document_chunks"
    chunk_target_tokens: int = 650  # mid-point of the 500-800 token target range
    chunk_overlap_tokens: int = 80

    indexing_queue: str = "document.indexing"


@lru_cache
def get_settings() -> Settings:

    return Settings()  # type: ignore[call-arg]  # loaded from env, not args
