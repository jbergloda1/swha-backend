from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form, WebSocket, WebSocketDisconnect
from typing import Optional, List
import shutil
import tempfile
import os
import time
import httpx
import logging
import asyncio

from app.schemas.stt import STTResponse
from app.services.stt_service import STTService, get_stt_service
from app.api.dependencies import get_current_user, get_current_user_ws
from app.models.user import User

logger = logging.getLogger(__name__)

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

@router.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    # Debug flag
    DEBUG_MODE = True
    
    # Manual authentication without dependency
    query_params = dict(websocket.query_params)
    token = query_params.get("token")
    
    if DEBUG_MODE:
        logger.info(f"🔍 DEBUG: WebSocket connection attempt with token: {token[:20] if token else 'None'}...")
    
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    
    try:
        # Verify token manually
        from app.core.security import verify_token
        from app.database.database import get_db
        payload = verify_token(token)
        user_id = payload.get("sub")
        
        # Get user from database
        db = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            await websocket.close(code=4003, reason="Invalid user")
            return
            
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        await websocket.close(code=4003, reason="Authentication failed")
        return
    
    # Accept connection after successful authentication
    await websocket.accept()
    logger.info(f"🔌 Real-time STT WebSocket connected for user: {user.email}")
    
    # Send initial message to confirm connection
    await websocket.send_json({
        "type": "connected", 
        "message": "Real-time STT ready",
        "mode": "continuous"
    })
    
    # Real-time processing variables
    audio_buffer = bytearray()
    stt_service = STTService()
    last_process_time = time.time()
    process_interval = 1.0  # Process every 1 second (reduced from 2.0)
    min_chunk_size = 4096   # Minimum buffer size to process (4KB, reduced from 8KB)
    silence_threshold = 5.0  # Reset buffer after 5 seconds of no new data
    last_chunk_time = time.time()
    transcription_history = []
    
    if DEBUG_MODE:
        logger.info(f"🔧 DEBUG: Variables initialized - interval: {process_interval}s")
    
    async def process_audio_buffer():
        """Process current audio buffer and return transcription"""
        logger.info(f"🎵 DEBUG: process_audio_buffer called with {len(audio_buffer)} bytes")
        
        if len(audio_buffer) < min_chunk_size:
            logger.info(f"⚠️ DEBUG: Buffer too small ({len(audio_buffer)} < {min_chunk_size}), skipping processing")
            return None
            
        try:
            logger.info(f"🎵 Processing {len(audio_buffer)} bytes for real-time transcription")
            start_time = time.time()
            
            # Process current buffer
            logger.info("📞 DEBUG: Calling stt_service.transcribe_stream...")
            result = stt_service.transcribe_stream(bytes(audio_buffer))
            processing_time = (time.time() - start_time) * 1000
            logger.info(f"✅ DEBUG: Transcription completed in {processing_time:.2f}ms")
            logger.info(f"🔍 DEBUG: Raw result: {result}")
            
            # Always return something for testing, even if no speech detected
            transcription = {
                "type": "partial_transcription",
                "text": result.get("text", "").strip(),
                "language": result.get("language", "unknown"),
                "processing_time_ms": processing_time,
                "buffer_size": len(audio_buffer),
                "timestamp": time.time()
            }
            
            # If no text detected, still return result for debugging
            if not transcription["text"]:
                transcription["debug_info"] = "No speech detected in audio buffer"
                logger.info("🔇 DEBUG: No speech detected, but returning result for debugging")
            else:
                logger.info(f"📝 DEBUG: Speech detected: '{transcription['text'][:50]}...'")
            
            # Keep history for context
            transcription_history.append(transcription)
            if len(transcription_history) > 10:  # Keep last 10 results
                transcription_history.pop(0)
            
            return transcription
                
        except Exception as e:
            logger.error(f"❌ Real-time transcription error: {e}")
            import traceback
            logger.error(f"🔍 Full traceback: {traceback.format_exc()}")
            return {"type": "error", "message": f"Transcription failed: {str(e)}"}
        
        return None
    
    try:
        message_count = 0
        while True:
            try:
                # Receive message with timeout
                logger.info("⏳ DEBUG: About to wait for message...")
                message = await asyncio.wait_for(websocket.receive(), timeout=1.0)
                message_count += 1
                current_time = time.time()
                
                # Handle disconnect message
                if message.get("type") == "websocket.disconnect":
                    logger.info("🔌 DEBUG: Client disconnected gracefully")
                    break
                
                logger.info(f"📨 DEBUG: Message #{message_count} received!")
                logger.info(f"🔍 DEBUG: Message keys: {list(message.keys())}")
                logger.info(f"🔍 DEBUG: Message type check - 'bytes' in message: {'bytes' in message}")
                logger.info(f"🔍 DEBUG: Message type check - 'text' in message: {'text' in message}")
                
                if "bytes" in message:
                    chunk_size = len(message["bytes"])
                    audio_buffer.extend(message["bytes"])
                    last_chunk_time = current_time
                    
                    logger.info(f"🎵 DEBUG: AUDIO CHUNK RECEIVED! Size: {chunk_size} bytes, total: {len(audio_buffer)} bytes")
                    
                    # Send chunk acknowledgment immediately
                    ack_message = {
                        "type": "chunk_received",
                        "chunk_size": chunk_size,
                        "total_size": len(audio_buffer)
                    }
                    await websocket.send_json(ack_message)
                    logger.info(f"📤 DEBUG: Sent chunk acknowledgment: {ack_message}")
                    
                    # Check if it's time to process or buffer is large enough
                    time_since_last_chunk = current_time - last_chunk_time
                    time_since_last_process = current_time - last_process_time
                    should_process = (
                        time_since_last_process >= process_interval or 
                        len(audio_buffer) >= min_chunk_size * 2  # 8KB threshold
                    )
                    
                    logger.info(f"🤔 DEBUG: Should process? {should_process}")
                    logger.info(f"   - Time since last process: {time_since_last_process:.1f}s (threshold: {process_interval}s)")
                    logger.info(f"   - Buffer size: {len(audio_buffer)} bytes (threshold: {min_chunk_size * 2} bytes)")
                    
                    if should_process:
                        logger.info("🚀 DEBUG: Starting audio processing...")
                        result = await process_audio_buffer()
                        if result:
                            await websocket.send_json(result)
                            logger.info(f"✅ DEBUG: Sent real-time result: '{result.get('text', '')[:50]}...'")
                        else:
                            logger.info("🔇 DEBUG: No result from processing")
                        
                        last_process_time = current_time
                        
                        # Keep some audio for context (overlap)
                        if len(audio_buffer) > min_chunk_size * 2:
                            # Keep last 50% of buffer for context
                            overlap_size = len(audio_buffer) // 2
                            audio_buffer = audio_buffer[-overlap_size:]
                            logger.info(f"🔄 DEBUG: Buffer trimmed to {len(audio_buffer)} bytes")
                
                elif "text" in message:
                    text_msg = message["text"].strip()
                    logger.info(f"📝 DEBUG: Text message received: '{text_msg}'")
                    
                    # Skip empty messages
                    if not text_msg:
                        logger.info("⚠️ DEBUG: Empty text message, ignoring")
                        continue
                    
                    if text_msg == "start_recording":
                        logger.info("🎙️ DEBUG: Processing start_recording command")
                        # Reset everything for new session
                        audio_buffer = bytearray()
                        transcription_history = []
                        last_process_time = time.time()
                        last_chunk_time = time.time()
                        
                        response = {
                            "type": "recording_started",
                            "message": "Real-time transcription started"
                        }
                        await websocket.send_json(response)
                        logger.info("📤 DEBUG: Sent recording_started confirmation")
                    
                    elif text_msg == "stop_recording":
                        logger.info("🛑 DEBUG: Processing stop_recording command")
                        # Force process final buffer
                        if len(audio_buffer) > 0:
                            logger.info(f"🎵 DEBUG: Force processing final buffer with {len(audio_buffer)} bytes")
                            result = await process_audio_buffer()
                            if result:
                                result["type"] = "final_transcription"
                                await websocket.send_json(result)
                                logger.info("📤 DEBUG: Sent final transcription")
                        
                        # Send complete session summary
                        full_text = " ".join([t.get("text", "") for t in transcription_history if t.get("text", "")])
                        summary = {
                            "type": "session_complete",
                            "full_text": full_text,
                            "total_segments": len(transcription_history)
                        }
                        await websocket.send_json(summary)
                        logger.info(f"📤 DEBUG: Sent session summary - segments: {len(transcription_history)}")
                        
                        # Reset for next session
                        audio_buffer = bytearray()
                        transcription_history = []
                    
                    elif text_msg == "ping":
                        await websocket.send_json({"type": "pong"})
                        logger.debug("🏓 DEBUG: Pong sent")
                    
                    else:
                        logger.warning(f"❓ DEBUG: Unknown control message: '{text_msg}'")
                
                else:
                    logger.warning(f"❓ DEBUG: Unknown message format! Message: {message}")
                    
            except asyncio.TimeoutError:
                current_time = time.time()
                logger.debug("⏰ DEBUG: Timeout occurred (no message in 1s)")
                
                # Check for silence timeout
                time_since_last_chunk = current_time - last_chunk_time
                if time_since_last_chunk > silence_threshold and len(audio_buffer) > 0:
                    logger.info(f"🔇 DEBUG: Silence detected ({time_since_last_chunk:.1f}s), processing final buffer")
                    result = await process_audio_buffer()
                    if result:
                        result["type"] = "silence_transcription"
                        await websocket.send_json(result)
                        logger.info("📤 DEBUG: Sent silence transcription")
                    
                    # Clear buffer after silence
                    audio_buffer = bytearray()
                    last_process_time = current_time
                
                # Send periodic ping
                elif time_since_last_chunk > 30:
                    logger.info("🏓 DEBUG: Sending periodic ping...")
                    try:
                        await websocket.send_json({
                            "type": "ping", 
                            "message": "Server ping - connection alive"
                        })
                    except Exception as ping_error:
                        logger.error(f"❌ DEBUG: Failed to send ping: {ping_error}")
                        break
                        
            except Exception as e:
                logger.error(f"❌ DEBUG: Error processing message: {e}")
                import traceback
                logger.error(f"🔍 DEBUG: Full traceback: {traceback.format_exc()}")
                break
                
    except WebSocketDisconnect:
        logger.info(f"🔌 Real-time STT WebSocket disconnected for user: {user.email}")
    except Exception as e:
        logger.error(f"❌ Unexpected WebSocket error: {e}")
        try:
            await websocket.close(code=1011)
        except:
            pass 