from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RegIQ"
    app_version: str = "0.1.0"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = False

    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "RegIQ"

    aiml_api_key: str
    qdrant_api_key: str
    qdrant_cluster_endpoint: str

    thenvoi_ws_url: str | None = None
    thenvoi_rest_url: str | None = None
    band_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()