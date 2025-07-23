from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class Segment(BaseModel):
    id: int
    seek: int
    start: float
    end: float
    text: str
    tokens: List[int]
    temperature: float
    avg_logprob: float
    compression_ratio: float
    no_speech_prob: float

class STTResponse(BaseModel):
    text: str
    segments: List[Segment]
    language: str
    processing_time_ms: Optional[float] = None 