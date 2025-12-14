"""Main application entry point using FastAPI."""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uuid
import os
import json
from typing import Dict, List
import torch

from app.models import (
    MessageRequest,
    MessageResponse,
    DocumentResponse,
    HealthResponse,
    SessionCreate,
    SessionResponse,
    SessionUpdate,
    QuickActionRequest,
    UploadRecord,
)
from app.rag.chat import ChatBot
from app.config import Settings
from app.db import db
from app.rag.loader import ingest
import tempfile
import shutil

# Global state
chat_sessions: Dict[str, ChatBot] = {}
settings = Settings()

# Check CUDA availability on startup
def check_gpu_availability():
    """Check and log GPU availability."""
    if torch.cuda.is_available():
        print(f"✓ GPU detected: {torch.cuda.get_device_name(0)}")
        print(f"  CUDA Version: {torch.version.cuda}")
        print(f"  Device Count: {torch.cuda.device_count()}")
    else:
        print("⚠ WARNING: CUDA not available. PyTorch cannot access GPU.")
        print("  To enable GPU support:")
        print("    1. Verify NVIDIA GPU is installed and drivers updated")
        print("    2. Install CUDA Toolkit (matching PyTorch version)")
        print("    3. Reinstall PyTorch with CUDA support:")
        print("       pip uninstall torch torchvision torchaudio")
        print("       pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
        print("       (Replace cu118 with your CUDA version: cu118, cu121, etc.)")

check_gpu_availability()


def ensure_session_paths(session: Dict) -> Dict:
    """Ensure vector_index_path and chat_history_path exist for a session."""
    updated = False
    if not session.get('vector_index_path'):
        session['vector_index_path'] = f"{settings.VECTORS_DIR}/{session['session_id']}"
        updated = True
    if not session.get('chat_history_path'):
        session['chat_history_path'] = f"{settings.HISTORY_DIR}/{session['session_id']}.json"
        updated = True
    if updated:
        db.update_session(
            session_id=session['session_id'],
            vector_index_path=session['vector_index_path'],
            chat_history_path=session['chat_history_path'],
        )
        session = db.get_session(session['session_id']) or session
    return session


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print("StudyRAG starting up...")
    print("Initializing database...")
    db.init_db()
    # Ensure migrations run for legacy DBs
    try:
        db._migrate_add_last_used()
    except Exception as e:
        print(f"Migration check error: {e}")
    yield
    print("StudyRAG shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="StudyRAG",
    description="AI-powered study material RAG system with local LLM",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {"message": "Welcome to StudyRAG API"}


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        model=settings.OLLAMA_MODEL,
        message="StudyRAG is running and ready",
    )


@app.post("/chat", response_model=MessageResponse, tags=["Chat"])
async def chat(request: MessageRequest):
    """
    Send a message to the chatbot with RAG support.

    - **message**: User's message (required, 1-5000 characters)
    - **session_id**: Session identifier for conversation tracking (required for RAG)
    - **mode**: Prompt mode - chat, summary, points, flashcards, teacher, exam (default: chat)
    """
    try:
        # Session ID is required for RAG
        if not request.session_id:
            raise HTTPException(status_code=400, detail="session_id is required for RAG chat")
        
        session_id = request.session_id
        mode = request.mode or "chat"
        
        # Validate mode
        valid_modes = ["chat", "summary", "points", "flashcards", "teacher", "exam"]
        if mode not in valid_modes:
            raise HTTPException(status_code=400, detail=f"Invalid mode. Must be one of: {', '.join(valid_modes)}")
        
        # Get session from database
        session = db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        session = ensure_session_paths(session)

        # Create or get chat session with RAG enabled
        if session_id not in chat_sessions:
            chat_sessions[session_id] = ChatBot(
                vector_store_path=session['vector_index_path'],
                history_path=session['chat_history_path']
            )

        bot = chat_sessions[session_id]

        # Get response from chatbot with RAG and specified mode
        response_text = bot.chat(request.message, use_rag=True, mode=mode)
        
        # Update last_used timestamp
        db.update_last_used(session_id)

        return MessageResponse(
            response=response_text,
            session_id=session_id,
            timestamp=__import__("datetime").datetime.now(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.post("/upload", response_model=DocumentResponse, tags=["Documents"])
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    category: str = Form("notes")
):
    """
    Upload and ingest a document for RAG processing.

    Supported formats: PDF, DOCX, PPTX, images (for OCR)
    """
    try:
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")

        # Save uploaded file temporarily
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, file.filename)
        
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Ingest the document
        result = ingest(temp_path, session_id, category)
        
        # Cleanup
        os.remove(temp_path)
        os.rmdir(temp_dir)
        
        doc_id = str(uuid.uuid4())
        
        # Record upload in DB
        try:
            db.add_upload(
                upload_id=doc_id,
                session_id=session_id,
                filename=file.filename,
                category=category,
                chunks_count=result.get("chunks_count", 0),
            )
        except Exception as e:
            print(f"Warning: failed to record upload: {e}")

        # Reload in-memory vector store if session active
        if session_id in chat_sessions:
            bot = chat_sessions[session_id]
            if bot.vector_store:
                try:
                    bot.vector_store.load()
                except Exception as e:
                    print(f"Warning: failed to reload vector store for session {session_id}: {e}")
        
        return DocumentResponse(
            document_id=doc_id,
            filename=file.filename,
            status="completed" if result["status"] == "success" else "failed",
            chunks_count=result.get("chunks_count", 0),
            message=result["message"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")




@app.get("/sessions/{session_id}/history", tags=["Chat"])
async def get_chat_history(session_id: str):
    """Get conversation history for a session."""
    try:
        # Check if session exists in DB
        session = db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # If session is loaded in memory, get from chat bot
        if session_id in chat_sessions:
            bot = chat_sessions[session_id]
            history = bot.get_conversation_history()
        else:
            # Load from disk history file
            history_file = f"{settings.HISTORY_DIR}/{session_id}.json"
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    history = data.get('messages', [])
            else:
                history = []

        return {
            "session_id": session_id,
            "messages": history,
            "total_messages": len(history),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.delete("/sessions/{session_id}", tags=["Chat"])
async def clear_session(session_id: str):
    """
    Clear conversation history for a session (does not delete the session).
    
    This only clears the chat messages, keeping the session and vector data intact.
    """
    try:
        if session_id not in chat_sessions:
            raise HTTPException(status_code=404, detail="Session not found in memory")

        bot = chat_sessions[session_id]
        bot.clear_history()
        del chat_sessions[session_id]

        return {"message": f"Chat history cleared for session {session_id}"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# Session Management Endpoints
@app.post("/api/sessions", response_model=SessionResponse, tags=["Sessions"])
async def create_session(session: SessionCreate):
    """
    Create a new session (subject/workspace).

    - **name**: Session name (required)
    - **category_map**: Category type - 'notes' or 'qpapers' (default: notes)
    - **vector_index_path**: Optional path to vector index
    - **chat_history_path**: Optional path to chat history
    """
    try:
        session_id = f"sess-{uuid.uuid4()}"
        
        # Set default paths if not provided (using config directories)
        vector_path = session.vector_index_path or f"{settings.VECTORS_DIR}/{session_id}.json"
        history_path = session.chat_history_path or f"{settings.HISTORY_DIR}/{session_id}.json"
        
        result = db.create_session(
            session_id=session_id,
            name=session.name,
            category_map=session.category_map,
            vector_index_path=vector_path,
            chat_history_path=history_path,
        )
        
        return SessionResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")


@app.get("/api/sessions", response_model=List[SessionResponse], tags=["Sessions"])
async def get_all_sessions():
    """Get all sessions."""
    try:
        sessions = db.get_all_sessions()
        return [SessionResponse(**session) for session in sessions]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sessions: {str(e)}")


@app.get("/api/sessions/{session_id}", response_model=SessionResponse, tags=["Sessions"])
async def get_session(session_id: str):
    """Get a specific session by ID."""
    try:
        session = db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        # Update last_used when a session is opened/viewed
        updated = db.update_last_used(session_id)
        return SessionResponse(**(updated or session))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching session: {str(e)}")


@app.patch("/api/sessions/{session_id}", response_model=SessionResponse, tags=["Sessions"])
async def update_session(session_id: str, update_data: SessionUpdate):
    """Update a session."""
    try:
        # Check if session exists
        if not db.get_session(session_id):
            raise HTTPException(status_code=404, detail="Session not found")
        
        result = db.update_session(
            session_id=session_id,
            name=update_data.name,
            category_map=update_data.category_map,
            vector_index_path=update_data.vector_index_path,
            chat_history_path=update_data.chat_history_path,
        )
        
        return SessionResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating session: {str(e)}")


@app.delete("/api/sessions/{session_id}", tags=["Sessions"])
async def delete_session(session_id: str):
    """
    Delete a session permanently.
    
    This will remove:
    - Session record from database
    - Vector index files (.index and .meta)
    - Chat history file
    - In-memory chat bot instance
    """
    try:
        # Get session info first
        session = db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Delete session and all associated files
        deleted = db.delete_session(session_id)
        
        # Clear from memory if active
        if session_id in chat_sessions:
            del chat_sessions[session_id]
        
        return {
            "message": f"Session {session_id} and all associated data deleted successfully",
            "deleted_files": {
                "vector_index": session['vector_index_path'],
                "chat_history": session['chat_history_path']
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")


@app.get("/api/sessions/category/{category}", response_model=List[SessionResponse], tags=["Sessions"])
async def get_sessions_by_category(category: str):
    """
    Get all sessions by category.
    
    - **category**: Filter by 'notes' or 'qpapers'
    """
    try:
        if category not in ["notes", "qpapers"]:
            raise HTTPException(status_code=400, detail="Category must be 'notes' or 'qpapers'")
        
        sessions = db.get_sessions_by_category(category)
        return [SessionResponse(**session) for session in sessions]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sessions: {str(e)}")


@app.get("/api/sessions/{session_id}/files", response_model=List[UploadRecord], tags=["Sessions"])
async def get_session_files(session_id: str):
    """List uploaded files for a session."""
    try:
        session = db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        uploads = db.get_uploads_for_session(session_id)
        return [UploadRecord(**u) for u in uploads]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching files: {str(e)}")


# Quick Action Endpoints (1-click intelligence)
@app.post("/explain-simple", response_model=MessageResponse, tags=["Quick Actions"])
async def explain_simple(request: QuickActionRequest):
    """
    Get a simple, beginner-friendly explanation of the content.
    
    Uses teacher mode to provide detailed, pedagogical explanations.
    
    - **session_id**: Session identifier (required)
    - **topic**: Specific topic to explain (optional, uses all context if not provided)
    """
    try:
        session = db.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
        session = ensure_session_paths(session)
        
        # Create or get chat session
        if request.session_id not in chat_sessions:
            chat_sessions[request.session_id] = ChatBot(
                vector_store_path=session['vector_index_path'],
                history_path=session['chat_history_path']
            )
        
        bot = chat_sessions[request.session_id]
        
        # Generate query
        query = request.topic if request.topic else "Explain this topic in simple terms"
        
        # Get response with teacher mode
        response_text = bot.chat(query, use_rag=True, mode="teacher")
        
        return MessageResponse(
            response=response_text,
            session_id=request.session_id,
            timestamp=__import__("datetime").datetime.now(),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/important-points", response_model=MessageResponse, tags=["Quick Actions"])
async def important_points(request: QuickActionRequest):
    """
    Extract the most important points from the content.
    
    Uses points mode to identify key information.
    
    - **session_id**: Session identifier (required)
    - **topic**: Specific topic to extract points from (optional)
    """
    try:
        session = db.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
        session = ensure_session_paths(session)
        
        # Create or get chat session
        if request.session_id not in chat_sessions:
            chat_sessions[request.session_id] = ChatBot(
                vector_store_path=session['vector_index_path'],
                history_path=session['chat_history_path']
            )
        
        bot = chat_sessions[request.session_id]
        
        # Generate query
        query = f"What are the important points about {request.topic}" if request.topic else "What are the most important points"
        
        # Get response with points mode
        response_text = bot.chat(query, use_rag=True, mode="points")
        
        return MessageResponse(
            response=response_text,
            session_id=request.session_id,
            timestamp=__import__("datetime").datetime.now(),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/revise-fast", response_model=MessageResponse, tags=["Quick Actions"])
async def revise_fast(request: QuickActionRequest):
    """
    Get a quick summary for fast revision.
    
    Uses summary mode to provide concise overviews.
    
    - **session_id**: Session identifier (required)
    - **topic**: Specific topic to summarize (optional)
    """
    try:
        session = db.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
        session = ensure_session_paths(session)
        
        # Create or get chat session
        if request.session_id not in chat_sessions:
            chat_sessions[request.session_id] = ChatBot(
                vector_store_path=session['vector_index_path'],
                history_path=session['chat_history_path']
            )
        
        bot = chat_sessions[request.session_id]
        
        # Generate query
        query = f"Summarize {request.topic}" if request.topic else "Provide a summary of the key concepts"
        
        # Get response with summary mode
        response_text = bot.chat(query, use_rag=True, mode="summary")
        
        return MessageResponse(
            response=response_text,
            session_id=request.session_id,
            timestamp=__import__("datetime").datetime.now(),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/ask-questions", response_model=MessageResponse, tags=["Quick Actions"])
async def ask_questions(request: QuickActionRequest):
    """
    Generate exam questions based on the content.
    
    Uses exam mode to create comprehensive test questions.
    
    - **session_id**: Session identifier (required)
    - **topic**: Specific topic to generate questions for (optional)
    """
    try:
        session = db.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {request.session_id} not found")
        session = ensure_session_paths(session)
        
        # Create or get chat session
        if request.session_id not in chat_sessions:
            chat_sessions[request.session_id] = ChatBot(
                vector_store_path=session['vector_index_path'],
                history_path=session['chat_history_path']
            )
        
        bot = chat_sessions[request.session_id]
        
        # Generate query
        query = f"Generate exam questions about {request.topic}" if request.topic else "Generate exam questions based on the content"
        
        # Get response with exam mode
        response_text = bot.chat(query, use_rag=True, mode="exam")
        
        return MessageResponse(
            response=response_text,
            session_id=request.session_id,
            timestamp=__import__("datetime").datetime.now(),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
