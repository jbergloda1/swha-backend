import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
from sync import Sync
from sync.common import Audio, GenerationOptions, Video
from sync.core.api_error import ApiError

from app.schemas.lipsync import LipsyncStatus, LipsyncJobInfo

logger = logging.getLogger(__name__)

class LipsyncService:
    """Service for Lip Sync using Sync.so API."""
    
    def __init__(self):
        self.base_url = "https://api.sync.so"
        self.active_jobs: Dict[str, LipsyncJobInfo] = {}  # In-memory job tracking
        
    def _get_client(self, api_key: str):
        """Get Sync.so client with API key."""
        return Sync(
            base_url=self.base_url,
            api_key=api_key
        ).generations
    
    def _convert_datetime_to_timestamp(self, dt_value):
        """Convert datetime object to timestamp, return None if not datetime."""
        if dt_value is None:
            return None
        if isinstance(dt_value, datetime):
            return dt_value.timestamp()
        # If it's already a number, return as is
        if isinstance(dt_value, (int, float)):
            return float(dt_value)
        return None

    def create_lipsync_job(
        self,
        video_url: str,
        audio_url: str,
        api_key: str,
        model: str = "lipsync-2",
        sync_mode: str = "cut_off",
        output_filename: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict:
        """
        Create a new lipsync generation job.
        
        Args:
            video_url: URL to source video
            audio_url: URL to audio file  
            api_key: Sync.so API key
            model: Lipsync model to use
            sync_mode: Synchronization mode
            output_filename: Optional output filename
            user_id: User ID for tracking
            
        Returns:
            Dictionary with job information
        """
        start_time = time.time()
        
        try:
            logger.info(f"Creating lipsync job for user {user_id}")
            logger.info(f"Video URL: {video_url}")
            logger.info(f"Audio URL: {audio_url}")
            
            client = self._get_client(api_key)
            
            # Prepare generation options
            options = GenerationOptions(sync_mode=sync_mode)
            
            # Create generation request
            response = client.create(
                input=[Video(url=video_url), Audio(url=audio_url)],
                model=model,
                options=options
            )
            
            job_id = response.id
            
            # Store job info for tracking
            job_info = LipsyncJobInfo(
                job_id=job_id,
                status=LipsyncStatus.PENDING,
                video_url=video_url,
                audio_url=audio_url,
                model=model,
                sync_mode=sync_mode,
                submitted_at=start_time,
                user_id=user_id or 0
            )
            
            self.active_jobs[job_id] = job_info
            
            logger.info(f"Lipsync job created successfully: {job_id}")
            
            return {
                "job_id": job_id,
                "status": LipsyncStatus.PENDING.value,
                "video_url": video_url,
                "audio_url": audio_url,
                "model": model,
                "sync_mode": sync_mode,
                "submitted_at": start_time,
                "api_key_provided": bool(api_key)
            }
            
        except ApiError as e:
            logger.error(f"Sync.so API error: Status {e.status_code}, Body: {e.body}")
            raise Exception(f"Sync.so API error: {e.body}")
        except Exception as e:
            logger.error(f"Error creating lipsync job: {str(e)}")
            raise e
    
    def get_job_status(
        self,
        job_id: str,
        api_key: str,
        update_cache: bool = True
    ) -> Dict:
        """
        Get status of a lipsync job.
        
        Args:
            job_id: Job ID to check
            api_key: Sync.so API key
            update_cache: Whether to update local cache
            
        Returns:
            Dictionary with job status information
        """
        try:
            client = self._get_client(api_key)
            generation = client.get(job_id)
            
            current_time = time.time()
            
            # Debug logging
            logger.debug(f"Raw generation object for job {job_id}:")
            logger.debug(f"  status: {generation.status} (type: {type(generation.status)})")
            logger.debug(f"  created_at: {getattr(generation, 'created_at', None)} (type: {type(getattr(generation, 'created_at', None))})")
            logger.debug(f"  completed_at: {getattr(generation, 'completed_at', None)} (type: {type(getattr(generation, 'completed_at', None))})")
            logger.debug(f"  output_url: {getattr(generation, 'output_url', None)}")
            logger.debug(f"  progress: {getattr(generation, 'progress', None)}")
            
            # Convert datetime objects to timestamps
            created_at = self._convert_datetime_to_timestamp(getattr(generation, 'created_at', None))
            completed_at = self._convert_datetime_to_timestamp(getattr(generation, 'completed_at', None))
            
            logger.debug(f"Converted timestamps - created_at: {created_at}, completed_at: {completed_at}")
            
            result = {
                "job_id": job_id,
                "status": generation.status,
                "output_url": generation.output_url if hasattr(generation, 'output_url') else None,
                "progress": getattr(generation, 'progress', None),
                "error_message": getattr(generation, 'error_message', None),
                "created_at": created_at,
                "completed_at": completed_at
            }
            
            # Update local cache if requested
            if update_cache and job_id in self.active_jobs:
                job_info = self.active_jobs[job_id]
                
                # Safely convert status
                try:
                    job_info.status = LipsyncStatus(generation.status)
                except ValueError:
                    # Default to PENDING if status is unknown
                    logger.warning(f"Unknown status '{generation.status}' for job {job_id}, defaulting to PENDING")
                    job_info.status = LipsyncStatus.PENDING
                
                if generation.status == 'COMPLETED':
                    job_info.output_url = generation.output_url if hasattr(generation, 'output_url') else None
                    job_info.completed_at = completed_at or current_time
                    job_info.processing_time = current_time - job_info.submitted_at
                    
                elif generation.status == 'FAILED':
                    job_info.completed_at = completed_at or current_time
            
            logger.info(f"Job {job_id} status: {generation.status}")
            logger.debug(f"Returning result: {result}")
            return result
            
        except ApiError as e:
            logger.error(f"Error getting job status: {e.status_code} - {e.body}")
            raise Exception(f"Failed to get job status: {e.body}")
        except Exception as e:
            logger.error(f"Error getting job status: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Job ID: {job_id}")
            raise e
    
    def wait_for_completion(
        self,
        job_id: str,
        api_key: str,
        timeout: int = 300,  # 5 minutes default timeout
        poll_interval: int = 10
    ) -> Dict:
        """
        Wait for a job to complete with polling.
        
        Args:
            job_id: Job ID to wait for
            api_key: Sync.so API key
            timeout: Maximum time to wait in seconds
            poll_interval: Polling interval in seconds
            
        Returns:
            Final job status
        """
        start_time = time.time()
        
        try:
            while (time.time() - start_time) < timeout:
                status_info = self.get_job_status(job_id, api_key)
                status = status_info["status"]
                
                if status in ['COMPLETED', 'FAILED']:
                    logger.info(f"Job {job_id} finished with status: {status}")
                    return status_info
                
                logger.info(f"Job {job_id} still processing, status: {status}")
                time.sleep(poll_interval)
            
            # Timeout reached
            logger.warning(f"Job {job_id} timed out after {timeout} seconds")
            return {
                "job_id": job_id,
                "status": "TIMEOUT",
                "error_message": f"Job timed out after {timeout} seconds"
            }
            
        except Exception as e:
            logger.error(f"Error waiting for job completion: {str(e)}")
            raise e
    
    def get_user_jobs(self, user_id: int) -> List[LipsyncJobInfo]:
        """Get all jobs for a specific user."""
        user_jobs = [
            job for job in self.active_jobs.values() 
            if job.user_id == user_id
        ]
        return user_jobs
    
    def get_all_jobs(self) -> List[LipsyncJobInfo]:
        """Get all active jobs."""
        return list(self.active_jobs.values())
    
    def cleanup_completed_jobs(self, hours_old: int = 24):
        """Remove completed jobs older than specified hours."""
        current_time = time.time()
        to_remove = []
        
        for job_id, job_info in self.active_jobs.items():
            if (job_info.status in [LipsyncStatus.COMPLETED, LipsyncStatus.FAILED] and 
                job_info.completed_at and 
                (current_time - job_info.completed_at) > (hours_old * 3600)):
                to_remove.append(job_id)
        
        for job_id in to_remove:
            del self.active_jobs[job_id]
            
        logger.info(f"Cleaned up {len(to_remove)} old lipsync jobs")
        return len(to_remove)
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported lipsync models."""
        return ["lipsync-1", "lipsync-2"]
    
    def get_supported_sync_modes(self) -> List[str]:
        """Get list of supported sync modes."""
        return ["cut_off", "loop", "fade"]


# Singleton instance
_lipsync_service = None

def get_lipsync_service() -> LipsyncService:
    """Get singleton instance of Lipsync service."""
    global _lipsync_service
    if _lipsync_service is None:
        _lipsync_service = LipsyncService()
    return _lipsync_service 