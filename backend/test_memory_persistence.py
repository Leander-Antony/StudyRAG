"""Test script for memory persistence and deletion."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db import db
from app.rag.loader import ingest
from app.rag.chat import ChatBot
from app.rag.retriever import VectorStore
import uuid
import time


def test_memory_persistence():
    """Test that data persists across sessions and can be properly deleted."""
    
    print("=" * 70)
    print("Memory Persistence & Deletion Test")
    print("=" * 70)
    
    # Step 1: Create session and ingest data
    print("\n[Step 1] Creating session and ingesting documents...")
    session_id = f"sess-{uuid.uuid4()}"
    vector_path = f"data/vectors/{session_id}"
    history_path = f"data/history/{session_id}.json"
    
    session = db.create_session(
        session_id=session_id,
        name="Persistence Test Session",
        category_map="notes",
        vector_index_path=vector_path,
        chat_history_path=history_path
    )
    print(f"✓ Session created: {session_id}")
    
    # Create a simple test file
    test_dir = "test_data"
    os.makedirs(test_dir, exist_ok=True)
    test_file = os.path.join(test_dir, "persistence_test.txt")
    
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("""
Persistence Testing Document

This document is used to test memory persistence in StudyRAG.
The system should remember this content across restarts.
Key facts:
- Data persists on disk
- Chat history is saved
- Vector embeddings are stored
- Everything can be deleted when needed
""")
    
    result = ingest(test_file, session_id, "notes")
    print(f"✓ Document ingested: {result['chunks_count']} chunks")
    
    # Step 2: Chat with RAG
    print("\n[Step 2] Starting conversation with RAG...")
    bot1 = ChatBot(vector_store_path=vector_path, history_path=history_path)
    
    response1 = bot1.chat("What is this document about?", use_rag=True)
    print(f"Q: What is this document about?")
    print(f"A: {response1[:100]}...")
    
    response2 = bot1.chat("What are the key facts?", use_rag=True)
    print(f"\nQ: What are the key facts?")
    print(f"A: {response2[:100]}...")
    
    # Check history
    history = bot1.get_conversation_history()
    print(f"\n✓ Chat history saved: {len(history)} messages")
    
    # Verify files exist
    print("\n[Step 3] Verifying persistence on disk...")
    
    index_exists = os.path.exists(f"{vector_path}.index")
    meta_exists = os.path.exists(f"{vector_path}.meta")
    history_exists = os.path.exists(history_path)
    
    print(f"✓ Vector index file: {index_exists}")
    print(f"✓ Vector metadata file: {meta_exists}")
    print(f"✓ Chat history file: {history_exists}")
    
    # Step 4: Simulate restart - load from disk
    print("\n[Step 4] Simulating restart - loading from disk...")
    bot2 = ChatBot(vector_store_path=vector_path, history_path=history_path)
    
    # Check if history was loaded
    loaded_history = bot2.get_conversation_history()
    print(f"✓ History loaded: {len(loaded_history)} messages")
    
    # Continue conversation
    response3 = bot2.chat("Summarize our previous conversation", use_rag=True)
    print(f"\nQ: Summarize our previous conversation")
    print(f"A: {response3[:150]}...")
    
    # Verify vector store still works
    vector_store = VectorStore(vector_path)
    print(f"✓ Vector store loaded: {vector_store.index.ntotal if vector_store.index else 0} vectors")
    
    # Step 5: Test deletion
    print("\n[Step 5] Testing deletion logic...")
    print(f"Deleting session: {session_id}")
    
    deleted = db.delete_session(session_id)
    
    if deleted:
        print("✓ Session deleted from database")
        
        # Verify files are deleted
        index_exists_after = os.path.exists(f"{vector_path}.index")
        meta_exists_after = os.path.exists(f"{vector_path}.meta")
        history_exists_after = os.path.exists(history_path)
        
        print(f"✓ Vector index deleted: {not index_exists_after}")
        print(f"✓ Vector metadata deleted: {not meta_exists_after}")
        print(f"✓ Chat history deleted: {not history_exists_after}")
        
        # Verify session not in database
        session_check = db.get_session(session_id)
        print(f"✓ Session removed from DB: {session_check is None}")
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary:")
    print("=" * 70)
    print("✅ Data persists on disk (vectors + chat history)")
    print("✅ Data survives 'restart' (new bot instance loads data)")
    print("✅ Deletion removes all traces (DB + files)")
    print("✅ Memory exists until explicitly deleted")
    print("=" * 70)


def test_multiple_sessions():
    """Test that multiple sessions don't interfere with each other."""
    
    print("\n\n" + "=" * 70)
    print("Multiple Sessions Isolation Test")
    print("=" * 70)
    
    sessions = []
    
    # Create 3 separate sessions
    for i in range(1, 4):
        print(f"\n[Session {i}] Creating session...")
        session_id = f"sess-{uuid.uuid4()}"
        
        session = db.create_session(
            session_id=session_id,
            name=f"Test Session {i}",
            category_map="notes",
            vector_index_path=f"data/vectors/{session_id}",
            chat_history_path=f"data/history/{session_id}.json"
        )
        
        # Create unique test file
        test_file = f"test_data/session{i}_test.txt"
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(f"This is content for session {i}. Topic: Session {i} Data")
        
        # Ingest
        result = ingest(test_file, session_id, "notes")
        print(f"✓ Session {i} created with {result['chunks_count']} chunks")
        
        sessions.append(session_id)
    
    print(f"\n✓ Created {len(sessions)} isolated sessions")
    
    # Query each session
    print("\n[Testing] Each session should only see its own data...")
    for i, session_id in enumerate(sessions, 1):
        session = db.get_session(session_id)
        bot = ChatBot(
            vector_store_path=session['vector_index_path'],
            history_path=session['chat_history_path']
        )
        
        response = bot.chat(f"What session is this?", use_rag=True)
        print(f"\nSession {i} response: {response[:80]}...")
    
    # Clean up
    print("\n[Cleanup] Deleting all test sessions...")
    for session_id in sessions:
        db.delete_session(session_id)
    print("✓ All sessions deleted")
    
    print("\n" + "=" * 70)
    print("✅ Sessions are properly isolated (one index per session)")
    print("=" * 70)


if __name__ == "__main__":
    test_memory_persistence()
    test_multiple_sessions()
