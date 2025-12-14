"""Data models for the StudyRAG application."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class MessageRequest(BaseModel):
    """Request model for chat messages."""

    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[str] = None
    mode: Optional[str] = Field(default="chat", description="Prompt mode: chat, summary, points, flashcards, teacher, exam")

    class Config:
        example = {
            "message": "What is machine learning?",
            "session_id": "user-123",
            "mode": "chat",
        }


class MessageResponse(BaseModel):
    """Response model for chat messages."""

    response: str
    session_id: str
    timestamp: datetime

    class Config:
        example = {
            "response": "Machine learning is...",
            "session_id": "user-123",
            "timestamp": "2025-12-14T10:30:00",
        }


class DocumentUpload(BaseModel):
    """Request model for document uploads."""

    filename: str
    document_type: str = Field(..., description="pdf, docx, pptx, youtube, etc.")

    class Config:
        example = {
            "filename": "study_material.pdf",
            "document_type": "pdf",
        }


class DocumentResponse(BaseModel):
    """Response model for document processing."""

    document_id: str
    filename: str
    status: str = Field(..., description="processing, completed, failed")
    chunks_count: Optional[int] = None
    message: str

    class Config:
        example = {
            "document_id": "doc-123",
            "filename": "study_material.pdf",
            "status": "processing",
            "chunks_count": None,
            "message": "Document uploaded and processing started",
        }


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    model: str
    message: str

    class Config:
        example = {
            "status": "healthy",
            "model": "llama3:latest",
            "message": "StudyRAG is running and ready",
        }


class SessionCreate(BaseModel):
    """Request model for creating a session."""

    name: str = Field(..., min_length=1, max_length=200, description="Subject/workspace name")
    category_map: str = Field(default="notes", description="Category: notes or qpapers")
    vector_index_path: Optional[str] = None
    chat_history_path: Optional[str] = None

    class Config:
        example = {
            "name": "Machine Learning Notes",
            "category_map": "notes",
            "vector_index_path": None,
            "chat_history_path": None,
        }


class SessionResponse(BaseModel):
    """Response model for session data."""

    session_id: str
    name: str
    created_at: str
    last_used: Optional[str] = None
    category_map: str
    vector_index_path: Optional[str] = None
    chat_history_path: Optional[str] = None

    class Config:
        example = {
            "session_id": "sess-abc123",
            "name": "Machine Learning Notes",
            "created_at": "2025-12-14 10:30:00",
            "last_used": "2025-12-14 15:45:00",
            "category_map": "notes",
            "vector_index_path": "data/vectors/sess-abc123",
            "chat_history_path": "data/history/sess-abc123.json",
        }


class SessionUpdate(BaseModel):
    """Request model for updating a session."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category_map: Optional[str] = None
    vector_index_path: Optional[str] = None
    chat_history_path: Optional[str] = None

    class Config:
        example = {
            "name": "Updated ML Notes",
            "category_map": "qpapers",
        }


class UploadRecord(BaseModel):
    """Response model for uploaded files per session."""

    upload_id: str
    session_id: str
    filename: str
    category: str
    chunks_count: Optional[int] = 0
    created_at: Optional[str] = None

    class Config:
        example = {
            "upload_id": "doc-123",
            "session_id": "sess-abc123",
            "filename": "notes.pdf",
            "category": "notes",
            "chunks_count": 24,
            "created_at": "2025-12-14 10:45:00",
        }


class QuickActionRequest(BaseModel):
    """Request model for quick action endpoints."""

    session_id: str = Field(..., description="Session identifier")
    topic: Optional[str] = Field(None, description="Specific topic to focus on (optional, uses all context if not provided)")

    class Config:
        example = {
            "session_id": "sess-abc123",
            "topic": "machine learning algorithms",
        }
