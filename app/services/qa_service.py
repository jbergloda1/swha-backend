import torch
import time
from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import logging

from app.models.qa import QAHistory

logger = logging.getLogger(__name__)

class QAService:
    """Service for Question Answering using RoBERTa model."""
    
    def __init__(self):
        self.model_name = "deepset/roberta-base-squad2"
        self.pipeline = None
        self.tokenizer = None
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the RoBERTa question answering model."""
        try:
            logger.info(f"Loading QA model: {self.model_name}")
            
            # Load using pipeline for easier usage
            self.pipeline = pipeline(
                'question-answering',
                model=self.model_name,
                tokenizer=self.model_name,
                device=0 if torch.cuda.is_available() else -1  # Use GPU if available
            )
            
            # Also load tokenizer and model separately for more control
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForQuestionAnswering.from_pretrained(self.model_name)
            
            logger.info("QA model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading QA model: {str(e)}")
            raise e
    
    def answer_question(
        self, 
        question: str, 
        context: str, 
        db: Optional[Session] = None, 
        user_id: Optional[int] = None,
        save_history: bool = True
    ) -> Dict:
        """Answer a single question based on the given context."""
        start_time = time.time()
        
        try:
            if not self.pipeline:
                raise ValueError("QA model not loaded")
            
            # Prepare input
            qa_input = {
                'question': question,
                'context': context
            }
            
            # Get prediction
            result = self.pipeline(qa_input)
            
            processing_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds
            
            # Determine if the question is answerable
            # RoBERTa SQUAD2 returns empty string for unanswerable questions
            is_answerable = result['answer'].strip() != '' and result['score'] > 0.1
            
            response = {
                'question': question,
                'context': context,
                'answer': result['answer'],
                'confidence': result['score'],
                'start_position': result['start'],
                'end_position': result['end'],
                'is_answerable': is_answerable,
                'processing_time_ms': processing_time
            }
            
            # Save to database if requested and db session provided
            if save_history and db:
                try:
                    qa_history = QAHistory(
                        question=question,
                        context=context,
                        answer=result['answer'],
                        confidence=result['score'],
                        start_position=result['start'],
                        end_position=result['end'],
                        is_answerable=is_answerable,
                        model_used=self.model_name,
                        processing_time_ms=processing_time,
                        user_id=user_id
                    )
                    db.add(qa_history)
                    db.commit()
                    logger.info(f"QA history saved for user {user_id}")
                except Exception as e:
                    logger.error(f"Error saving QA history: {str(e)}")
                    # Don't fail the request if history saving fails
                    pass
            
            return response
            
        except Exception as e:
            logger.error(f"Error in question answering: {str(e)}")
            raise e
    
    def answer_multiple_questions(
        self, 
        questions: List[str], 
        context: str,
        db: Optional[Session] = None,
        user_id: Optional[int] = None,
        save_history: bool = True
    ) -> List[Dict]:
        """Answer multiple questions based on the same context."""
        try:
            results = []
            
            for question in questions:
                result = self.answer_question(
                    question=question, 
                    context=context,
                    db=db,
                    user_id=user_id,
                    save_history=save_history
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch question answering: {str(e)}")
            raise e
    
    def get_detailed_answer(self, question: str, context: str) -> Dict:
        """Get detailed answer with token-level information."""
        start_time = time.time()
        
        try:
            if not self.tokenizer or not self.model:
                raise ValueError("QA model components not loaded")
            
            # Tokenize input
            inputs = self.tokenizer(
                question, 
                context, 
                add_special_tokens=True,
                return_tensors="pt",
                max_length=512,
                truncation=True,
                return_offsets_mapping=True
            )
            
            # Get model outputs
            with torch.no_grad():
                outputs = self.model(**{k: v for k, v in inputs.items() if k != 'offset_mapping'})
            
            # Get start and end scores
            start_scores = outputs.start_logits
            end_scores = outputs.end_logits
            
            # Get best start and end positions
            start_position = torch.argmax(start_scores)
            end_position = torch.argmax(end_scores)
            
            # Calculate confidence score
            start_prob = torch.softmax(start_scores, dim=-1)[0][start_position].item()
            end_prob = torch.softmax(end_scores, dim=-1)[0][end_position].item()
            confidence = (start_prob + end_prob) / 2
            
            # Extract answer tokens
            input_ids = inputs['input_ids'][0]
            answer_tokens = input_ids[start_position:end_position + 1]
            answer = self.tokenizer.decode(answer_tokens, skip_special_tokens=True)
            
            # Get character-level positions in original context
            offset_mapping = inputs['offset_mapping'][0]
            start_char = offset_mapping[start_position][0].item()
            end_char = offset_mapping[end_position][1].item()
            
            is_answerable = answer.strip() != '' and confidence > 0.1
            processing_time = int((time.time() - start_time) * 1000)
            
            return {
                'question': question,
                'context': context,
                'answer': answer,
                'confidence': confidence,
                'start_position': start_char,
                'end_position': end_char,
                'is_answerable': is_answerable,
                'start_token_position': start_position.item(),
                'end_token_position': end_position.item(),
                'start_probability': start_prob,
                'end_probability': end_prob,
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Error in detailed question answering: {str(e)}")
            raise e

    def get_qa_stats(self, db: Session, user_id: Optional[int] = None) -> Dict:
        """Get QA usage statistics."""
        try:
            query = db.query(QAHistory)
            
            if user_id:
                query = query.filter(QAHistory.user_id == user_id)
            
            total_questions = query.count()
            answerable_questions = query.filter(QAHistory.is_answerable == True).count()
            avg_confidence = query.filter(QAHistory.is_answerable == True).with_entities(
                db.func.avg(QAHistory.confidence)
            ).scalar() or 0
            avg_processing_time = query.with_entities(
                db.func.avg(QAHistory.processing_time_ms)
            ).scalar() or 0
            
            return {
                'total_questions': total_questions,
                'answerable_questions': answerable_questions,
                'unanswerable_questions': total_questions - answerable_questions,
                'average_confidence': round(avg_confidence, 3),
                'average_processing_time_ms': round(avg_processing_time, 2),
                'answer_rate': round(answerable_questions / total_questions * 100, 1) if total_questions > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting QA stats: {str(e)}")
            raise e

# Global QA service instance
qa_service = None

def get_qa_service() -> QAService:
    """Get or create QA service instance."""
    global qa_service
    if qa_service is None:
        qa_service = QAService()
    return qa_service 