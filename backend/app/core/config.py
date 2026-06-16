"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Project
    PROJECT_NAME: str = "ControlMap AI"
    API_V1_PREFIX: str = "/api/v1"
    VERSION: str = "1.0.0"

    # Database
    # Defaults to a zero-config local SQLite file so the backend runs without any
    # external services. Docker Compose overrides this with a PostgreSQL URL.
    DATABASE_URL: str = "sqlite:///./controlmap.db"

    # Security
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Bootstrap admin
    ADMIN_EMAIL: str = "admin@controlmap.ai"
    ADMIN_PASSWORD: str = "Admin123!"
    SEED_ON_STARTUP: bool = True

    # Rate limiting
    RATE_LIMIT: str = "200/minute"

    # AI
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def split_cors(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
