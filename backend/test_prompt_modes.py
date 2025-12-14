"""Test script for different prompt modes."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db import db
from app.rag.loader import ingest
from app.rag.chat import ChatBot
import uuid


def create_test_content():
    """Create test content about Python programming."""
    test_dir = "test_data"
    os.makedirs(test_dir, exist_ok=True)
    
    test_file = os.path.join(test_dir, "python_basics.txt")
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("""
Python Programming Fundamentals

Python is a high-level, interpreted programming language known for its simplicity and readability.

Key Features:
1. Easy to Learn: Python's syntax is clear and intuitive
2. Dynamically Typed: No need to declare variable types
3. Object-Oriented: Supports OOP principles like inheritance and polymorphism
4. Large Standard Library: Includes modules for many common tasks
5. Cross-Platform: Runs on Windows, Mac, Linux

Basic Concepts:
- Variables: Store data using simple assignments (x = 5)
- Data Types: int, float, str, list, dict, tuple, set
- Control Flow: if/elif/else, for loops, while loops
- Functions: Define reusable code blocks with def keyword
- Modules: Import and use external code libraries

Common Use Cases:
- Web Development (Django, Flask)
- Data Science and Machine Learning (NumPy, Pandas, scikit-learn)
- Automation and Scripting
- Scientific Computing
- Artificial Intelligence

Best Practices:
- Follow PEP 8 style guide
- Use meaningful variable names
- Write docstrings for functions
- Handle exceptions properly
- Keep functions small and focused

Python's philosophy emphasizes code readability and simplicity, making it an excellent choice for beginners and experts alike.
""")
    
    return test_file


def test_prompt_modes():
    """Test all different prompt modes with the same content."""
    
    print("=" * 70)
    print("Prompt Templates Test - Different Modes, Same RAG")
    print("=" * 70)
    
    # Setup
    print("\n[Setup] Creating session and ingesting content...")
    session_id = f"sess-{uuid.uuid4()}"
    vector_path = f"data/vectors/{session_id}"
    history_path = f"data/history/{session_id}.json"
    
    session = db.create_session(
        session_id=session_id,
        name="Prompt Modes Test",
        category_map="notes",
        vector_index_path=vector_path,
        chat_history_path=history_path
    )
    
    # Ingest test content
    test_file = create_test_content()
    result = ingest(test_file, session_id, "notes")
    print(f"✓ Document ingested: {result['chunks_count']} chunks")
    print(f"✓ Session ID: {session_id}")
    
    # Initialize bot
    bot = ChatBot(vector_store_path=vector_path, history_path=history_path)
    
    # Test different modes
    modes = [
        ("chat", "What is Python?"),
        ("summary", "Summarize the key information about Python"),
        ("points", "Extract the most important points about Python"),
        ("flashcards", "Create flashcards for studying Python"),
        ("teacher", "Explain Python programming to a beginner"),
        ("exam", "Generate exam questions about Python")
    ]
    
    for mode, query in modes:
        print("\n" + "=" * 70)
        print(f"MODE: {mode.upper()}")
        print("=" * 70)
        print(f"Query: {query}\n")
        
        # Clear history between modes for clean test
        bot.messages.clear()
        
        response = bot.chat(query, use_rag=True, mode=mode)
        print(response)
        print()
    
    # Cleanup
    print("\n" + "=" * 70)
    print("[Cleanup] Deleting test session...")
    db.delete_session(session_id)
    print("✓ Session deleted")
    
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)
    print("\nAll modes use the same RAG retrieval but different prompt templates:")
    print("  📝 Summary - Concise overviews")
    print("  📌 Important Points - Key information extraction")
    print("  🃏 Flashcards - Study cards with Q&A")
    print("  👨‍🏫 Teacher - Detailed pedagogical explanations")
    print("  📝 Exam Questions - Comprehensive test questions")
    print("=" * 70)


if __name__ == "__main__":
    test_prompt_modes()
