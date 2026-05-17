import os
from functools import lru_cache

from pydantic import BaseModel, Field


class Settings(BaseModel):
    app_name: str = Field(default="Local LLM Interactive Novel World Engine")
    app_env: str = Field(default="local")
    database_url: str = Field(default="sqlite:///./world_engine.db")
    llm_provider: str = Field(default="mock")
    llm_model: str = Field(default="gpt-4.1-mini")
    llm_api_key: str | None = Field(default=None, repr=False)
    enable_debug_api: bool = True
    enable_authoring_api: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Local LLM Interactive Novel World Engine"),
        app_env=os.getenv("APP_ENV", "local"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./world_engine.db"),
        llm_provider=os.getenv("LLM_PROVIDER", "mock"),
        llm_model=os.getenv("LLM_MODEL", "gpt-4.1-mini"),
        llm_api_key=os.getenv("LLM_API_KEY") or None,
        enable_debug_api=_read_bool_env("ENABLE_DEBUG_API", default=True),
        enable_authoring_api=_read_bool_env("ENABLE_AUTHORING_API", default=False),
    )


def _read_bool_env(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}
