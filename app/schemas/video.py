from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VideoBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_public: bool = True

class VideoCreate(VideoBase):
    pass

class VideoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None

class VideoInDB(VideoBase):
    id: int
    filename: str
    original_filename: str
    file_path: str
    thumbnail_path: Optional[str] = None
    file_size: int
    duration: Optional[int] = None
    resolution: Optional[str] = None
    format: Optional[str] = None
    is_processed: bool
    views_count: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class Video(VideoInDB):
    pass

class VideoResponse(VideoInDB):
    pass

class VideoList(BaseModel):
    videos: list[Video]
    total: int
    page: int
    per_page: int
    total_pages: int

class VideoUploadResponse(BaseModel):
    video_id: int
    message: str
    filename: str 