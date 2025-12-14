"""Unified document loader and ingestion interface."""

import os
import re
from typing import Optional
from app.processors.pdf import process_pdf
from app.processors.docx import process_docx
from app.processors.pptx import process_pptx
from app.processors.ocr import process_image_ocr
from app.rag.chunker import chunk_text
from app.rag.embedder import generate_embeddings
from app.rag.retriever import VectorStore
from app.db import db
from app.config import settings


def clean_text(text: str) -> str:
    """
    Clean extracted text.
    
    Args:
        text: Raw text
        
    Returns:
        Cleaned text
    """
    # Remove multiple whitespaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove multiple newlines
    text = re.sub(r'\n+', '\n', text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def detect_file_type(file_or_link: str) -> str:
    """
    Detect the type of file.
    
    Args:
        file_or_link: File path
        
    Returns:
        File type (pdf, docx, pptx, image, txt)
    """
    ext = os.path.splitext(file_or_link)[1].lower()
    
    if ext == ".pdf":
        return "pdf"
    elif ext == ".docx":
        return "docx"
    elif ext == ".pptx":
        return "pptx"
    elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
        return "image"
    elif ext == ".txt":
        return "txt"
    else:
        return "unknown"


def extract_text(file_or_link: str, file_type: str) -> dict:
    """
    Extract text based on file type.
    
    Args:
        file_or_link: File path
        file_type: Type of file
        
    Returns:
        Dictionary with 'text' key
    """
    if file_type == "pdf":
        return {"text": process_pdf(file_or_link)}
    elif file_type == "docx":
        return {"text": process_docx(file_or_link)}
    elif file_type == "pptx":
        return {"text": process_pptx(file_or_link)}
    elif file_type == "image":
        return {"text": process_image_ocr(file_or_link)}
    elif file_type == "txt":
        with open(file_or_link, 'r', encoding='utf-8') as f:
            return {"text": f.read()}
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def ingest(file_or_link: str, session_id: str, category: str = "notes") -> dict:
    """
    Unified ingestion interface.
    
    Pipeline:
    1. Extract text from file/link
    2. Clean text
    3. Chunk text
    4. Generate embeddings
    5. Store vectors + metadata
    
    Args:
        file_or_link: File path or URL to ingest
        session_id: Session ID to associate with
        category: Category (notes/qpapers)
        
    Returns:
        Ingestion result dictionary
    """
    # Get session info
    session = db.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # Ensure vector index path exists for this session
    if not session.get("vector_index_path"):
        default_vector_path = f"{settings.VECTORS_DIR}/{session_id}"
        db.update_session(session_id, vector_index_path=default_vector_path)
        session = db.get_session(session_id)
    
    # Detect file type
    file_type = detect_file_type(file_or_link)
    
    # Extract text
    print(f"Extracting text from {file_type}...")
    extract_result = extract_text(file_or_link, file_type)
    raw_text = extract_result["text"]
    source_title = extract_result.get("title", os.path.basename(file_or_link) if os.path.exists(file_or_link) else file_or_link)
    
    # Clean text
    print("Cleaning text...")
    cleaned_text = clean_text(raw_text)
    
    # Chunk text with token-based strategy (uses config defaults)
    print("Chunking text...")
    chunks = chunk_text(cleaned_text)
    
    if not chunks:
        return {
            "status": "error",
            "message": "No text extracted from document",
            "chunks_count": 0
        }
    
    # Generate embeddings
    print(f"Generating embeddings for {len(chunks)} chunks...")
    embeddings = generate_embeddings(chunks)
    
    # Prepare metadata with source, page/timestamp, and category
    metadata = []
    for i, chunk in enumerate(chunks):
        metadata.append({
            "session_id": session_id,
            "category": category,
            "source": source_title,
            "source_full_path": file_or_link,
            "chunk_index": i,
            "page": i + 1,  # Approximate page number
            "timestamp": None,  # Can be populated for video timestamps
            "text": chunk
        })
    
    # Store vectors
    print("Storing vectors...")
    vector_store = VectorStore(session["vector_index_path"])
    vector_store.add(embeddings, metadata)
    
    return {
        "status": "success",
        "message": "Document ingested successfully",
        "chunks_count": len(chunks),
        "file_type": file_type,
        "session_id": session_id,
        "source_title": source_title
    }
