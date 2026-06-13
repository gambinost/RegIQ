from dotenv import load_dotenv

load_dotenv()  # noqa: E402 — must run before any langsmith/env-dependent imports

from functools import lru_cache  # noqa: E402
from typing import Optional  # noqa: E402

from pydantic_settings import BaseSettings, SettingsConfigDict  # noqa: E402


class Settings(BaseSettings):
    APP_NAME: str = "RegIQ"
    APP_VERSION: str = "0.1.0"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = True

    LANGSMITH_TRACING: Optional[bool] = None
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "RegIQ"

    AIML_API_KEY: str
    OPENAI_BASE_URL: str = "https://api.aimlapi.com/v1"

    MODEL_FAST: str = "gemini-2.5-flash"
    MODEL_BALANCED: str = "anthropic/claude-sonnet-4.6"
    MODEL_EMBEDDINGS: str = "text-embedding-3-small"

    QDRANT_CLUSTER_ENDPOINT: str
    QDRANT_API_KEY: str
    QDRANT_COLLECTION: str = "regiq_company_kb"

    THENVOI_REST_URL: str = "https://app.band.ai/"
    THENVOI_WS_URL: str = "wss://app.band.ai/api/v1/socket/websocket"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
