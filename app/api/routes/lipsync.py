from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from typing import List, Dict
from sqlalchemy.orm import Session

from app.schemas.lipsync import (
    LipsyncRequest, LipsyncResponse, LipsyncStatusResponse, 
    LipsyncJobInfo, LipsyncStatus, LipsyncModel, SyncMode
)
from app.services.lipsync_service import get_lipsync_service, LipsyncService
from app.api.dependencies import get_current_user
from app.models.user import User
from app.database.database import get_db

router = APIRouter()

def _safe_status_conversion(status_str: str) -> LipsyncStatus:
    """Safely convert status string to LipsyncStatus enum."""
    try:
        # Try direct conversion first
        return LipsyncStatus(status_str)
    except ValueError:
        # Map common variations
        status_mapping = {
            "PENDING": LipsyncStatus.PENDING,
            "PROCESSING": LipsyncStatus.PROCESSING,
            "COMPLETED": LipsyncStatus.COMPLETED,
            "FAILED": LipsyncStatus.FAILED,
            "TIMEOUT": LipsyncStatus.FAILED,  # Map timeout to failed
            "pending": LipsyncStatus.PENDING,
            "processing": LipsyncStatus.PROCESSING,
            "completed": LipsyncStatus.COMPLETED,
            "failed": LipsyncStatus.FAILED,
        }
        return status_mapping.get(status_str, LipsyncStatus.PENDING)

