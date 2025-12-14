"""Embedding generation using Ollama."""

from typing import List
import requests
import json
from app.config import settings


def generate_embeddings(texts: List[str], model: str = None) -> List[List[float]]:
    """
    Generate embeddings for text chunks using Ollama.
    
    Args:
        texts: List of text chunks to embed
        model: Ollama embedding model to use (uses config default if None)
        
    Returns:
        List of embedding vectors
    """
    if model is None:
        model = settings.EMBEDDING_MODEL
        
    embeddings = []
    
    for text in texts:
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/embeddings",
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


def generate_embedding(text: str, model: str = None) -> List[float]:
    """
    Generate embedding for a single text.
    
    Args:
        text: Text to embed
        model: Ollama embedding model to use (uses config default if None)
        
    Returns:
        Embedding vector
    """
    if model is None:
        model = settings.EMBEDDING_MODEL
        
    response = requests.post(
        f"{settings.OLLAMA_BASE_URL}/api/embeddings",
        json={
            "model": model,
            "prompt": text
        }
    )
    
    if response.status_code == 200:
        return response.json()["embedding"]
    
    return [0.0] * 768  # Fallback
