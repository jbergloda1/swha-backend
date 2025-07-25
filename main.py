from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.api.routes import auth, users, videos, upload, qa, tts, lipsync, stt, captioning
from app.database.database import engine, Base
from app.core.config import settings

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SWHA Backend API",
    description="A comprehensive backend API with FastAPI, video streaming, database, and AI question answering",
    version="1.0.0",
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_DOCS else None
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for video serving
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(videos.router, prefix="/api/v1/videos", tags=["videos"])
app.include_router(upload.router, prefix="/api/v1/upload", tags=["upload"])
app.include_router(qa.router, prefix="/api/v1/qa", tags=["question-answering"])
app.include_router(tts.router, prefix="/api/v1/tts", tags=["text-to-speech"])
app.include_router(lipsync.router, prefix="/api/v1/lipsync", tags=["lipsync"])
app.include_router(stt.router, prefix="/api/v1/stt", tags=["speech-to-text"])
app.include_router(captioning.router, prefix="/api/v1/captioning", tags=["image-captioning"])

@app.get("/")
async def root():
    return {
        "message": "SWHA Backend API is running!",
        "version": "1.0.0",
        "environment": "development" if settings.is_development else "production",
        "features": [
            "User Authentication",
            "Video Streaming",
            "File Upload",
            "AI Question Answering (RoBERTa)",
            "Text-to-Speech (Kokoro)",
            "Lip Sync (Sync.so)",
            "Speech-to-Text (Whisper)",
            "Database Management"
        ],
        "docs": {
            "swagger": "/docs" if settings.ENABLE_DOCS else "disabled",
            "redoc": "/redoc" if settings.ENABLE_DOCS else "disabled"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "version": "1.0.0",
        "environment": "development" if settings.is_development else "production"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    ) 