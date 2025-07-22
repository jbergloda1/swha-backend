import os
import aiofiles
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.database.database import get_db
from app.models.user import User
from app.models.video import Video, VideoView
from app.schemas.video import Video as VideoSchema, VideoUpdate, VideoList
from app.api.dependencies import get_current_user
from app.core.config import settings
from app.services.video_service import VideoService

router = APIRouter()

@router.get("/", response_model=VideoList)
async def get_videos(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get paginated list of videos."""
    query = db.query(Video)
    
    # Filter by public videos unless it's the owner or admin
    if not current_user or not current_user.is_superuser:
        if user_id and current_user and current_user.id == user_id:
            # Show all user's own videos
            query = query.filter(Video.owner_id == user_id)
        else:
            # Show only public videos
            query = query.filter(Video.is_public == True)
            if user_id:
                query = query.filter(Video.owner_id == user_id)
    elif user_id:
        query = query.filter(Video.owner_id == user_id)
    
    # Search functionality
    if search:
        query = query.filter(
            or_(
                Video.title.ilike(f"%{search}%"),
                Video.description.ilike(f"%{search}%")
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    videos = query.order_by(desc(Video.created_at)).offset((page - 1) * per_page).limit(per_page).all()
    
    total_pages = (total + per_page - 1) // per_page
    
    return VideoList(
        videos=videos,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )

@router.get("/{video_id}", response_model=VideoSchema)
async def get_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get video by ID."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Check access permissions
    if not video.is_public:
        if not current_user or (video.owner_id != current_user.id and not current_user.is_superuser):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return video

@router.put("/{video_id}", response_model=VideoSchema)
async def update_video(
    video_id: int,
    video_update: VideoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update video information."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Check ownership
    if video.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update video fields
    update_data = video_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(video, field, value)
    
    db.commit()
    db.refresh(video)
    
    return video

@router.delete("/{video_id}")
async def delete_video(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete video."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Check ownership
    if video.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Delete video file
    video_service = VideoService()
    video_service.delete_video_files(video)
    
    # Delete from database
    db.delete(video)
    db.commit()
    
    return {"message": "Video deleted successfully"}

@router.get("/{video_id}/stream")
async def stream_video(
    video_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Stream video content."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found"
        )
    
    # Check access permissions
    if not video.is_public:
        if not current_user or (video.owner_id != current_user.id and not current_user.is_superuser):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Record view
    video_view = VideoView(
        video_id=video_id,
        user_id=current_user.id if current_user else None,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(video_view)
    
    # Increment view count
    video.views_count += 1
    db.commit()
    
    # Check if file exists
    if not os.path.exists(video.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video file not found"
        )
    
    # Get range header for partial content support
    range_header = request.headers.get("range")
    
    if range_header:
        # Handle range requests for video streaming
        return await _stream_video_range(video.file_path, range_header)
    else:
        # Stream entire video
        return await _stream_video_full(video.file_path)

async def _stream_video_range(file_path: str, range_header: str):
    """Stream video with range support for seeking."""
    start, end = _parse_range_header(range_header, os.path.getsize(file_path))
    
    async def generate():
        async with aiofiles.open(file_path, 'rb') as file:
            await file.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                chunk_size = min(settings.CHUNK_SIZE, remaining)
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk
    
    headers = {
        'Content-Range': f'bytes {start}-{end}/{os.path.getsize(file_path)}',
        'Accept-Ranges': 'bytes',
        'Content-Length': str(end - start + 1),
        'Content-Type': 'video/mp4',
    }
    
    return StreamingResponse(
        generate(),
        status_code=206,
        headers=headers
    )

async def _stream_video_full(file_path: str):
    """Stream entire video file."""
    async def generate():
        async with aiofiles.open(file_path, 'rb') as file:
            while chunk := await file.read(settings.CHUNK_SIZE):
                yield chunk
    
    return StreamingResponse(
        generate(),
        media_type='video/mp4',
        headers={'Content-Length': str(os.path.getsize(file_path))}
    )

def _parse_range_header(range_header: str, file_size: int):
    """Parse HTTP Range header."""
    range_match = range_header.replace('bytes=', '').split('-')
    start = int(range_match[0]) if range_match[0] else 0
    end = int(range_match[1]) if range_match[1] else file_size - 1
    return start, end 