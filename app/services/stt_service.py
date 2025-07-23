import whisper
import torch
import os
import logging
from typing import Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

class STTService:
    """Service for Speech-to-Text using OpenAI's Whisper."""
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(STTService, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'model'):  # Ensure model is loaded only once
            self.device = "cuda" if torch.cuda.is_available() and not settings.FORCE_CPU else "cpu"
            self.model_name = settings.STT_MODEL_NAME
            self.model_dir = settings.STT_MODEL_DIR
            self.model = self._load_model()
            logger.info(f"STT Service initialized on device: {self.device}")

    def _load_model(self):
        """Load the Whisper model."""
        logger.info(f"Loading Whisper model '{self.model_name}'...")
        try:
            model = whisper.load_model(self.model_name, device=self.device, download_root=self.model_dir)
            logger.info(f"Whisper model '{self.model_name}' loaded successfully.")
            return model
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            raise RuntimeError(f"Could not load Whisper model '{self.model_name}'. Please check model name and paths.")

    def transcribe(self, audio_file_path: str) -> Dict:
        """
        Transcribe an audio file to text.

        Args:
            audio_file_path: The path to the audio file.

        Returns:
            A dictionary containing the transcription result.
        """
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found at: {audio_file_path}")
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
        logger.info(f"Starting transcription for: {audio_file_path}")
        
        try:
            result = self.model.transcribe(audio_file_path, fp16=self.device=="cuda")
            logger.info(f"Transcription successful for: {audio_file_path}")
            return result
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
            raise

def get_stt_service() -> STTService:
    """Dependency injector for the STTService."""
    return STTService() 