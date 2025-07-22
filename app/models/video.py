from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.database import Base

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    thumbnail_path = Column(String(500), nullable=True)
    file_size = Column(BigInteger, nullable=False)
    duration = Column(Integer, nullable=True)  # in seconds
    resolution = Column(String(20), nullable=True)  # e.g., "1920x1080"
    format = Column(String(10), nullable=True)  # e.g., "mp4"
    is_public = Column(Boolean, default=True)
    is_processed = Column(Boolean, default=False)
    views_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Foreign key
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="videos")

class VideoView(Base):
    __tablename__ = "video_views"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for anonymous views
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now()) 