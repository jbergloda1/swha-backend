from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from typing import Optional
import shutil
import tempfile
import os
import time
import httpx

from app.schemas.stt import STTResponse
from app.services.stt_service import STTService, get_stt_service
from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/transcribe", response_model=STTResponse)
async def transcribe_audio(
    file: Optional[UploadFile] = File(None),
    audio_url: Optional[str] = Form(None),
    stt_service: STTService = Depends(get_stt_service),
    current_user: User = Depends(get_current_user)
):
    """
    Transcribes an audio file to text using Whisper.

    This endpoint requires authentication. You must provide either a direct
    file upload or a URL to an audio file.

    - **file**: The audio file to transcribe (e.g., .mp3, .wav, .m4a).
    - **audio_url**: A URL to an audio file to transcribe.
    """
    start_time = time.time()
    tmp_path = None

    if not file and not audio_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either a file upload or an audio_url must be provided.",
        )

    if file and audio_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either a file upload or an audio_url, not both.",
        )

    try:
        # Create a temporary file to store the audio
        if file:
            suffix = os.path.splitext(file.filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                shutil.copyfileobj(file.file, tmp)
                tmp_path = tmp.name
        elif audio_url:
            async with httpx.AsyncClient() as client:
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as tmp:
                        tmp_path = tmp.name
                        async with client.stream("GET", audio_url, follow_redirects=True, timeout=60.0) as response:
                            response.raise_for_status()
                            async for chunk in response.aiter_bytes():
                                tmp.write(chunk)
                except httpx.RequestError as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to download audio from URL: {e}",
                    )

        if not tmp_path or not os.path.exists(tmp_path):
             raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create or access temporary audio file.",
            )

        # Perform transcription
        transcription_result = stt_service.transcribe(tmp_path)

        # Calculate processing time
        end_time = time.time()
        processing_time_ms = (end_time - start_time) * 1000

        # Format the response
        return STTResponse(
            text=transcription_result.get("text", ""),
            segments=transcription_result.get("segments", []),
            language=transcription_result.get("language", ""),
            processing_time_ms=processing_time_ms,
        )

    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Temporary audio file not found.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during transcription: {str(e)}",
        )
    finally:
        # Clean up the temporary file
        if file:
            file.file.close()
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path) 