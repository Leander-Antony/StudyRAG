"""Text chunking logic with token-based strategy."""

from typing import List
import tiktoken
from app.config import settings


def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """
    Count tokens in text.
    
    Args:
        text: Input text
        encoding_name: Tokenizer encoding to use
        
    Returns:
        Token count
    """
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def chunk_text(
    text: str, 
    chunk_size: int = None,
    overlap_percent: float = None
) -> List[str]:
    """
    Split text into chunks based on token count with percentage overlap.
    
    Args:
        text: Input text to chunk
        chunk_size: Target token count per chunk (uses config default if None)
        overlap_percent: Overlap as percentage (uses config default if None)
        
    Returns:
        List of text chunks
    """
    if chunk_size is None:
        chunk_size = settings.CHUNK_SIZE
    if overlap_percent is None:
        overlap_percent = settings.CHUNK_OVERLAP_PERCENT
        
    if not text or not text.strip():
        return []
    
    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(text)
    
    if len(tokens) <= chunk_size:
        return [text]
    
    chunks = []
    overlap_tokens = int(chunk_size * overlap_percent)
    start = 0
    
    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        
        # Decode tokens back to text
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text.strip())
        
        # Move start position with overlap
        start = end - overlap_tokens
        
        # Prevent infinite loop on last chunk
        if start >= len(tokens):
            break
    
    return chunks
