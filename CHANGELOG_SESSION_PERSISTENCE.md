# Fix Summary: Session Last Used + Chat History Persistence

## Issues Fixed

### 1. Missing Last Used Timestamp ✓
**Problem:** Sessions didn't show when they were last accessed

**Solution:**
- Added `last_used` column to sessions table (with automatic migration for existing databases)
- Updated timestamp every time a session is accessed (in `/chat` endpoint)
- Display "Last used: [date & time]" in session cards
- Order sessions by `last_used` DESC so most recent appear first

### 2. Chat History Disappearing on Session Reopen ✓
**Problem:** When opening a previous session, all earlier chats were gone

**Root Cause:** 
- Chat history was being saved to disk in `chat.py`
- But the frontend wasn't loading it when reopening a session
- Backend endpoint existed but frontend wasn't calling it

**Solution:**
- Added `/sessions/{session_id}/history` endpoint to retrieve chat history
- Frontend now calls `loadChatHistory()` when session loads
- Restores all previous messages from the history file
- Shows system message: "✓ Restored X previous messages"

## Backend Changes

### `app/db.py`
```python
# Added last_used column to schema
cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        ...
        last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ...
    )
""")

# Migration for existing databases
def _migrate_add_last_used(self)

# New method to update last_used
def update_last_used(self, session_id: str) -> Optional[Dict]

# Updated ordering
SELECT * FROM sessions ORDER BY last_used DESC
```

### `app/main.py`
```python
# In /chat endpoint, after getting response:
db.update_last_used(session_id)  # Updates timestamp
```

### `app/models.py`
```python
class SessionResponse(BaseModel):
    ...
    last_used: Optional[str] = None
    ...
```

## Frontend Changes

### `frontend/js/api.js`
```javascript
// New method
static async getChatHistory(sessionId)
```

### `frontend/js/sessions.js`
```javascript
// Display last_used in session card
"Last used: ${lastUsedDate}"
```

### `frontend/js/chat.js`
```javascript
// Load chat history when session opens
async function loadChatHistory(session)

// Fetch history from backend
StudyRAGAPI.getChatHistory(currentSessionId)

// Restore messages to UI
data.messages.forEach(msg => {
    if (msg.role === 'user') addUserMessage(msg.content);
    else addAssistantMessage(msg.content);
})
```

## How It Works Now

### User Reopens Previous Session
1. Frontend loads session info from `/api/sessions/{session_id}`
2. Gets `last_used` timestamp
3. Calls `/sessions/{session_id}/history` to fetch chat history
4. Renders all previous messages in chat window
5. Shows "✓ Restored X previous messages"

### User Sends New Message
1. Message sent with selected mode
2. ChatBot loads history from disk: `load_history()`
3. ChatBot responds to message
4. Response saved to history file
5. Backend updates `last_used` timestamp

### Session List
1. Sessions ordered by `last_used DESC` (most recent first)
2. Shows "Last used: [date time]"
3. Shows time when session was first created in tooltip

## Testing

Run the comprehensive test:
```bash
python backend/test_session_persistence.py
```

Tests:
- ✓ Last used timestamp updates correctly
- ✓ Chat history persists across bot restarts
- ✓ Sessions ordered correctly by last_used
- ✓ Messages are restored when reopening session

## Database Migration

If you have an existing database, the code automatically adds the `last_used` column on startup:
```python
def _migrate_add_last_used(self):
    try:
        cursor.execute("ALTER TABLE sessions ADD COLUMN last_used ...")
    except sqlite3.OperationalError:
        # Column already exists
        pass
```

No manual migration needed! ✓

## Files Modified

Backend:
- `app/db.py` - Added last_used column, migration, update_last_used method
- `app/main.py` - Call db.update_last_used() in chat endpoint
- `app/models.py` - Added last_used field to SessionResponse

Frontend:
- `js/api.js` - Added getChatHistory() method
- `js/sessions.js` - Display last_used timestamp in cards
- `js/chat.js` - Load chat history on session open
- `style.css` - Updated session-meta styling

Tests:
- `backend/test_session_persistence.py` - New comprehensive test file
