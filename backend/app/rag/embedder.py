"""Embedding generation using Ollama."""

from typing import List
import requests
import json


def generate_embeddings(texts: List[str], model: str = "nomic-embed-text") -> List[List[float]]:
    """
    Generate embeddings for text chunks using Ollama.
    
    Args:
        texts: List of text chunks to embed
        model: Ollama embedding model to use
        
    Returns:
        List of embedding vectors
    """
    embeddings = []
    
    for text in texts:
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json={
                "model": model,
                "prompt": text
            }
        )
        
        if response.status_code == 200:
            embedding = response.json()["embedding"]
            embeddings.append(embedding)
        else:
            # Fallback to zero vector if embedding fails
            embeddings.append([0.0] * 768)  # Default dimension
    
    return embeddings


def generate_embedding(text: str, model: str = "nomic-embed-text") -> List[float]:
    """
    Generate embedding for a single text.
    
    Args:
        text: Text to embed
        model: Ollama embedding model to use
        
    Returns:
        Embedding vector
    """
    response = requests.post(
        "http://localhost:11434/api/embeddings",
        json={
            "model": model,
            "prompt": text
        }
    )
    
    if response.status_code == 200:
        return response.json()["embedding"]
    
    return [0.0] * 768  # Fallback