@router.post("/create", response_model=LipsyncResponse)
async def create_lipsync_job(
    lipsync_request: LipsyncRequest,
    lipsync_service: LipsyncService = Depends(get_lipsync_service),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new lipsync generation job.
    
    - **video_url**: URL to source video file
    - **audio_url**: URL to audio file (from TTS or uploaded)
    - **api_key**: Your Sync.so API key
    - **model**: Lipsync model (lipsync-1 or lipsync-2)
    - **sync_mode**: Synchronization mode (cut_off, loop, fade)
    - **output_filename**: Optional output filename
    """
    try:
        # Create lipsync job
        result = lipsync_service.create_lipsync_job(
            video_url=lipsync_request.video_url,
            audio_url=lipsync_request.audio_url,
            api_key=lipsync_request.api_key,
            model=lipsync_request.model.value,
            sync_mode=lipsync_request.sync_mode.value,
            output_filename=lipsync_request.output_filename,
            user_id=current_user.id
        )
        
        return LipsyncResponse(
            message="Lipsync job created successfully",
            job_id=result["job_id"],
            status=_safe_status_conversion(result["status"]),
            video_url=result["video_url"],
            audio_url=result["audio_url"],
            model=result["model"],
            sync_mode=result["sync_mode"],
            submitted_at=result["submitted_at"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating lipsync job: {str(e)}"
        )

@router.get("/status/{job_id}", response_model=LipsyncStatusResponse)
async def get_job_status(
    job_id: str,
    api_key: str,
    lipsync_service: LipsyncService = Depends(get_lipsync_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get status of a lipsync job.
    
    - **job_id**: The job ID to check
    - **api_key**: Your Sync.so API key
    """
    try:
        result = lipsync_service.get_job_status(job_id, api_key)
        
        return LipsyncStatusResponse(
            job_id=result["job_id"],
            status=_safe_status_conversion(result["status"]),
            output_url=result.get("output_url"),
            progress=result.get("progress"),
            error_message=result.get("error_message"),
            created_at=result.get("created_at"),
            completed_at=result.get("completed_at")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting job status: {str(e)}"
        )

@router.post("/wait/{job_id}", response_model=LipsyncStatusResponse)
async def wait_for_completion(
    job_id: str,
    api_key: str,
    timeout: int = 300,
    poll_interval: int = 10,
    lipsync_service: LipsyncService = Depends(get_lipsync_service),
    current_user: User = Depends(get_current_user)
):
    """
    Wait for a lipsync job to complete with polling.
    
    - **job_id**: The job ID to wait for
    - **api_key**: Your Sync.so API key
    - **timeout**: Maximum time to wait in seconds (default: 300)
    - **poll_interval**: Polling interval in seconds (default: 10)
    """
    try:
        result = lipsync_service.wait_for_completion(
            job_id=job_id,
            api_key=api_key,
            timeout=timeout,
            poll_interval=poll_interval
        )
        
        return LipsyncStatusResponse(
            job_id=result["job_id"],
            status=_safe_status_conversion(result["status"]),
            output_url=result.get("output_url"),
            progress=result.get("progress"),
            error_message=result.get("error_message"),
            created_at=result.get("created_at"),
            completed_at=result.get("completed_at")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error waiting for job completion: {str(e)}"
        )

@router.post("/create-from-tts")
async def create_lipsync_from_tts(
    video_url: str,
    tts_audio_url: str,  # Audio URL from TTS API response (presigned or local)
    api_key: str,
    model: LipsyncModel = LipsyncModel.LIPSYNC_2,
    sync_mode: SyncMode = SyncMode.CUT_OFF,
    lipsync_service: LipsyncService = Depends(get_lipsync_service),
    current_user: User = Depends(get_current_user)
):
    """
    Create lipsync job using audio from TTS API.
    This is a convenience endpoint for TTS + Lipsync workflow.
    
    - **video_url**: URL to source video
    - **tts_audio_url**: Audio URL from TTS API (presigned S3 URL or local static URL)
    - **api_key**: Your Sync.so API key
    - **model**: Lipsync model
    - **sync_mode**: Synchronization mode
    
    Note: This endpoint accepts both S3 presigned URLs and local static URLs from TTS API.
    """
    try:
        # The audio URL can be either a presigned S3 URL or local static URL
        # Sync.so should be able to access both types
        full_audio_url = tts_audio_url
        
        # If it's a relative local URL, convert to absolute
        if tts_audio_url.startswith('/static/'):
            # In production, you might want to get the base URL from config
            base_url = "http://localhost:8000"  # This should come from settings
            full_audio_url = f"{base_url}{tts_audio_url}"
        
        result = lipsync_service.create_lipsync_job(
            video_url=video_url,
            audio_url=full_audio_url,
            api_key=api_key,
            model=model.value,
            sync_mode=sync_mode.value,
            user_id=current_user.id
        )
        
        return {
            "message": "Lipsync job created from TTS audio",
            "job_id": result["job_id"],
            "status": result["status"],
            "video_url": video_url,
            "audio_url": full_audio_url,
            "audio_url_type": "presigned_s3" if "amazonaws.com" in full_audio_url else "local_static",
            "model": result["model"],
            "sync_mode": result["sync_mode"],
            "submitted_at": result["submitted_at"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating lipsync from TTS: {str(e)}"
        )

@router.get("/jobs/my")
async def get_my_jobs(
    lipsync_service: LipsyncService = Depends(get_lipsync_service),
    current_user: User = Depends(get_current_user)
):
    """Get all lipsync jobs for the current user."""
    try:
        jobs = lipsync_service.get_user_jobs(current_user.id)
        return {
            "jobs": [job.dict() for job in jobs],
            "total_count": len(jobs)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user jobs: {str(e)}"
        )

@router.get("/models")
async def get_supported_models(
    lipsync_service: LipsyncService = Depends(get_lipsync_service),
    current_user: User = Depends(get_current_user)
):
    """Get list of supported lipsync models."""
    try:
        models = lipsync_service.get_supported_models()
        return {
            "models": models,
            "total_count": len(models),
            "descriptions": {
                "lipsync-1": "Basic lipsync model",
                "lipsync-2": "Advanced lipsync model with better quality"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving models: {str(e)}"
        )

@router.get("/sync-modes")
async def get_sync_modes(
    lipsync_service: LipsyncService = Depends(get_lipsync_service),
    current_user: User = Depends(get_current_user)
):
    """Get list of supported synchronization modes."""
    try:
        sync_modes = lipsync_service.get_supported_sync_modes()
        return {
            "sync_modes": sync_modes,
            "total_count": len(sync_modes),
            "descriptions": {
                "cut_off": "Cut off audio/video at the end of the shorter one",
                "loop": "Loop the shorter content to match the longer one",
                "fade": "Fade out the longer content to match the shorter one"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving sync modes: {str(e)}"
        )

@router.post("/cleanup")
async def cleanup_old_jobs(
    hours_old: int = 24,
    lipsync_service: LipsyncService = Depends(get_lipsync_service),
    current_user: User = Depends(get_current_user)
):
    """
    Clean up completed jobs older than specified hours.
    Only accessible to authenticated users.
    """
    try:
        cleaned_count = lipsync_service.cleanup_completed_jobs(hours_old=hours_old)
        return {
            "message": f"Cleanup completed for jobs older than {hours_old} hours",
            "cleaned_jobs": cleaned_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during cleanup: {str(e)}"
        )

@router.get("/debug/status/{job_id}")
async def debug_job_status(
    job_id: str,
    api_key: str,
    lipsync_service: LipsyncService = Depends(get_lipsync_service),
    current_user: User = Depends(get_current_user)
):
    """
    Debug endpoint to get raw job status data from Sync.so API.
    This endpoint returns raw data without schema validation for debugging.
    """
    try:
        import logging
        logging.getLogger("app.services.lipsync_service").setLevel(logging.DEBUG)
        
        result = lipsync_service.get_job_status(job_id, api_key, update_cache=False)
        
        # Return raw result for debugging
        return {
            "message": "Raw status data for debugging",
            "job_id": job_id,
            "raw_result": result,
            "data_types": {
                "job_id": str(type(result.get("job_id"))),
                "status": str(type(result.get("status"))),
                "output_url": str(type(result.get("output_url"))),
                "progress": str(type(result.get("progress"))),
                "error_message": str(type(result.get("error_message"))),
                "created_at": str(type(result.get("created_at"))),
                "completed_at": str(type(result.get("completed_at")))
            }
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "error_type": str(type(e)),
            "job_id": job_id
        } 