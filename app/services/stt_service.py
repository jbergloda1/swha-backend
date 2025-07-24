import whisper
import torch
import os
import logging
import tempfile
import struct
import wave
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

    def _create_wav_header(self, data_length: int, sample_rate: int = 16000, channels: int = 1, bits_per_sample: int = 16) -> bytes:
        """Create a WAV file header for raw audio data."""
        # WAV file format specifications
        byte_rate = sample_rate * channels * bits_per_sample // 8
        block_align = channels * bits_per_sample // 8
        
        header = struct.pack('<4sI4s4sIHHIIHH4sI',
            b'RIFF',           # Chunk ID
            36 + data_length,  # Chunk size
            b'WAVE',           # Format
            b'fmt ',           # Subchunk1 ID
            16,                # Subchunk1 size (PCM)
            1,                 # Audio format (PCM)
            channels,          # Number of channels
            sample_rate,       # Sample rate
            byte_rate,         # Byte rate
            block_align,       # Block align
            bits_per_sample,   # Bits per sample
            b'data',           # Subchunk2 ID
            data_length        # Subchunk2 size
        )
        
        return header

    def _convert_to_wav(self, audio_bytes: bytes) -> bytes:
        """Convert raw audio data to proper WAV format."""
        try:
            # Check if it's already a valid WAV file
            if audio_bytes.startswith(b'RIFF') and b'WAVE' in audio_bytes[:12]:
                logger.info("Audio is already in WAV format")
                return audio_bytes
            
            # For MediaRecorder chunks, we need to handle them as raw audio data
            # Most browsers produce WebM with Opus codec, but chunks are often raw PCM-like data
            
            # Try to detect if this looks like raw PCM data
            if len(audio_bytes) > 0:
                logger.info(f"Converting {len(audio_bytes)} bytes to WAV format")
                
                # Assume 16kHz, mono, 16-bit PCM (common for speech)
                # This is a reasonable assumption for most speech applications
                wav_header = self._create_wav_header(len(audio_bytes))
                wav_data = wav_header + audio_bytes
                
                logger.info("Successfully created WAV file with header")
                return wav_data
            
            return audio_bytes
            
        except Exception as e:
            logger.error(f"Error converting to WAV: {e}")
            # If conversion fails, return original data and let Whisper handle it
            return audio_bytes

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

    def transcribe_stream(self, audio_bytes: bytes) -> Dict:
        """
        Transcribe an audio stream (bytes) to text.

        Args:
            audio_bytes: The audio data in bytes.

        Returns:
            A dictionary containing the transcription result.
        """
        logger.info(f"Starting transcription for audio stream ({len(audio_bytes)} bytes).")
        tmp_path = None
        
        try:
            # Convert raw audio bytes to proper WAV format
            wav_data = self._convert_to_wav(audio_bytes)
            
            # Save as WAV file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(wav_data)
                tmp_path = tmp.name
            
            logger.info(f"Saved audio to temporary WAV file: {tmp_path}")
            
            # Use Whisper to transcribe
            result = self.transcribe(tmp_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Error during stream transcription: {e}")
            raise
        finally:
            # Clean up the temporary file
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                    logger.info(f"Cleaned up temporary file: {tmp_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file {tmp_path}: {e}")

def get_stt_service() -> STTService:
    """Dependency injector for the STTService."""
    return STTService() 