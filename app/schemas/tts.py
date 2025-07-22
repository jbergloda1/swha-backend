from pydantic import BaseModel
from typing import Optional, Literal, List
from enum import Enum

class LanguageCode(str, Enum):
    AMERICAN_ENGLISH = "a"  # 🇺🇸 American English
    BRITISH_ENGLISH = "b"   # 🇬🇧 British English
    SPANISH = "e"           # 🇪🇸 Spanish es
    FRENCH = "f"            # 🇫🇷 French fr-fr
    HINDI = "h"             # 🇮🇳 Hindi hi
    ITALIAN = "i"           # 🇮🇹 Italian it
    JAPANESE = "j"          # 🇯🇵 Japanese (requires misaki[ja])
    PORTUGUESE = "p"        # 🇧🇷 Brazilian Portuguese pt-br
    CHINESE = "z"           # 🇨🇳 Mandarin Chinese (requires misaki[zh])

class AudioSegment(BaseModel):
    index: int
    graphemes: str  # Text content
    phonemes: str   # Phonetic representation
    filename: str
    local_url: Optional[str] = None      # Local static URL
    presigned_url: Optional[str] = None  # S3 presigned URL
    s3_key: Optional[str] = None         # S3 object key
    expires_at: Optional[float] = None   # Presigned URL expiry timestamp

class TTSRequest(BaseModel):
    text: str
    voice: str = "af_heart"  # Default voice
    language_code: LanguageCode = LanguageCode.AMERICAN_ENGLISH
    speed: float = 1.0
    split_pattern: str = r'\n+'
    use_s3: bool = True  # Use S3 storage by default
    presigned_url_expiry: Optional[int] = 3600  # 1 hour default

class TTSResponse(BaseModel):
    message: str
    audio_files: List[str]  # List of audio file URLs (presigned or local)
    audio_segments: List[AudioSegment]  # Detailed segment information
    total_segments: int
    language_code: str
    voice: str
    processing_time: float
    storage_type: str  # "s3" or "local"
    session_id: str
    expires_at: Optional[float] = None  # When presigned URLs expire 