import os
import cv2
import ffmpeg
from PIL import Image
from sqlalchemy.orm import Session
from app.models.video import Video
from app.core.config import settings

class VideoService:
    """Service for video processing operations."""
    
    async def process_video(self, video: Video, db: Session):
        """Process video: extract metadata and create thumbnail."""
        try:
            # Extract video metadata
            metadata = self._extract_metadata(video.file_path)
            
            # Update video with metadata
            video.duration = metadata.get('duration')
            video.resolution = metadata.get('resolution')
            
            # Generate thumbnail
            thumbnail_path = await self._create_thumbnail(video)
            if thumbnail_path:
                video.thumbnail_path = thumbnail_path
            
            video.is_processed = True
            db.commit()
            
        except Exception as e:
            print(f"Error processing video {video.id}: {str(e)}")
            # Mark as processed even if failed to avoid reprocessing
            video.is_processed = True
            db.commit()
    
    def _extract_metadata(self, file_path: str) -> dict:
        """Extract video metadata using ffmpeg."""
        try:
            probe = ffmpeg.probe(file_path)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            
            if video_stream:
                duration = float(probe['format']['duration'])
                width = int(video_stream['width'])
                height = int(video_stream['height'])
                
                return {
                    'duration': int(duration),
                    'resolution': f"{width}x{height}"
                }
        except Exception as e:
            print(f"Error extracting metadata: {str(e)}")
        
        return {}
    
    async def _create_thumbnail(self, video: Video) -> str:
        """Create video thumbnail."""
        try:
            # Create thumbnails directory
            thumbnails_dir = os.path.join(settings.UPLOAD_DIR, "thumbnails")
            os.makedirs(thumbnails_dir, exist_ok=True)
            
            # Generate thumbnail filename
            thumbnail_filename = f"{os.path.splitext(video.filename)[0]}_thumb.jpg"
            thumbnail_path = os.path.join(thumbnails_dir, thumbnail_filename)
            
            # Extract frame at 10% of video duration or 5 seconds, whichever is smaller
            cap = cv2.VideoCapture(video.file_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            if fps > 0:
                duration = total_frames / fps
                seek_time = min(duration * 0.1, 5.0)  # 10% or 5 seconds
                frame_number = int(seek_time * fps)
                
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()
                
                if ret:
                    # Resize and save thumbnail
                    height, width = frame.shape[:2]
                    aspect_ratio = width / height
                    
                    # Standard thumbnail size
                    thumb_width = 320
                    thumb_height = int(thumb_width / aspect_ratio)
                    
                    resized_frame = cv2.resize(frame, (thumb_width, thumb_height))
                    cv2.imwrite(thumbnail_path, resized_frame)
                    
                    cap.release()
                    return thumbnail_path
            
            cap.release()
            
        except Exception as e:
            print(f"Error creating thumbnail: {str(e)}")
        
        return None
    
    def delete_video_files(self, video: Video):
        """Delete video file and associated files."""
        try:
            # Delete video file
            if os.path.exists(video.file_path):
                os.remove(video.file_path)
            
            # Delete thumbnail
            if video.thumbnail_path and os.path.exists(video.thumbnail_path):
                os.remove(video.thumbnail_path)
                
        except Exception as e:
            print(f"Error deleting video files: {str(e)}")
    
    def get_video_info(self, file_path: str) -> dict:
        """Get detailed video information."""
        try:
            probe = ffmpeg.probe(file_path)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
            
            info = {
                'format': probe['format']['format_name'],
                'duration': float(probe['format']['duration']),
                'size': int(probe['format']['size']),
                'bitrate': int(probe['format']['bit_rate']) if 'bit_rate' in probe['format'] else None
            }
            
            if video_stream:
                info.update({
                    'width': int(video_stream['width']),
                    'height': int(video_stream['height']),
                    'video_codec': video_stream['codec_name'],
                    'frame_rate': eval(video_stream['r_frame_rate']) if 'r_frame_rate' in video_stream else None
                })
            
            if audio_stream:
                info.update({
                    'audio_codec': audio_stream['codec_name'],
                    'channels': int(audio_stream['channels']) if 'channels' in audio_stream else None,
                    'sample_rate': int(audio_stream['sample_rate']) if 'sample_rate' in audio_stream else None
                })
            
            return info
            
        except Exception as e:
            print(f"Error getting video info: {str(e)}")
            return {} 