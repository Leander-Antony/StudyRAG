# StudyRAG Frontend

Minimal, function-first UI for the StudyRAG system.

## Structure

```
frontend/
├── index.html          # Session list and management
├── chat.html           # Main chat interface
├── style.css           # Shared styling
├── js/
│   ├── api.js         # Backend API client
│   ├── sessions.js    # Session management logic
│   └── chat.js        # Chat interface logic
└── README.md
```

## Pages

### 1. **Sessions List** (`index.html`)
- View all study sessions
- Create new session (modal)
- Delete sessions
- Jump to chat for any session

### 2. **Chat Screen** (`chat.html`)
- Main interaction with StudyRAG
- Message history
- Mode selector (chat, teacher, summary, points, flashcards, exam)
- Quick action buttons (1-click intelligence)
- Document upload panel
- Real-time responses

## Quick Actions

One-click endpoints for common study tasks:

- 🎓 **Explain Simple** - Teacher mode explanation
- 📌 **Important Points** - Extract key information
- 📝 **Revise Fast** - Quick summary
- ❓ **Ask Questions** - Generate exam questions

## API Integration

All communication with backend via `api.js`:

```javascript
// Create session
await StudyRAGAPI.createSession('ML Notes', 'notes');

// Chat with mode
await StudyRAGAPI.chat(sessionId, 'message', 'teacher');

// Quick actions
await StudyRAGAPI.explainSimple(sessionId, 'topic');
await StudyRAGAPI.importantPoints(sessionId);
await StudyRAGAPI.reviseFast(sessionId);
await StudyRAGAPI.askQuestions(sessionId);

// Upload document
await StudyRAGAPI.uploadDocument(sessionId, file, 'notes');
```

## Running

1. Start backend: `python -m uvicorn backend.app.main:app --reload`
2. Open `index.html` in browser (or serve via local server)
3. Create a session
4. Upload documents
5. Chat with RAG + quick actions

## Design Philosophy

**Function > Beauty**

- No CSS frameworks
- Clean, readable HTML
- Simple, focused UI
- Fast interactions
- Mobile responsive basics
- Focus on usability

## Future Enhancements

- Offline support (localStorage)
- Real-time collaboration
- Export chat history
- Session sharing
- Dark mode
