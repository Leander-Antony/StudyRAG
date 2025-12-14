"""YouTube content processor using yt-dlp and Whisper."""

import yt_dlp
import whisper
import os
import tempfile
import torch
from app.config import settings


def process_youtube(url: str, model_name: str = None) -> dict:
    """
    Extract text from YouTube video using yt-dlp and Whisper.
    
    Args:
        url: YouTube video URL
        model_name: Whisper model to use (uses config default if None)
        
    Returns:
        Dictionary with 'text' and 'title' keys
    """
    if model_name is None:
        model_name = settings.WHISPER_MODEL
        
    # Create temporary directory for audio
    temp_dir = tempfile.mkdtemp()
    audio_path = os.path.join(temp_dir, "audio.mp3")
    
    try:
        # Download audio from YouTube - use direct audio format without ffmpeg conversion
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': audio_path,
            'quiet': False,  # Show output for debugging
            'no_warnings': False,
            'extract_audio': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        
        # Extract video title
        video_title = info.get('title', 'Unknown Video')
            
        # Find the downloaded audio file (could have various extensions)
        downloaded_file = None
        for file in os.listdir(temp_dir):
            if file.startswith('audio'):
                downloaded_file = os.path.join(temp_dir, file)
                break
        
        if not downloaded_file or not os.path.exists(downloaded_file):
            raise Exception(f"Audio file not found in {temp_dir}")
        
        if not downloaded_file or not os.path.exists(downloaded_file):
            raise Exception(f"Audio file not found in {temp_dir}")
        
        # Load Whisper model with GPU support and proper device mapping
        print(f"Loading Whisper model: {model_name} on device: {settings.WHISPER_DEVICE}")
        try:
            # Try to load on the specified device
            model = whisper.load_model(model_name, device=settings.WHISPER_DEVICE)
        except RuntimeError as e:
            # If CUDA fails (model cached for different device), fall back to CPU
            if "cuda" in str(e).lower() or "device" in str(e).lower():
                print(f"Warning: CUDA load failed, falling back to CPU: {e}")
                model = whisper.load_model(model_name, device="cpu")
            else:
                raise
        
        # Transcribe audio (force FP32 if configured)
        print(f"Transcribing audio from: {downloaded_file}")
        result = model.transcribe(downloaded_file, fp16=settings.WHISPER_FP16)
        text = result["text"]
        
        return {
            "text": text,
            "title": video_title
        }
    
    finally:
        # Cleanup - be more careful with file removal
        try:
            # yt-dlp may have created audio.mp3.mp3 or similar variations
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(temp_dir)
        except Exception as e:
            print(f"Warning: Cleanup failed for {temp_dir}: {e}")
