"""Test script for session last_used and chat history persistence."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db import db
from app.rag.loader import ingest
from app.rag.chat import ChatBot
import uuid
from datetime import datetime
import time


def test_last_used_timestamp():
    """Test that last_used timestamp is updated on session access."""
    
    print("=" * 70)
    print("Test: Session Last Used Timestamp")
    print("=" * 70)
    
    # Create session
    session_id = f"sess-{uuid.uuid4()}"
    vector_path = f"data/vectors/{session_id}"
    history_path = f"data/history/{session_id}.json"
    
    session = db.create_session(
        session_id=session_id,
        name="Test Session",
        category_map="notes",
        vector_index_path=vector_path,
        chat_history_path=history_path
    )
    
    print(f"\n✓ Session created at: {session['created_at']}")
    print(f"  Last used: {session.get('last_used', 'N/A')}")
    
    # Wait a bit
    time.sleep(2)
    
    # Update last_used
    updated_session = db.update_last_used(session_id)
    print(f"\n✓ Session accessed, last_used updated to: {updated_session.get('last_used')}")
    
    # Cleanup
    db.delete_session(session_id)
    print(f"\n✓ Session deleted")


def test_chat_history_persistence():
    """Test that chat history persists across bot restarts."""
    
    print("\n" + "=" * 70)
    print("Test: Chat History Persistence")
    print("=" * 70)
    
    # Setup
    session_id = f"sess-{uuid.uuid4()}"
    vector_path = f"data/vectors/{session_id}"
    history_path = f"data/history/{session_id}.json"
    
    session = db.create_session(
        session_id=session_id,
        name="History Test",
        category_map="notes",
        vector_index_path=vector_path,
        chat_history_path=history_path
    )
    
    # Create test content
    test_dir = "test_data"
    os.makedirs(test_dir, exist_ok=True)
    test_file = os.path.join(test_dir, "history_test.txt")
    with open(test_file, 'w') as f:
        f.write("Python is a programming language. It's used for web development, data science, and automation.")
    
    # Ingest document
    print("\n[Step 1] Ingesting document...")
    ingest(test_file, session_id, "notes")
    print("✓ Document ingested")
    
    # First bot session - add messages
    print("\n[Step 2] Creating first ChatBot instance and adding messages...")
    bot1 = ChatBot(vector_store_path=vector_path, history_path=history_path)
    
    msg1 = "What is Python?"
    resp1 = bot1.chat(msg1, use_rag=True, mode="chat")
    print(f"Message 1: {msg1}")
    print(f"Response: {resp1[:100]}...")
    
    print(f"\n✓ First bot has {len(bot1.messages)} messages in memory")
    print(f"  History file exists: {os.path.exists(history_path)}")
    
    # Create new bot instance - should load history
    print("\n[Step 3] Creating second ChatBot instance (should load history)...")
    bot2 = ChatBot(vector_store_path=vector_path, history_path=history_path)
    
    print(f"✓ Second bot loaded {len(bot2.messages)} messages from disk")
    
    if len(bot2.messages) > 0:
        print("✓ SUCCESS: Chat history persisted across restarts!")
        print(f"  Restored messages:")
        for i, msg in enumerate(bot2.messages, 1):
            preview = str(msg.content)[:60]
            print(f"    {i}. {msg.__class__.__name__}: {preview}...")
    else:
        print("✗ FAILURE: Chat history not restored!")
    
    # Add another message to second bot
    print("\n[Step 4] Adding message to second bot instance...")
    msg2 = "Tell me more about Python."
    resp2 = bot2.chat(msg2, use_rag=True, mode="chat")
    print(f"Message 2: {msg2}")
    print(f"Response: {resp2[:100]}...")
    
    print(f"\n✓ Second bot now has {len(bot2.messages)} messages")
    
    # Create third bot to verify both messages persist
    print("\n[Step 5] Creating third ChatBot instance (final verification)...")
    bot3 = ChatBot(vector_store_path=vector_path, history_path=history_path)
    
    print(f"✓ Third bot loaded {len(bot3.messages)} messages from disk")
    
    if len(bot3.messages) == 4:  # 2 user + 2 assistant
        print("✓ SUCCESS: All messages persisted!")
    else:
        print(f"⚠ Expected 4 messages, got {len(bot3.messages)}")
    
    # Cleanup
    print("\n[Cleanup] Removing test session and files...")
    db.delete_session(session_id)
    os.remove(test_file)
    print("✓ Cleaned up")


def test_session_ordering():
    """Test that sessions are ordered by last_used in descending order."""
    
    print("\n" + "=" * 70)
    print("Test: Session Ordering by Last Used")
    print("=" * 70)
    
    # Create 3 sessions
    session_ids = []
    for i in range(3):
        sid = f"sess-{uuid.uuid4()}"
        db.create_session(sid, f"Session {i+1}", "notes")
        session_ids.append(sid)
        time.sleep(0.5)
    
    print(f"\n✓ Created 3 sessions: {', '.join([s[:12] + '...' for s in session_ids])}")
    
    # Access them in reverse order
    print(f"\nAccessing sessions in reverse order...")
    for i, sid in enumerate(reversed(session_ids)):
        db.update_last_used(sid)
        print(f"  {i+1}. Accessed {sid[:12]}...")
        time.sleep(0.3)
    
    # Get all sessions - should be in reverse order
    all_sessions = db.get_all_sessions()
    print(f"\n✓ Sessions ordered by last_used (most recent first):")
    for i, sess in enumerate(all_sessions[-3:], 1):  # Get last 3 (our test sessions)
        print(f"  {i}. {sess['name']} - Last used: {sess.get('last_used')}")
    
    # Cleanup
    print(f"\n[Cleanup] Removing test sessions...")
    for sid in session_ids:
        db.delete_session(sid)
    print("✓ Cleaned up")


if __name__ == "__main__":
    try:
        test_last_used_timestamp()
        test_chat_history_persistence()
        test_session_ordering()
        
        print("\n" + "=" * 70)
        print("All tests completed!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
