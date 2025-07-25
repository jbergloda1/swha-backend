from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from typing import Optional
import httpx
import time

from app.schemas.captioning import CaptioningResponse
from app.services.captioning_service import CaptioningService, get_captioning_service
from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/generate", response_model=CaptioningResponse)
async def generate_image_caption(
    file: Optional[UploadFile] = File(None, description="Image file to upload."),
    image_url: Optional[str] = Form(None, description="URL of an image."),
    conditional_text: Optional[str] = Form(None, description="Optional text to guide the caption."),
    captioning_service: CaptioningService = Depends(get_captioning_service),
    current_user: User = Depends(get_current_user)
):
    """
    Generates a descriptive caption for a given image.

    Provide either an image file via upload (`file`) or a public URL (`image_url`).
    Optionally, provide `conditional_text` to guide the caption generation.
    """
    start_time = time.time()
    
    if not file and not image_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either an image file or an image_url must be provided.",
        )
        
    if file and image_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either an image file or an image_url, not both.",
        )
    
    image_bytes = None
    if file:
        image_bytes = await file.read()
    elif image_url:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(image_url, follow_redirects=True, timeout=30.0)
                response.raise_for_status()
                image_bytes = response.content
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to download image from URL: {e}",
            )

    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process the image.",
        )

    try:
        caption = captioning_service.generate_caption(
            image_bytes=image_bytes,
            conditional_text=conditional_text
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during caption generation: {str(e)}",
        )
        
    end_time = time.time()
    processing_time_ms = (end_time - start_time) * 1000

    return CaptioningResponse(
        caption=caption,
        conditional_text=conditional_text,
        processing_time_ms=processing_time_ms,
        model_name=captioning_service.model_name
    ) 