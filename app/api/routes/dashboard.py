from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.services.lipsync_service import get_lipsync_service
from app.services.tts_service import get_tts_service
from app.api.dependencies import get_current_user, get_current_active_superuser
from app.models.qa import QAHistory
from app.models.user import User
from app.database.database import get_db
import psutil
import platform
import os
from sqlalchemy.orm import Session

router = APIRouter()

@router.get("/system", tags=["dashboard"])
async def get_system_stats():
    """Lấy thông tin hệ thống: CPU, RAM, load, OS."""
    cpu_percent = psutil.cpu_percent(interval=0.5)
    cpu_count = psutil.cpu_count()
    ram = psutil.virtual_memory()
    load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)
    return {
        "cpu_percent": cpu_percent,
        "cpu_count": cpu_count,
        "ram_total": ram.total,
        "ram_used": ram.used,
        "ram_percent": ram.percent,
        "load_avg": load_avg,
        "os": platform.system(),
        "os_version": platform.version(),
        "hostname": platform.node(),
    }

@router.get("/models", tags=["dashboard"])
async def get_model_stats():
    """Lấy thông tin các model: trạng thái, số lần sử dụng, tên model."""
    lipsync_service = get_lipsync_service()
    tts_service = get_tts_service()
    # Thống kê model lipsync
    lipsync_jobs = lipsync_service.get_all_jobs()
    lipsync_models = {}
    for job in lipsync_jobs:
        lipsync_models.setdefault(job.model, 0)
        lipsync_models[job.model] += 1
    # Thống kê model TTS (nếu có)
    # Ở đây chỉ trả về tên model, số lần sử dụng cần lưu log riêng nếu muốn
    tts_models = ["kokoro"]
    return {
        "lipsync": {
            "supported_models": lipsync_service.get_supported_models(),
            "active_jobs": len(lipsync_jobs),
            "job_count_by_model": lipsync_models,
        },
        "tts": {
            "supported_models": tts_models,
        }
    }

@router.get("/user-requests", tags=["dashboard"])
async def get_user_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_active_superuser)):
    """Thống kê số lần request QA của từng user (chỉ admin)."""
    # Thống kê số lần hỏi QA của từng user
    user_counts = db.query(QAHistory.user_id, User.username, User.email, db.func.count(QAHistory.id)) \
        .join(User, QAHistory.user_id == User.id) \
        .group_by(QAHistory.user_id, User.username, User.email).all()
    return [
        {
            "user_id": row[0],
            "username": row[1],
            "email": row[2],
            "qa_request_count": row[3]
        }
        for row in user_counts
    ] 