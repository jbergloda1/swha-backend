import torch
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from sqlalchemy.orm import Session

from app.schemas.qa import QARequest, QAResponse, QABatchRequest, QABatchResponse
from app.services.qa_service import get_qa_service, QAService
from app.api.dependencies import get_current_user
from app.models.user import User
from app.database.database import get_db

router = APIRouter()

@router.post("/answer", response_model=QAResponse)
async def answer_question(
    qa_request: QARequest,
    qa_service: QAService = Depends(get_qa_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Answer a single question based on the provided context."""
    try:
        result = qa_service.answer_question(
            question=qa_request.question,
            context=qa_request.context,
            db=db,
            user_id=current_user.id,
            save_history=True
        )
        
        return QAResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing question: {str(e)}"
        )

@router.post("/answer-batch", response_model=QABatchResponse)
async def answer_multiple_questions(
    qa_batch_request: QABatchRequest,
    qa_service: QAService = Depends(get_qa_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Answer multiple questions based on the same context."""
    try:
        results = qa_service.answer_multiple_questions(
            questions=qa_batch_request.questions,
            context=qa_batch_request.context,
            db=db,
            user_id=current_user.id,
            save_history=True
        )
        
        qa_responses = [QAResponse(**result) for result in results]
        
        return QABatchResponse(
            context=qa_batch_request.context,
            results=qa_responses
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing batch questions: {str(e)}"
        )

@router.post("/answer-detailed")
async def answer_question_detailed(
    qa_request: QARequest,
    qa_service: QAService = Depends(get_qa_service),
    current_user: User = Depends(get_current_user)
):
    """Answer a question with detailed token-level information."""
    try:
        result = qa_service.get_detailed_answer(
            question=qa_request.question,
            context=qa_request.context
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing detailed question: {str(e)}"
        )

@router.get("/stats")
async def get_qa_statistics(
    qa_service: QAService = Depends(get_qa_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    user_stats: bool = True
):
    """Get QA usage statistics for the current user."""
    try:
        user_id = current_user.id if user_stats else None
        stats = qa_service.get_qa_stats(db=db, user_id=user_id)
        
        return {
            "user_id": current_user.id if user_stats else None,
            "stats": stats,
            "scope": "user" if user_stats else "global"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting QA statistics: {str(e)}"
        )

@router.get("/history")
async def get_qa_history(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get QA history for the current user."""
    try:
        from app.models.qa import QAHistory
        
        history = db.query(QAHistory).filter(
            QAHistory.user_id == current_user.id
        ).order_by(QAHistory.created_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "history": [
                {
                    "id": h.id,
                    "question": h.question,
                    "context": h.context[:200] + "..." if len(h.context) > 200 else h.context,
                    "answer": h.answer,
                    "confidence": h.confidence,
                    "is_answerable": h.is_answerable,
                    "processing_time_ms": h.processing_time_ms,
                    "created_at": h.created_at
                }
                for h in history
            ],
            "total": db.query(QAHistory).filter(QAHistory.user_id == current_user.id).count()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting QA history: {str(e)}"
        )

@router.get("/model-info")
async def get_model_info(
    qa_service: QAService = Depends(get_qa_service),
    current_user: User = Depends(get_current_user)
):
    """Get information about the loaded QA model."""
    return {
        "model_name": qa_service.model_name,
        "model_type": "RoBERTa-base fine-tuned on SQuAD 2.0",
        "description": "Extractive Question Answering model that can handle both answerable and unanswerable questions",
        "capabilities": [
            "Extractive question answering",
            "Handles unanswerable questions",
            "Returns confidence scores",
            "Provides answer positions in context",
            "GPU acceleration support",
            "History tracking and analytics"
        ],
        "input_format": {
            "question": "The question to be answered",
            "context": "The context/passage containing the answer"
        },
        "output_format": {
            "answer": "Extracted answer from context",
            "confidence": "Confidence score (0-1)",
            "start_position": "Start character position in context",
            "end_position": "End character position in context",
            "is_answerable": "Whether the question is answerable",
            "processing_time_ms": "Processing time in milliseconds"
        },
        "hardware": {
            "gpu_available": torch.cuda.is_available(),
            "device": "cuda" if torch.cuda.is_available() else "cpu"
        }
    }

# Public endpoint for testing (no auth required)
@router.post("/demo", response_model=QAResponse)
async def demo_question_answering(qa_request: QARequest):
    """Demo endpoint for testing QA functionality without authentication."""
    try:
        qa_service = get_qa_service()
        result = qa_service.answer_question(
            question=qa_request.question,
            context=qa_request.context,
            save_history=False  # Don't save demo requests
        )
        
        return QAResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing demo question: {str(e)}"
        ) 