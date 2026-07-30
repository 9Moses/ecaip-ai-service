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


@lru_cache
def get_settings() -> Settings:

    return Settings()  # type: ignore[call-arg]  # loaded from env, not args
