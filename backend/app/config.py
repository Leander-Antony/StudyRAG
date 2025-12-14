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

    # RAG settings - Chunking strategy and retrieval behavior
    CHUNK_SIZE: int = 1024  # tokens
    CHUNK_OVERLAP_PERCENT: float = 0.125  # 12.5%
    EMBEDDING_MODEL: str = "nomic-embed-text"
    
    # Retrieval controls
    # When ALL_RESULTS is True, the retriever should return all available chunks for the session.
    # Otherwise, it will cap by TOP_K_RESULTS.
    ALL_RESULTS: bool = True
    TOP_K_RESULTS: int = 1000  # High cap to approximate full coverage if ALL_RESULTS is ignored

    # Document settings
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    SUPPORTED_FORMATS: list = ["pdf", "docx", "pptx", "txt", "jpg", "png", "jpeg"]
    
    # Whisper settings
    WHISPER_MODEL: str = "base"  # tiny, base, small, medium, large
    WHISPER_FP16: bool = False  # use FP32 by default (fp16 disabled)
    WHISPER_DEVICE: str = "cuda"  # Device: cuda (GPU), cpu, mps (Apple Silicon)
    
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
