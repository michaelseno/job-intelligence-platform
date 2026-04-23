from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./job_intelligence_platform.db"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    scheduler_enabled: bool = False
    digest_hour_local: int = 8
    saved_reminder_days: int = 3
    applied_reminder_days: int = 7
    adapter_timeout_seconds: int = 20
    empty_warning_threshold: int = 1


@lru_cache
def get_settings() -> Settings:
    return Settings()
