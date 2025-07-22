from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Dict
from sqlalchemy.orm import Session

from app.schemas.tts import TTSRequest, TTSResponse, LanguageCode
from app.services.tts_service import get_tts_service, TTSService
from app.api.dependencies import get_current_user
from app.models.user import User
from app.database.database import get_db
from app.core.config import settings

router = APIRouter()

@router.post("/generate", response_model=TTSResponse)
async def generate_speech(
    tts_request: TTSRequest,
    tts_service: TTSService = Depends(get_tts_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate speech from text using Kokoro TTS.
    
    - **text**: Text to convert to speech
    - **voice**: Voice type (default: af_heart)
    - **language_code**: Language code (a=American English, b=British English, etc.)
    - **speed**: Speech speed multiplier (default: 1.0)
    - **split_pattern**: Pattern to split text into segments (default: line breaks)
    - **use_s3**: Whether to upload to S3 and generate presigned URLs (default: True)
    - **presigned_url_expiry**: Presigned URL expiry in seconds (default: 3600)
    """
    try:
        # Generate speech using TTS service
        result = tts_service.generate_speech(
            text=tts_request.text,
            voice=tts_request.voice,
            language_code=tts_request.language_code.value,
            speed=tts_request.speed,
            split_pattern=tts_request.split_pattern,
            user_id=current_user.id,
            use_s3=tts_request.use_s3,
            presigned_url_expiry=tts_request.presigned_url_expiry
        )
        
        return TTSResponse(
            message="Speech generated successfully",
            audio_files=result["audio_files"],
            audio_segments=result["audio_segments"],
            total_segments=result["total_segments"],
            language_code=result["language_code"],
            voice=result["voice"],
            processing_time=result["processing_time"],
            storage_type=result["storage_type"],
            session_id=result["session_id"],
            expires_at=result.get("expires_at")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating speech: {str(e)}"
        )

@router.get("/voices")
async def get_available_voices(
    tts_service: TTSService = Depends(get_tts_service),
    current_user: User = Depends(get_current_user)
):
    """Get list of available voices for TTS."""
    try:
        voices = tts_service.get_available_voices()
        return {
            "voices": voices,
            "total_count": len(voices)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving voices: {str(e)}"
        )

@router.get("/languages")
async def get_supported_languages(
    tts_service: TTSService = Depends(get_tts_service),
    current_user: User = Depends(get_current_user)
):
    """Get list of supported languages for TTS."""
    try:
        languages = tts_service.get_supported_languages()
        return {
            "languages": languages,
            "total_count": len(languages)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving languages: {str(e)}"
        )

@router.post("/generate-simple")
async def generate_speech_simple(
    text: str,
    voice: str = "af_heart",
    language_code: LanguageCode = LanguageCode.AMERICAN_ENGLISH,
    use_s3: bool = True,
    presigned_url_expiry: int = 3600,
    tts_service: TTSService = Depends(get_tts_service),
    current_user: User = Depends(get_current_user)
):
    """
    Simple endpoint to generate speech with minimal parameters.
    Useful for quick testing or basic integrations.
    
    - **text**: Text to convert to speech
    - **voice**: Voice type (default: af_heart)
    - **language_code**: Language code (default: American English)
    - **use_s3**: Whether to upload to S3 (default: True)
    - **presigned_url_expiry**: URL expiry in seconds (default: 3600)
    """
    try:
        result = tts_service.generate_speech(
            text=text,
            voice=voice,
            language_code=language_code.value,
            user_id=current_user.id,
            use_s3=use_s3,
            presigned_url_expiry=presigned_url_expiry
        )
        
        return {
            "message": "Speech generated successfully",
            "audio_files": result["audio_files"],
            "audio_segments": result["audio_segments"],
            "first_audio_url": result["audio_files"][0] if result["audio_files"] else None,
            "total_segments": result["total_segments"],
            "processing_time": result["processing_time"],
            "storage_type": result["storage_type"],
            "session_id": result["session_id"],
            "expires_at": result.get("expires_at")
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating speech: {str(e)}"
        )

@router.get("/s3-info")
async def get_s3_info(
    current_user: User = Depends(get_current_user)
):
    """Get S3 configuration information."""
    return {
        "s3_enabled": settings.s3_enabled,
        "bucket_name": settings.S3_BUCKET_NAME if settings.s3_enabled else None,
        "region": settings.AWS_REGION if settings.s3_enabled else None,
        "default_expiry": settings.S3_PRESIGNED_URL_EXPIRY,
        "use_s3_storage": settings.USE_S3_STORAGE
    }

@router.post("/cleanup")
async def cleanup_old_audio_files(
    days_old: int = 7,
    cleanup_s3: bool = True,
    tts_service: TTSService = Depends(get_tts_service),
    current_user: User = Depends(get_current_user)
):
    """
    Clean up audio files older than specified days.
    Only accessible to authenticated users.
    
    - **days_old**: Delete files older than this many days (default: 7)
    - **cleanup_s3**: Also cleanup S3 files if S3 is enabled (default: True)
    """
    try:
        # Cleanup local files
        local_cleaned = tts_service.cleanup_old_files(days_old=days_old)
        
        result = {
            "message": f"Cleanup completed for files older than {days_old} days",
            "local_files_cleaned": local_cleaned,
            "s3_files_cleaned": 0
        }
        
        # Cleanup S3 files if enabled and requested
        if cleanup_s3 and settings.s3_enabled and tts_service.s3_service:
            try:
                s3_cleaned = tts_service.s3_service.cleanup_old_files(
                    prefix="audio/",
                    days_old=days_old
                )
                result["s3_files_cleaned"] = s3_cleaned
                result["message"] += f" (Local: {local_cleaned}, S3: {s3_cleaned})"
            except Exception as e:
                result["s3_cleanup_error"] = str(e)
                
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during cleanup: {str(e)}"
        ) 