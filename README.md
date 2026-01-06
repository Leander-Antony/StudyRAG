# StudyRAG - AI-Powered Study Assistant

A comprehensive Retrieval-Augmented Generation (RAG) system for intelligent document processing and conversational learning. StudyRAG allows you to upload educational documents and engage in multi-modal conversations with an AI assistant that understands your study materials.

## 🌟 Features

- **📚 Multi-Format Document Support**
  - PDF, DOCX, PPTX, TXT files
  - Image OCR support (PNG, JPG, JPEG)
  - Automatic text extraction and chunking

- **🤖 Intelligent RAG Engine**
  - Vector-based semantic search using FAISS
  - Retrieves complete document context for answers
  - Token-based text chunking (1024 tokens with 12.5% overlap)
  - Top-K results (configurable, retrieves all chunks by default)

- **💬 Multi-Mode Conversations**
  - Chat mode: General discussion
  - Explain mode: Detailed explanations
  - Summary mode: Quick summaries
  - Points mode: Key takeaways
  - Flashcards mode: Review flashcards
  - Exam mode: Practice questions

- **💾 Session Management**
  - Persistent chat history (stored as JSON)
  - Per-session vector stores
  - Upload tracking and management
  - Automatic history recovery on refresh

- **🎨 Modern Web Interface**
  - Dark theme UI
  - Real-time file upload with progress
  - PDF export of conversations
  - Responsive design
  - Custom scrollbar styling

- **⚙️ Advanced Configuration**
  - GPU support (CUDA/CPU/MPS)
  - FP16/FP32 precision control for Whisper
  - Configurable retrieval strategy
  - Environment-based settings

## 🏗️ Architecture

```
StudyRAG/
├── frontend/          # Web UI (Nginx + HTML/CSS/JS)
├── backend/           # FastAPI + RAG pipeline
│   ├── app/
│   │   ├── processors/  # PDF, DOCX, PPTX, OCR
│   │   └── rag/         # Chunking, embeddings, retrieval
│   └── data/          # Vectors, history, SQLite DB
└── docker-compose.yml
```

## 📋 Prerequisites

### Local Development
- Python 3.11+
- Ollama (for LLM inference)
- CUDA/GPU support (optional, for faster Whisper transcription)
- FFmpeg (for audio processing)
- Tesseract OCR (for image text extraction)

### Docker (Recommended)
- Docker 20.10+
- Docker Compose 2.0+
- 8GB+ RAM recommended

## 🚀 Quick Start

### Option 1: Docker (Easiest)

```bash
# Clone the repository
git clone https://github.com/zorocancode/StudyRAG.git
cd StudyRAG

# Start all services
docker-compose up -d

# On first run, pull the required Ollama models
docker exec ollama-server ollama pull llama3:latest
docker exec ollama-server ollama pull nomic-embed-text

# Access the application
# Frontend: http://localhost
# Backend API: http://localhost:8000/docs
```

### Option 2: Local Development

**Backend Setup:**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Ollama (in separate terminal)
ollama serve

# Pull the required models
ollama pull llama3:latest
ollama pull nomic-embed-text

# Run the backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Setup:**
```bash
cd frontend

# If using a web server (e.g., Python)
python -m http.server 8080

# Or open directly in browser
# file:///path/to/StudyRAG/frontend/index.html
```

## ⚙️ Configuration

Edit `backend/app/config.py`:

```python
# LLM Settings
OLLAMA_MODEL = "llama3:latest"
OLLAMA_BASE_URL = "http://localhost:11434"
TEMPERATURE = 0.7

# RAG Settings
CHUNK_SIZE = 1024  # tokens
CHUNK_OVERLAP_PERCENT = 0.125  # 12.5%
EMBEDDING_MODEL = "nomic-embed-text"  # Ollama embedding model
TOP_K_RESULTS = 1000
ALL_RESULTS = True  # Retrieve all chunks by default

# Whisper Settings
WHISPER_MODEL = "base"  # tiny, base, small, medium, large
WHISPER_FP16 = False  # Use FP32 for stability
WHISPER_DEVICE = "cuda"  # cuda, cpu, mps

# Document Settings
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
SUPPORTED_FORMATS = ["pdf", "docx", "pptx", "txt", "jpg", "png", "jpeg"]
```

## 📡 API Documentation

Complete API documentation available at: `http://localhost:8000/docs` (Swagger UI)

##  Data Storage

- `data/studyrag.db` - SQLite database (sessions, uploads, metadata)
- `data/vectors/` - FAISS vector indices per session
- `data/history/` - JSON chat history files

## 🔧 Troubleshooting

**Models not loading:** Pull Ollama models first:
```bash
docker exec ollama-server ollama pull llama3:latest
docker exec ollama-server ollama pull nomic-embed-text
```

**Connection errors:** Check services with `docker-compose logs -f`

**Out of memory:** Reduce `CHUNK_SIZE` or use smaller `WHISPER_MODEL` in config

## 🎯 Usage

1. **Create Session** → Open `http://localhost` and create a new study session
2. **Upload Documents** → Upload PDF/DOCX/PPTX files (automatically processed)
3. **Chat** → Ask questions, select modes (Chat/Explain/Summary/etc), get AI responses with sources
4. **Export** → Download conversation as PDF

