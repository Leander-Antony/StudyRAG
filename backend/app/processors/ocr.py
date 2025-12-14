"""OCR processor for image files."""

from PIL import Image
import pytesseract


def process_image_ocr(file_path: str) -> str:
    """
    Extract text from image using OCR.
    
    Args:
        file_path: Path to image file
        
    Returns:
        Extracted text via OCR
    """
    img = Image.open(file_path)
    text = pytesseract.image_to_string(img)
    return text
