"""YouTube content processor using yt-dlp and Whisper."""

import yt_dlp
import whisper
import os
import tempfile
from app.config import settings


def process_youtube(url: str, model_name: str = None) -> str:
    """
    Extract text from YouTube video using yt-dlp and Whisper.
    
    Args:
        url: YouTube video URL
        model_name: Whisper model to use (uses config default if None)
        
    Returns:
        Transcribed text
    """
    if model_name is None:
        model_name = settings.WHISPER_MODEL
        
    # Create temporary directory for audio
    temp_dir = tempfile.mkdtemp()
    audio_path = os.path.join(temp_dir, "audio.mp3")
    
    try:
        # Download audio from YouTube
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': audio_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Load Whisper model
        model = whisper.load_model(model_name)
        
        # Transcribe audio
        result = model.transcribe(audio_path)
        text = result["text"]
        
        return text
    
    finally:
        # Cleanup
        if os.path.exists(audio_path):
            os.remove(audio_path)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)
