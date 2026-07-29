from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────
    APP_NAME: str = "Unilever Cloud Operations Portal"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    SECRET_KEY: str  # Used for session cookie signing

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str  # postgresql+asyncpg://...
    DATABASE_URL_SYNC: str  # postgresql+psycopg2://...  (Alembic)

    # ── JWT ──────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # ── Micetro ──────────────────────────────────────────────────────────
    MICETRO_BASE_URL: str = "https://ssportal-qa.unilever.com/mmws/api/v2"
    MICETRO_USERNAME: str = ""
    MICETRO_PASSWORD: str = ""
    MICETRO_VERIFY_SSL: bool = True
    MICETRO_SESSION_TIMEOUT: int = 3600  # seconds

    # ── Rate limiting ────────────────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 2
    RATE_LIMIT_PERIOD_HOURS: int = 24

    # ── Bootstrap admin ──────────────────────────────────────────────────
    INITIAL_ADMIN_EMAIL: str = "admin@unilever.com"
    INITIAL_ADMIN_PASSWORD: str = "ChangeMe123!"
    INITIAL_ADMIN_FULL_NAME: str = "Portal Administrator"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
