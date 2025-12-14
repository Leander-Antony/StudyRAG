"""Test script for document ingestion pipeline."""

from app.db import db
from app.rag.loader import ingest
import uuid


def test_ingestion():
    """Test the unified ingestion interface."""
    
    # Create a test session
    session_id = f"sess-{uuid.uuid4()}"
    
    print("Creating test session...")
    session = db.create_session(
        session_id=session_id,
        name="Test Session",
        category_map="notes",
        vector_index_path=f"data/vectors/{session_id}.json",
        chat_history_path=f"data/history/{session_id}.json"
    )
    
    print(f"Session created: {session['session_id']}")
    print(f"Session name: {session['name']}")
    
    # Test file path (replace with your actual file)
    test_file = "path/to/your/test.pdf"  # Change this
    
    # Uncomment to test with a real file:
    # print(f"\nIngesting document: {test_file}")
    # result = ingest(test_file, session_id, "notes")
    # print(f"Status: {result['status']}")
    # print(f"Message: {result['message']}")
    # print(f"Chunks: {result['chunks_count']}")
    
    # Test YouTube ingestion (uncomment to test)
    # youtube_url = "https://www.youtube.com/watch?v=EXAMPLE"
    # print(f"\nIngesting YouTube video: {youtube_url}")
    # result = ingest(youtube_url, session_id, "notes")
    # print(f"Status: {result['status']}")
    # print(f"Message: {result['message']}")
    
    print("\nTest completed!")


if __name__ == "__main__":
    test_ingestion()
