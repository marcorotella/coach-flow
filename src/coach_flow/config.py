"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    DEBUG: bool = True

    # Meta WhatsApp
    META_WA_PHONE_NUMBER_ID: str = ""
    META_WA_ACCESS_TOKEN: str = ""
    META_WA_VERIFY_TOKEN: str = ""
    META_WA_APP_SECRET: str = ""

    # Personal Trainer
    PT_NAME: str = "Coach"
    PT_PHONE_NUMBER: str = ""
    CALENDAR_PROVIDER: str = "google"
    DEFAULT_VOICE_MEMO_URL: str = ""

    # Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./coach_flow.db"

    # AI Configuration
    AI_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    AI_MODEL_NAME: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
