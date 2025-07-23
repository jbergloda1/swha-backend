import os
import time
import logging
from typing import List, Dict, Optional, Tuple
import soundfile as sf
from kokoro import KPipeline
import torch

from app.core.config import settings
from app.services.s3_service import get_s3_service
from app.schemas.tts import AudioSegment

logger = logging.getLogger(__name__)

class TTSService:
    """Service for Text-to-Speech using Kokoro library."""
    
    def __init__(self):
        self.pipelines: Dict[str, KPipeline] = {}  # Cache pipelines by language
        self.audio_dir = "app/static/audio"
        self.s3_service = get_s3_service()
        self._ensure_audio_directory()
        self._setup_spacy_environment()
    
    def _ensure_audio_directory(self):
        """Ensure audio directory exists."""
        os.makedirs(self.audio_dir, exist_ok=True)
        logger.info(f"Audio directory ensured: {self.audio_dir}")
    
    def _setup_spacy_environment(self):
        """Setup spaCy environment variables for proper model loading."""
        # Set up spaCy data directories
        spacy_dirs = [
            "/home/app/.cache/spacy",
            "/app/.cache/spacy",
            os.path.expanduser("~/.cache/spacy")
        ]
        
        # Create directories if they don't exist
        for spacy_dir in spacy_dirs:
            try:
                os.makedirs(spacy_dir, exist_ok=True)
            except Exception as e:
                logger.warning(f"Could not create spaCy directory {spacy_dir}: {e}")
        
        # Set environment variables
        if not os.environ.get('SPACY_DATA'):
            os.environ['SPACY_DATA'] = "/home/app/.cache/spacy"
        
        logger.info(f"spaCy environment setup completed. SPACY_DATA: {os.environ.get('SPACY_DATA')}")
    
    def _download_spacy_models_if_needed(self):
        """Download spaCy models if they're not available."""
        try:
            import spacy
            
            models_to_check = ['en_core_web_sm', 'en_core_web_md']
            
            for model in models_to_check:
                try:
                    spacy.load(model)
                    logger.info(f"spaCy model {model} is available")
                except OSError:
                    logger.warning(f"spaCy model {model} not found, attempting to download...")
                    try:
                        spacy.cli.download(model)
                        logger.info(f"Successfully downloaded spaCy model: {model}")
                    except Exception as e:
                        logger.warning(f"Failed to download spaCy model {model}: {e}")
                        # Try alternative download method
                        try:
                            os.system(f"python -m spacy download {model}")
                            logger.info(f"Downloaded {model} via alternative method")
                        except Exception as e2:
                            logger.error(f"All download methods failed for {model}: {e2}")
                            
        except ImportError:
            logger.error("spaCy not available")
    
    def _get_pipeline(self, language_code: str) -> KPipeline:
        """Get or create pipeline for specific language with error handling."""
        if language_code not in self.pipelines:
            logger.info(f"Loading TTS pipeline for language: {language_code}")
            
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    # Setup environment before attempting to load
                    self._setup_spacy_environment()
                    
                    # Try to download spaCy models if needed
                    if attempt > 0:  # Only try downloading on retry
                        self._download_spacy_models_if_needed()
                    
                    # Initialize Kokoro pipeline
                    self.pipelines[language_code] = KPipeline(lang_code=language_code)
                    logger.info(f"TTS pipeline loaded successfully for language: {language_code}")
                    break
                    
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1}/{max_retries} failed to load TTS pipeline for {language_code}: {str(e)}")
                    
                    if attempt < max_retries - 1:
                        logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        # Final attempt failed
                        error_msg = f"Failed to load TTS pipeline for {language_code} after {max_retries} attempts: {str(e)}"
                        logger.error(error_msg)
                        
                        # Provide helpful error message
                        if "spacy" in str(e).lower() or "en_core_web" in str(e):
                            error_msg = (
                                f"TTS initialization failed due to missing spaCy models. "
                                f"This usually happens when models weren't properly downloaded during Docker build. "
                                f"Original error: {str(e)}"
                            )
                        
                        raise Exception(error_msg)
        
        return self.pipelines[language_code]
    
    def _create_s3_key(self, session_id: str, filename: str, user_id: Optional[int] = None) -> str:
        """Create S3 object key for audio file."""
        prefix = f"audio/users/{user_id}" if user_id else "audio/anonymous"
        return f"{prefix}/{session_id}/{filename}"
    
    def _upload_to_s3_and_get_presigned_url(
        self,
        local_file_path: str,
        session_id: str,
        filename: str,
        user_id: Optional[int] = None,
        expiry_seconds: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Upload file to S3 and return presigned URL and S3 key.
        
        Returns:
            Tuple of (presigned_url, s3_key) or (None, None) if error
        """
        if not self.s3_service:
            logger.warning("S3 service not available, skipping S3 upload")
            return None, None
        
        try:
            s3_key = self._create_s3_key(session_id, filename, user_id)
            
            # Helper function to ensure ASCII-safe metadata
            def make_ascii_safe(value: str, max_length: int = 100) -> str:
                """Convert string to ASCII-safe format for S3 metadata."""
                if not isinstance(value, str):
                    value = str(value)
                
                # Truncate if too long
                if len(value) > max_length:
                    value = value[:max_length]
                
                # Remove or replace non-ASCII characters
                try:
                    # Try to encode as ASCII
                    value.encode('ascii')
                    return value
                except UnicodeEncodeError:
                    # Replace non-ASCII characters with safe alternatives
                    import unicodedata
                    # Normalize and remove accents
                    value = unicodedata.normalize('NFKD', value)
                    value = ''.join(c for c in value if ord(c) < 128)
                    # If still problematic, use safe characters only
                    if not value or not value.strip():
                        value = "generated_content"
                    return value
            
            # Add metadata with ASCII-safe values
            file_metadata = {
                "session-id": make_ascii_safe(session_id, 50),
                "user-id": make_ascii_safe(str(user_id) if user_id else "anonymous", 20),
                "generated-at": str(int(time.time())),
                "filename": make_ascii_safe(filename, 100)
            }
            
            # Add custom metadata if provided, ensuring ASCII safety
            if metadata:
                for key, value in metadata.items():
                    # Convert key to ASCII-safe format (S3 metadata keys must be ASCII)
                    safe_key = make_ascii_safe(key.replace('_', '-').lower(), 30)
                    safe_value = make_ascii_safe(str(value), 200)
                    file_metadata[safe_key] = safe_value
            
            logger.debug(f"S3 metadata prepared: {file_metadata}")
            
            # Upload and get presigned URL
            presigned_url = self.s3_service.upload_and_get_presigned_url(
                file_path=local_file_path,
                s3_key=s3_key,
                metadata=file_metadata,
                expiry_seconds=expiry_seconds
            )
            
            if presigned_url:
                logger.info(f"Successfully uploaded {filename} to S3 and generated presigned URL")
                return presigned_url, s3_key
            else:
                logger.error(f"Failed to upload {filename} to S3")
                return None, None
                
        except Exception as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            return None, None

    def generate_speech(
        self,
        text: str,
        voice: str = "af_heart",
        language_code: str = "a",
        speed: float = 1.0,
        split_pattern: str = r'\n+',
        user_id: Optional[int] = None,
        use_s3: bool = True,
        presigned_url_expiry: Optional[int] = None
    ) -> Dict:
        """
        Generate speech from text using Kokoro TTS.
        
        Args:
            text: Text to convert to speech
            voice: Voice type to use
            language_code: Language code (a, b, e, f, h, i, j, p, z)
            speed: Speech speed multiplier
            split_pattern: Pattern to split text into segments
            user_id: Optional user ID for file organization
            use_s3: Whether to upload to S3 and generate presigned URLs
            presigned_url_expiry: Presigned URL expiry in seconds
            
        Returns:
            Dictionary with generated audio file paths and metadata
        """
        start_time = time.time()
        
        try:
            # Get pipeline for language
            pipeline = self._get_pipeline(language_code)
            
            # Generate audio
            generator = pipeline(
                text,
                voice=voice,
                speed=speed,
                split_pattern=split_pattern
            )
            
            # Create unique directory for this generation
            timestamp = int(time.time() * 1000)
            session_id = f"{timestamp}_{user_id if user_id else 'anonymous'}"
            session_dir = os.path.join(self.audio_dir, session_id)
            os.makedirs(session_dir, exist_ok=True)
            
            # Determine storage settings
            use_s3_storage = use_s3 and self.s3_service and settings.s3_enabled
            expiry_seconds = presigned_url_expiry or settings.S3_PRESIGNED_URL_EXPIRY
            
            audio_files = []
            audio_segments = []
            presigned_urls_expire_at = None
            
            if use_s3_storage:
                presigned_urls_expire_at = time.time() + expiry_seconds
                logger.info(f"Using S3 storage with {expiry_seconds}s expiry")
            else:
                logger.info("Using local storage")
            
            # Process each audio segment
            for i, (graphemes, phonemes, audio) in enumerate(generator):
                # Save audio file locally first
                filename = f"segment_{i:03d}.wav"
                local_filepath = os.path.join(session_dir, filename)
                sf.write(local_filepath, audio, 24000)
                
                # Create local URL
                local_url = f"/static/audio/{session_id}/{filename}"
                
                # Initialize segment data
                segment = AudioSegment(
                    index=i,
                    graphemes=graphemes,
                    phonemes=phonemes,
                    filename=filename,
                    local_url=local_url
                )
                
                # Upload to S3 if enabled
                if use_s3_storage:
                    try:
                        presigned_url, s3_key = self._upload_to_s3_and_get_presigned_url(
                            local_file_path=local_filepath,
                            session_id=session_id,
                            filename=filename,
                            user_id=user_id,
                            expiry_seconds=expiry_seconds,
                            metadata={
                                "voice": voice,
                                "language_code": language_code,
                                "speed": str(speed),
                                "segment_index": str(i),
                                "graphemes": graphemes[:100] if graphemes else "unknown"  # Ensure safe truncation
                            }
                        )
                        
                        if presigned_url:
                            segment.presigned_url = presigned_url
                            segment.s3_key = s3_key
                            segment.expires_at = presigned_urls_expire_at
                            audio_files.append(presigned_url)
                            
                            # Optionally delete local file after successful S3 upload
                            if settings.DEBUG is False:  # Keep local files in debug mode
                                try:
                                    os.remove(local_filepath)
                                    logger.debug(f"Deleted local file after S3 upload: {local_filepath}")
                                except Exception as e:
                                    logger.warning(f"Could not delete local file: {e}")
                        else:
                            logger.warning(f"S3 upload failed for segment {i}, falling back to local URL")
                            audio_files.append(local_url)
                            
                    except Exception as s3_error:
                        logger.error(f"S3 upload error for segment {i}: {str(s3_error)}")
                        logger.info(f"Falling back to local storage for segment {i}")
                        audio_files.append(local_url)
                else:
                    audio_files.append(local_url)
                
                audio_segments.append(segment)
                logger.info(f"Generated segment {i}: {graphemes[:50]}...")
            
            processing_time = time.time() - start_time
            storage_type = "s3" if use_s3_storage else "local"
            
            result = {
                "session_id": session_id,
                "audio_files": audio_files,
                "audio_segments": [segment.dict() for segment in audio_segments],
                "total_segments": len(audio_files),
                "language_code": language_code,
                "voice": voice,
                "speed": speed,
                "processing_time": processing_time,
                "text_length": len(text),
                "storage_type": storage_type,
                "expires_at": presigned_urls_expire_at
            }
            
            logger.info(f"TTS generation completed: {len(audio_files)} segments in {processing_time:.2f}s using {storage_type} storage")
            return result
            
        except Exception as e:
            logger.error(f"Error in TTS generation: {str(e)}")
            raise e
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voices."""
        # This is a basic list - in production you might want to 
        # dynamically discover available voices
        return [
            "af_heart",
            "af_bella", 
            "af_sarah",
            "af_nicole",
            "am_adam",
            "am_michael",
            # Add more voices as needed
        ]
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get supported language codes and their descriptions."""
        return {
            "a": "American English 🇺🇸",
            "b": "British English 🇬🇧", 
            "e": "Spanish 🇪🇸",
            "f": "French 🇫🇷",
            "h": "Hindi 🇮🇳",
            "i": "Italian 🇮🇹",
            "j": "Japanese 🇯🇵",
            "p": "Brazilian Portuguese 🇧🇷",
            "z": "Mandarin Chinese 🇨🇳"
        }
    
    def cleanup_old_files(self, days_old: int = 7) -> int:
        """Clean up audio files older than specified days."""
        try:
            current_time = time.time()
            cleanup_count = 0
            
            if not os.path.exists(self.audio_dir):
                logger.warning(f"Audio directory not found: {self.audio_dir}")
                return 0
            
            for item in os.listdir(self.audio_dir):
                if item == '.gitkeep':  # Skip .gitkeep file
                    continue
                    
                item_path = os.path.join(self.audio_dir, item)
                if os.path.isdir(item_path):
                    # Check if directory is old
                    dir_time = os.path.getctime(item_path)
                    if (current_time - dir_time) > (days_old * 24 * 3600):
                        import shutil
                        try:
                            shutil.rmtree(item_path)
                            cleanup_count += 1
                            logger.info(f"Deleted old audio directory: {item_path}")
                        except Exception as e:
                            logger.error(f"Failed to delete directory {item_path}: {e}")
            
            logger.info(f"Cleaned up {cleanup_count} old audio directories")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return 0


# Singleton instance
_tts_service = None

def get_tts_service() -> TTSService:
    """Get singleton instance of TTS service."""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service 