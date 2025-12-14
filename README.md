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
├── frontend/              # Web UI (HTML/CSS/JS)
│   ├── index.html        # Session management page
│   ├── chat.html         # Chat interface
│   ├── style.css         # Dark theme styling
│   ├── js/
│   │   ├── api.js        # API client
│   │   ├── chat.js       # Chat interactions
│   │   └── sessions.js   # Session management
│   ├── Dockerfile        # Frontend container
│   └── nginx.conf        # Nginx reverse proxy config
│
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── main.py       # FastAPI routes
│   │   ├── config.py     # Configuration settings
│   │   ├── db.py         # SQLite database layer
│   │   ├── models.py     # Pydantic models
│   │   ├── processors/   # Document processing
│   │   │   ├── pdf.py
│   │   │   ├── docx.py
│   │   │   ├── pptx.py
│   │   │   └── ocr.py
│   │   └── rag/          # RAG pipeline
│   │       ├── chat.py   # Chatbot logic
│   │       ├── loader.py # Document ingestion
│   │       ├── chunker.py # Text chunking
│   │       ├── embedder.py # Embedding generation
│   │       ├── retriever.py # Vector search
│   │       └── prompts.py # Mode-based prompts
│   ├── data/             # Data storage
│   │   ├── vectors/      # FAISS indices
│   │   ├── history/      # Chat histories
│   │   └── studyrag.db   # SQLite database
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
│
├── docker-compose.yml    # Complete stack orchestration
└── README.md
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

## 📡 API Endpoints

### Sessions
- `GET /sessions` - List all sessions
- `POST /sessions` - Create new session
- `GET /sessions/{id}` - Get session details
- `DELETE /sessions/{id}` - Delete session

### Documents
- `POST /upload` - Upload document
- `GET /sessions/{id}/files` - List uploaded files
- `DELETE /sessions/{id}/files/{file_id}` - Delete file

### Chat
- `POST /chat` - Send message (RAG-enabled)
- `GET /sessions/{id}/history` - Get chat history

### System
- `GET /docs` - Swagger API documentation
- `GET /health` - Health check

## 🐳 Docker Hub

Pre-built images available on Docker Hub:

```bash
# Using Docker Hub images
docker pull zorocancode/studyrag-backend:latest
docker pull zorocancode/studyrag-frontend:latest

# Run with docker-compose
docker-compose up -d
```

## 📊 Data Storage

- **SQLite Database** (`data/studyrag.db`)
  - Sessions metadata
  - Upload records
  - User preferences

- **FAISS Indices** (`data/vectors/`)
  - Per-session vector embeddings
  - Binary index files (.index)
  - Metadata pickles (.meta)

- **Chat History** (`data/history/`)
  - JSON files per session
  - Conversation records with sources

## 🔧 Troubleshooting

### Backend Issues

**CUDA not available:**
```bash
# Reinstall PyTorch with CUDA support
pip uninstall torch torchvision torchaudio -y
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Ollama connection error:**
- Ensure Ollama is running: `ollama serve`
- Check OLLAMA_BASE_URL in config
- Verify network connectivity in Docker

**Out of memory:**
- Reduce CHUNK_SIZE
- Use smaller WHISPER_MODEL (tiny or base)
- Reduce MAX_UPLOAD_SIZE

### Frontend Issues

**API calls failing:**
- Check backend is running on port 8000
- Verify nginx proxy config (frontend/nginx.conf)
- Check CORS headers in FastAPI

**PDF export not working:**
- Ensure html2pdf library is loaded
- Check browser console for errors
- Try a different browser

## 🎯 Usage Examples

### 1. Create a Study Session
1. Open http://localhost
2. Click "Create Session"
3. Enter session name and subject

### 2. Upload Documents
1. Navigate to session
2. Click "📎 Upload"
3. Select PDF, DOCX, or image files
4. Documents are automatically processed

### 3. Ask Questions
1. Type your question in the chat
2. Select a mode (Chat, Explain, Summary, etc.)
3. AI searches documents and provides answers with sources

### 4. Export Conversation
1. Click "📄 Export PDF"
2. Conversation is downloaded with formatting

## 🌐 Environment Variables

Create `.env` file in backend/:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
WHISPER_DEVICE=cuda
DEBUG=False
```

## 📈 Performance Tips

1. **Use GPU for Whisper:** Set `WHISPER_DEVICE=cuda` (requires CUDA PyTorch)
2. **Adjust chunk size:** Larger chunks = faster but less precise
3. **Limit TOP_K_RESULTS:** Smaller values = faster responses
4. **Use medium Whisper model:** Balance between speed and accuracy
5. **Enable GZIP compression:** Already configured in nginx

## 🐛 Known Limitations

- YouTube ingestion removed (use alternative tools)
- Single Ollama model per deployment
- Vector indices stored locally (not distributed)
- SQLite database (suitable for small to medium deployments)

## 🚀 Future Enhancements

- [ ] Multi-LLM support (GPT-4, Claude)
- [ ] Distributed vector store (Weaviate, Milvus)
- [ ] Real-time collaboration
- [ ] Advanced search filters
- [ ] Custom prompt templates
- [ ] Usage analytics dashboard
- [ ] Multiple language support
- [ ] Fine-tuning on custom datasets

## 📝 License

MIT License - See LICENSE file for details

## 👤 Author

**zorocancode** - [Docker Hub](https://hub.docker.com/r/zorocancode)

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

For issues and questions:
- Check [Troubleshooting](#-troubleshooting) section
- Review API docs at `/docs` endpoint
- Check Docker logs: `docker-compose logs -f`

## 🙏 Acknowledgments

- OpenAI Whisper for transcription
- Ollama for local LLM inference
- LangChain for RAG framework
- FAISS for vector similarity search
- FastAPI for the backend framework
- Nginx for reverse proxy

---

**Happy Learning! 📚**