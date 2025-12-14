"""PDF file processor with text extraction and OCR support."""

import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
from typing import Optional


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF file.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text content
    """
    text = ""
    doc = fitz.open(file_path)
    
    for page in doc:
        text += page.get_text()
    
    doc.close()
    return text


def extract_text_with_ocr(file_path: str) -> str:
    """
    Extract text from PDF using OCR (for scanned PDFs).
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text content via OCR
    """
    text = ""
    doc = fitz.open(file_path)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Render page to image
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
        img_data = pix.tobytes("png")
        
        # Convert to PIL Image
        img = Image.open(io.BytesIO(img_data))
        
        # OCR the image
        page_text = pytesseract.image_to_string(img)
        text += page_text + "\n"
    
    doc.close()
    return text


def process_pdf(file_path: str, use_ocr: bool = False) -> str:
    """
    Process PDF file and extract text.
    
    Args:
        file_path: Path to PDF file
        use_ocr: Whether to use OCR for text extraction
        
    Returns:
        Extracted text
    """
    if use_ocr:
        return extract_text_with_ocr(file_path)
    
    # Try regular text extraction first
    text = extract_text_from_pdf(file_path)
    
    # If no text found, fallback to OCR
    if not text.strip():
        return extract_text_with_ocr(file_path)
    
    return text
