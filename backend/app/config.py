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


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "Local LLM Interactive Novel World Engine"),
        app_env=os.getenv("APP_ENV", "local"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./world_engine.db"),
        llm_provider=os.getenv("LLM_PROVIDER", "mock"),
        llm_model=os.getenv("LLM_MODEL", "gpt-4.1-mini"),
        llm_api_key=os.getenv("LLM_API_KEY") or None,
    )
