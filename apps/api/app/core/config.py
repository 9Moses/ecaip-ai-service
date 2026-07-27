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


@lru_cache
def get_settings() -> Settings:

    return Settings()
