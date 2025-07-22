import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.models.video import Video
from app.schemas.video import VideoUploadResponse
from app.api.dependencies import get_current_user
from app.core.config import settings
from app.services.video_service import VideoService

router = APIRouter()

@router.post("/video", response_model=VideoUploadResponse)
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(None),
    is_public: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a video file."""
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in settings.ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_VIDEO_EXTENSIONS)}"
        )
    
    # Check file size
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, "videos", unique_filename)
    
    # Save file
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    
    # Create video record
    video = Video(
        title=title,
        description=description,
        filename=unique_filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        format=file_extension,
        is_public=is_public,
        owner_id=current_user.id
    )
    
    db.add(video)
    db.commit()
    db.refresh(video)
    
    # Process video (extract metadata, create thumbnail)
    video_service = VideoService()
    await video_service.process_video(video, db)
    
    return VideoUploadResponse(
        video_id=video.id,
        message="Video uploaded successfully",
        filename=unique_filename
    )

@router.post("/videos", response_model=List[VideoUploadResponse])
async def upload_multiple_videos(
    files: List[UploadFile] = File(...),
    titles: List[str] = Form(...),
    descriptions: List[str] = Form(None),
    is_public: List[bool] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload multiple video files."""
    if len(files) != len(titles):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Number of files must match number of titles"
        )
    
    responses = []
    
    for i, file in enumerate(files):
        try:
            # Validate file type
            if not file.filename:
                continue
            
            file_extension = file.filename.split('.')[-1].lower()
            if file_extension not in settings.ALLOWED_VIDEO_EXTENSIONS:
                continue
            
            # Check file size
            content = await file.read()
            if len(content) > settings.MAX_FILE_SIZE:
                continue
            
            # Generate unique filename
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            file_path = os.path.join(settings.UPLOAD_DIR, "videos", unique_filename)
            
            # Save file
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            
            # Create video record
            video = Video(
                title=titles[i],
                description=descriptions[i] if descriptions and i < len(descriptions) else None,
                filename=unique_filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size=len(content),
                format=file_extension,
                is_public=is_public[i] if is_public and i < len(is_public) else True,
                owner_id=current_user.id
            )
            
            db.add(video)
            db.commit()
            db.refresh(video)
            
            # Process video asynchronously
            video_service = VideoService()
            await video_service.process_video(video, db)
            
            responses.append(VideoUploadResponse(
                video_id=video.id,
                message="Video uploaded successfully",
                filename=unique_filename
            ))
            
        except Exception as e:
            # Log error but continue with other files
            print(f"Error uploading file {file.filename}: {str(e)}")
            continue
    
    return responses

@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload an image file (for profile pictures, thumbnails, etc.)."""
    # Validate file type
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided"
        )
    
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}"
        )
    
    # Check file size (smaller limit for images)
    content = await file.read()
    max_image_size = 10 * 1024 * 1024  # 10MB
    if len(content) > max_image_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image file too large (max 10MB)"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, "images", unique_filename)
    
    # Save file
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as buffer:
        buffer.write(content)
    
    return {
        "message": "Image uploaded successfully",
        "filename": unique_filename,
        "url": f"/static/uploads/images/{unique_filename}"
    } 