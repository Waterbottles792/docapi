"""Env-driven settings. No secret has a default; everything works at $0 with the stub."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    env: str = Field("dev", alias="DOCAPI_ENV")
    # stub = free, no network. anthropic / ollama wired in a later phase.
    llm_provider: str = Field("stub", alias="LLM_PROVIDER")
    llm_model: str = Field("", alias="LLM_MODEL")
    anthropic_api_key: str = Field("", alias="ANTHROPIC_API_KEY")
    ollama_host: str = Field("http://localhost:11434", alias="OLLAMA_HOST")

    max_file_mb: int = Field(20, alias="MAX_FILE_MB")
    max_pages: int = Field(30, alias="MAX_PAGES")
    request_timeout_seconds: int = Field(60, alias="REQUEST_TIMEOUT_SECONDS")


@lru_cache
def get_settings() -> Settings:
    return Settings()
