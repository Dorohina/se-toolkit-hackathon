"""
Configuration module for the Event Finder Bot.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Telegram Bot
    BOT_TOKEN: str
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/events_db"
    
    # Admin
    ADMIN_CHAT_ID: Optional[str] = None
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    
    # LLM (optional)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Timezone
    TIMEZONE: str = "Europe/Moscow"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
