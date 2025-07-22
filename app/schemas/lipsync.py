from pydantic import BaseModel, HttpUrl
from typing import Optional, Literal
from enum import Enum

class SyncMode(str, Enum):
    CUT_OFF = "cut_off"
    LOOP = "loop"
    FADE = "fade"

class LipsyncModel(str, Enum):
    LIPSYNC_1 = "lipsync-1"
    LIPSYNC_2 = "lipsync-2"

class LipsyncStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class LipsyncRequest(BaseModel):
    video_url: str  # URL to source video
    audio_url: str  # URL to audio file (from TTS or uploaded)
    api_key: str  # Sync.so API key
    model: LipsyncModel = LipsyncModel.LIPSYNC_2
    sync_mode: SyncMode = SyncMode.CUT_OFF
    output_filename: Optional[str] = None

class LipsyncResponse(BaseModel):
    message: str
    job_id: str
    status: LipsyncStatus
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    model: str
    sync_mode: str
    submitted_at: float

class LipsyncStatusResponse(BaseModel):
    job_id: str
    status: LipsyncStatus
    output_url: Optional[str] = None
    progress: Optional[float] = None
    error_message: Optional[str] = None
    created_at: Optional[float] = None
    completed_at: Optional[float] = None

class LipsyncJobInfo(BaseModel):
    job_id: str
    status: LipsyncStatus
    video_url: str
    audio_url: str
    model: str
    sync_mode: str
    output_url: Optional[str] = None
    submitted_at: float
    completed_at: Optional[float] = None
    processing_time: Optional[float] = None
    user_id: int 