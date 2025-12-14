"""Document retrieval using FAISS vector similarity."""

import numpy as np
from typing import List, Tuple
import json
import os
import faiss
import pickle


class VectorStore:
    """FAISS-based vector store for embeddings."""
    
    def __init__(self, storage_path: str):
        """
        Initialize vector store.
        
        Args:
            storage_path: Path to store vectors (without extension)
        """
        self.storage_path = storage_path
        self.index = None
        self.metadata = []
        self.dimension = None
        
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
        if not vectors:
            return
            
        vectors_array = np.array(vectors, dtype=np.float32)
        
        # Initialize index if first time
        if self.index is None:
            self.dimension = vectors_array.shape[1]
            self.index = faiss.IndexFlatIP(self.dimension)  # Inner product (cosine similarity)
            # Normalize vectors for cosine similarity
            faiss.normalize_L2(vectors_array)
        else:
            # Normalize new vectors
            faiss.normalize_L2(vectors_array)
        
        # Add to index
        self.index.add(vectors_array)
        self.metadata.extend(metadata)
        
        # Save immediately
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
        if self.index is None or self.index.ntotal == 0:
            return []
        
        # Convert to numpy and normalize
        query = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(query)
        
        # Search
        k = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(query, k)
        
        # Return results
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.metadata):
                results.append((self.metadata[idx], float(distance)))
        
        return results
    
    def save(self):
        """Save index and metadata to disk."""
        if self.index is not None:
            # Save FAISS index
            faiss.write_index(self.index, f"{self.storage_path}.index")
            
            # Save metadata
            with open(f"{self.storage_path}.meta", 'wb') as f:
                pickle.dump({
                    'metadata': self.metadata,
                    'dimension': self.dimension
                }, f)
    
    def load(self):
        """Load index and metadata from disk."""
        index_path = f"{self.storage_path}.index"
        meta_path = f"{self.storage_path}.meta"
        
        if os.path.exists(index_path) and os.path.exists(meta_path):
            # Load FAISS index
            self.index = faiss.read_index(index_path)
            
            # Load metadata
            with open(meta_path, 'rb') as f:
                data = pickle.load(f)
                self.metadata = data.get("metadata", [])
                self.dimension = data.get("dimension", None)
