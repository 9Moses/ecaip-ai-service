from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".evn", extra="ignore")

    app_name: str = "EACIP API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    # CORS
    cors_origins: list[str] = ["http://localhost:8000"]

    # Will be populated in later steps (DB, Redis, etc.)
    # database_url: str
    # redis_url: str


@lru_cache
def get_settings() -> Settings:

    return Settings()
