"""Application configuration."""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/prediction_markets",
    )

    # Polymarket API
    polymarket_api_key: Optional[str] = os.getenv("POLYMARKET_API_KEY")
    polymarket_rate_limit: float = float(os.getenv("POLYMARKET_RATE_LIMIT", "10.0"))

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = False


settings = Settings()

