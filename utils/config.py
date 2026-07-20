"""Centralized configuration loaded from environment / .env file."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings. All values overridable via .env or env vars."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "sqlite:///./database/swingtrader.db"

    # News / sentiment
    NEWSAPI_KEY: str = ""
    FINNHUB_KEY: str = ""
    ALPHAVANTAGE_KEY: str = ""

    # Alerts
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    ALERT_EMAIL_TO: str = ""

    # Scan behaviour
    SCAN_UNIVERSE: str = "ALL_NSE"
    MAX_WORKERS: int = 10
    MIN_PRICE: float = 5.0
    MIN_AVG_VOLUME: int = 50_000

    # App
    LOG_LEVEL: str = "INFO"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    ENV: str = "development"

    # Scoring weights (must sum to 1.0)
    WEIGHT_TECHNICAL: float = 0.40
    WEIGHT_MOMENTUM: float = 0.25
    WEIGHT_VOLUME: float = 0.15
    WEIGHT_NEWS: float = 0.10
    WEIGHT_FUNDAMENTAL: float = 0.10


settings = Settings()
