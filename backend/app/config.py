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

    # RAG settings - Chunking strategy (300-500 tokens, 10-15% overlap)
    CHUNK_SIZE: int = 400  # tokens
    CHUNK_OVERLAP_PERCENT: float = 0.125  # 12.5%
    EMBEDDING_MODEL: str = "nomic-embed-text"
    TOP_K_RESULTS: int = 5

    # Document settings
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    SUPPORTED_FORMATS: list = ["pdf", "docx", "pptx", "txt", "jpg", "png", "jpeg"]
    
    # Whisper settings
    WHISPER_MODEL: str = "base"  # tiny, base, small, medium, large
    
    # Database settings
    DATABASE_PATH: str = "data/studyrag.db"
    
    # Storage paths
    DATA_DIR: str = "data"
    VECTORS_DIR: str = "data/vectors"
    HISTORY_DIR: str = "data/history"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
