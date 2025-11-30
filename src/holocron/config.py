"""Configuration management for Holocron.

This module provides centralized configuration using pydantic-settings,
supporting environment variables and .env files.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Settings can be configured via:
    1. Environment variables (prefixed with HOLOCRON_)
    2. .env file in the project root
    3. Default values

    Example:
        ```bash
        export HOLOCRON_MODEL=openai/gpt-4
        export GEMINI_API_KEY=your-key-here
        ```
    """

    model_config = SettingsConfigDict(
        env_prefix="HOLOCRON_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Settings
    default_model: str = Field(
        default="gemini/gemini-2.0-flash",
        description="Default LLM model to use (litellm format)",
    )
    temperature: float = Field(
        default=0.3,
        description="LLM temperature for transformations",
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for LLM calls",
    )

    # Chunking Settings
    chunk_size: int = Field(
        default=3000,
        description="Maximum tokens per chunk",
    )
    chunk_overlap: int = Field(
        default=100,
        description="Token overlap between chunks",
    )

    # Mastery Settings
    default_mastery_model: str = Field(
        default="hybrid",
        description="Default mastery tracking model",
    )
    mastery_decay_rate: float = Field(
        default=0.05,
        description="Daily mastery decay rate",
    )
    mastery_threshold: float = Field(
        default=80.0,
        description="Mastery percentage to consider 'mastered'",
    )

    # Database Settings
    database_path: Optional[str] = Field(
        default=None,
        description="Path to SQLite database (default: ~/.holocron/holocron.db)",
    )

    # Web GUI Settings
    web_host: str = Field(
        default="127.0.0.1",
        description="Host for web GUI",
    )
    web_port: int = Field(
        default=8080,
        description="Port for web GUI",
    )
    web_reload: bool = Field(
        default=False,
        description="Enable hot reload for development",
    )

    # API Keys (read from environment, no prefix)
    gemini_api_key: Optional[str] = Field(
        default=None,
        validation_alias="GEMINI_API_KEY",
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        validation_alias="OPENAI_API_KEY",
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        validation_alias="ANTHROPIC_API_KEY",
    )
    ollama_api_base: Optional[str] = Field(
        default="http://localhost:11434",
        validation_alias="OLLAMA_API_BASE",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings object with all configuration values
    """
    return Settings()


def get_database_path() -> str:
    """Get the database path, creating directory if needed.

    Returns:
        Path to the SQLite database file
    """
    import os
    from pathlib import Path

    settings = get_settings()

    if settings.database_path:
        db_path = Path(settings.database_path)
    else:
        # Default to ~/.holocron/holocron.db
        home = Path.home()
        holocron_dir = home / ".holocron"
        holocron_dir.mkdir(exist_ok=True)
        db_path = holocron_dir / "holocron.db"

    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    return str(db_path)
