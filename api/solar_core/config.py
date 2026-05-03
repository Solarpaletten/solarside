"""Application configuration via pydantic-settings."""
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Solar Core settings, loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SOLAR_",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    env: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # --- Security ---
    secret_key: str = "change-me"
    api_keys: str = "dev-key-1"  # comma-separated

    @property
    def api_keys_list(self) -> list[str]:
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]

    # --- Database ---
    database_url: str = "sqlite+aiosqlite:///./solar_core.db"

    @property
    def is_postgres(self) -> bool:
        return self.database_url.startswith("postgresql")

    # --- AI ---
    ai_default_provider: Literal["anthropic", "openai", "deepseek"] = "anthropic"
    ai_reasoning_model: str = "claude-sonnet-4-6"
    ai_extraction_model: str = "claude-haiku-4-5-20251001"
    ai_fallback_provider: Literal["anthropic", "openai", "deepseek"] = "openai"

    # --- Connectors ---
    erp_base_url: str = "http://localhost:3000"
    erp_api_key: str = ""

    # --- Embeddings ---
    embeddings_model: str = "text-embedding-3-small"
    embeddings_dimension: int = 1536


class AIKeysSettings(BaseSettings):
    """Separate settings for AI provider keys (no SOLAR_ prefix)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")


class TelegramSettings(BaseSettings):
    """Telegram Bot API settings (no SOLAR_ prefix)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    default_chat_id: str = Field(default="", alias="TELEGRAM_DEFAULT_CHAT_ID")


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


@lru_cache
def get_ai_keys() -> AIKeysSettings:
    """Cached AI keys instance."""
    return AIKeysSettings()


@lru_cache
def get_telegram_settings() -> TelegramSettings:
    """Cached Telegram settings instance."""
    return TelegramSettings()
