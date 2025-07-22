from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.database import Base

class QAHistory(Base):
    __tablename__ = "qa_history"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    context = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    start_position = Column(Integer, nullable=False)
    end_position = Column(Integer, nullable=False)
    is_answerable = Column(Boolean, nullable=False)
    model_used = Column(String(100), default="deepset/roberta-base-squad2")
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Foreign key to user (optional, for tracking who asked)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id]) 