from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # PostgreSQL connection (used when DATABASE_URL is not set)
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5433
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "12345"
    POSTGRES_DB: str = "Testing"

    # Override everything with a full DSN (used by tests via os.environ)
    DATABASE_URL: str = ""

    # Redis connection (defaulting to localhost for dev, redis inside docker)
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    SECRET_KEY: str = "dev-secret-key-change-in-production-use-32-plus-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Groq AI
    GROQ_API_KEY: str = ""

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/auth/google/callback"

    # Email / SMTP (for daily reports)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""          # Gmail app password (not your login password)
    SMTP_FROM: str = "admin@mychatbot.codes"
    REPORT_EMAIL_TO: str = ""        # where to send the daily report

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
