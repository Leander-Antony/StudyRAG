"""Document retrieval using vector similarity."""

import numpy as np
from typing import List, Tuple
import json
import os


class VectorStore:
    """Simple vector store for embeddings."""
    
    def __init__(self, storage_path: str):
        """
        Initialize vector store.
        
        Args:
            storage_path: Path to store vectors
        """
        self.storage_path = storage_path
        self.vectors = []
        self.metadata = []
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        
        # Load existing vectors if available
        self.load()
    
    def add(self, vectors: List[List[float]], metadata: List[dict]):
        """
        Add vectors and metadata to store.
        
        Args:
            vectors: List of embedding vectors
            metadata: List of metadata dicts for each vector
        """
        self.vectors.extend(vectors)
        self.metadata.extend(metadata)
        self.save()
    
    def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[dict, float]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            
        Returns:
            List of (metadata, similarity_score) tuples
        """
        if not self.vectors:
            return []
        
        # Convert to numpy arrays
        query = np.array(query_vector)
        vectors = np.array(self.vectors)
        
        # Calculate cosine similarity
        similarities = np.dot(vectors, query) / (
            np.linalg.norm(vectors, axis=1) * np.linalg.norm(query)
        )
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Return results
        results = []
        for idx in top_indices:
            results.append((self.metadata[idx], float(similarities[idx])))
        
        return results
    
    def save(self):
        """Save vectors and metadata to disk."""
        data = {
            "vectors": self.vectors,
            "metadata": self.metadata
        }
        
        with open(self.storage_path, 'w') as f:
            json.dump(data, f)
    
    def load(self):
        """Load vectors and metadata from disk."""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                self.vectors = data.get("vectors", [])
                self.metadata = data.get("metadata", [])
