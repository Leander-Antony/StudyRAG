"""Test script for document ingestion and RAG query pipeline."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.db import db
from app.rag.loader import ingest
from app.rag.chat import ChatBot
import uuid


def create_test_files():
    """Create sample test files for ingestion."""
    test_dir = "test_data"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create test text files (simulating different document types)
    files = []
    
    # File 1: Machine Learning basics
    file1 = os.path.join(test_dir, "ml_basics.txt")
    with open(file1, 'w', encoding='utf-8') as f:
        f.write("""
Machine Learning Fundamentals

Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. 

Key Concepts:
1. Supervised Learning: Learning from labeled data to make predictions
2. Unsupervised Learning: Finding patterns in unlabeled data
3. Reinforcement Learning: Learning through interaction with environment

Common Algorithms:
- Linear Regression for prediction
- Decision Trees for classification
- Neural Networks for complex patterns
- K-Means for clustering

Applications include image recognition, natural language processing, recommendation systems, and autonomous vehicles.
""")
    files.append(file1)
    
    # File 2: Deep Learning
    file2 = os.path.join(test_dir, "deep_learning.txt")
    with open(file2, 'w', encoding='utf-8') as f:
        f.write("""
Deep Learning Overview

Deep learning is a subset of machine learning that uses artificial neural networks with multiple layers. These networks can automatically learn hierarchical representations of data.

Architecture Components:
- Input Layer: Receives raw data
- Hidden Layers: Process and transform data
- Output Layer: Produces final predictions

Popular Architectures:
1. Convolutional Neural Networks (CNNs) for image processing
2. Recurrent Neural Networks (RNNs) for sequential data
3. Transformers for natural language processing

Training Process:
- Forward propagation
- Loss calculation
- Backpropagation
- Weight updates using gradient descent

Deep learning has revolutionized computer vision, speech recognition, and language translation.
""")
    files.append(file2)
    
    # File 3: Data Science
    file3 = os.path.join(test_dir, "data_science.txt")
    with open(file3, 'w', encoding='utf-8') as f:
        f.write("""
Data Science Fundamentals

Data science combines statistics, programming, and domain knowledge to extract insights from data.

Key Skills:
- Statistical analysis and probability
- Programming (Python, R, SQL)
- Data visualization
- Machine learning
- Communication and storytelling

Data Science Workflow:
1. Problem Definition
2. Data Collection
3. Data Cleaning and Preprocessing
4. Exploratory Data Analysis
5. Feature Engineering
6. Model Building and Training
7. Model Evaluation
8. Deployment and Monitoring

Tools and Technologies:
- Pandas for data manipulation
- NumPy for numerical computing
- Scikit-learn for machine learning
- TensorFlow/PyTorch for deep learning
- Matplotlib/Seaborn for visualization

Data science drives decision-making in business, healthcare, finance, and scientific research.
""")
    files.append(file3)
    
    return files


def test_ingestion_and_query():
    """Test the complete pipeline: ingest documents and query."""
    
    print("=" * 60)
    print("StudyRAG - Document Ingestion and Query Test")
    print("=" * 60)
    
    # Create test files
    print("\n[1/5] Creating test documents...")
    test_files = create_test_files()
    print(f"✓ Created {len(test_files)} test documents")
    
    # Create a test session
    print("\n[2/5] Creating test session...")
    session_id = f"sess-{uuid.uuid4()}"
    vector_path = f"data/vectors/{session_id}"
    
    session = db.create_session(
        session_id=session_id,
        name="AI/ML Study Session",
        category_map="notes",
        vector_index_path=vector_path,
        chat_history_path=f"data/history/{session_id}.json"
    )
    print(f"✓ Session created: {session['name']}")
    print(f"  Session ID: {session_id}")
    
    # Ingest all documents
    print("\n[3/5] Ingesting documents...")
    for i, file_path in enumerate(test_files, 1):
        print(f"\n  Processing file {i}/{len(test_files)}: {os.path.basename(file_path)}")
        result = ingest(file_path, session_id, "notes")
        print(f"  ✓ Status: {result['status']}")
        print(f"  ✓ Chunks created: {result['chunks_count']}")
    
    print("\n✓ All documents ingested successfully!")
    
    # Initialize chatbot with RAG
    print("\n[4/5] Initializing RAG-enabled chatbot...")
    bot = ChatBot(
        vector_store_path=vector_path,
        history_path=f"data/history/{session_id}.json"
    )
    print("✓ Chatbot initialized with vector store and history")
    
    # Test queries
    print("\n[5/5] Testing RAG queries...")
    print("=" * 60)
    
    queries = [
        "What is this topic about?",
        "What are the key concepts in machine learning?",
        "Explain deep learning architectures",
        "What tools are used in data science?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n--- Query {i} ---")
        print(f"Question: {query}")
        print(f"\nAnswer:")
        response = bot.chat(query, use_rag=True)
        print(response)
        print("-" * 60)
    
    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)
    print(f"\nSession ID: {session_id}")
    print(f"Vector Store: {vector_path}")
    print(f"\nYou can continue chatting with this session using the session_id")


def interactive_mode():
    """Interactive query mode."""
    print("\n" + "=" * 60)
    print("Interactive RAG Query Mode")
    print("=" * 60)
    
    session_id = input("\nEnter session ID (or press Enter to create new): ").strip()
    
    if not session_id:
        # Create new session
        session_id = f"sess-{uuid.uuid4()}"
        session = db.create_session(
            session_id=session_id,
            name="Interactive Session",
            category_map="notes",
            vector_index_path=f"data/vectors/{session_id}",
            chat_history_path=f"data/history/{session_id}.json"
        )
        print(f"✓ New session created: {session_id}")
    else:
        session = db.get_session(session_id)
        if not session:
            print(f"✗ Session not found: {session_id}")
            return
    
    vector_path = session['vector_index_path']
    history_path = session['chat_history_path']
    bot = ChatBot(vector_store_path=vector_path, history_path=history_path)
    
    print(f"\nSession: {session['name']}")
    print(f"Vector Store: {vector_path}")
    print(f"Chat History: {history_path}")
    print("Type 'exit' to quit\n")
    
    while True:
        try:
            query = input("You: ").strip()
            if query.lower() == 'exit':
                print("Goodbye!")
                break
            if not query:
                continue
            
            response = bot.chat(query, use_rag=True)
            print(f"\nAssistant: {response}\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        test_ingestion_and_query()
