from pydantic import BaseModel
from typing import Optional

class QARequest(BaseModel):
    question: str
    context: str
    
class QAResponse(BaseModel):
    question: str
    context: str
    answer: str
    confidence: float
    start_position: int
    end_position: int
    is_answerable: bool

class QABatchRequest(BaseModel):
    questions: list[str]
    context: str
    
class QABatchResponse(BaseModel):
    context: str
    results: list[QAResponse] 