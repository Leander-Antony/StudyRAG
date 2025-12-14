"""Configuration settings for StudyRAG application."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings."""

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # Model settings
    OLLAMA_MODEL: str = "llama3:latest"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    TEMPERATURE: float = 0.7

    # RAG settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    EMBEDDING_MODEL: str = "nomic-embed-text"

    # Document settings
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    SUPPORTED_FORMATS: list = ["pdf", "docx", "pptx", "txt", "youtube"]

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
