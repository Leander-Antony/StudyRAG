"""Text chunking logic."""

from typing import List


def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """
    Split text into chunks with overlap.
    
    Args:
        text: Input text to chunk
        chunk_size: Maximum size of each chunk
        chunk_overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        
        # If this is not the last chunk, try to break at sentence boundary
        if end < text_length:
            # Look for sentence endings near the chunk boundary
            sentence_ends = ['. ', '! ', '? ', '\n\n']
            best_break = end
            
            for i in range(max(0, end - 100), min(text_length, end + 100)):
                for ending in sentence_ends:
                    if text[i:i+len(ending)] == ending:
                        best_break = i + len(ending)
                        break
            
            end = best_break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position with overlap
        start = end - chunk_overlap if end < text_length else text_length
    
    return chunks
