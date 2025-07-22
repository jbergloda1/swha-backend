from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from pydantic import Field

class Settings(BaseSettings):
    # Server configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Database configuration
    DATABASE_URL: str = "postgresql://user:password@localhost/swha_db"
    
    # Security configuration
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File upload configuration
    UPLOAD_DIR: str = "app/static/uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_VIDEO_EXTENSIONS: List[str] = ["mp4", "avi", "mov", "mkv", "webm"]
    ALLOWED_IMAGE_EXTENSIONS: List[str] = ["jpg", "jpeg", "png", "gif", "webp"]
    
    # Video streaming configuration
    CHUNK_SIZE: int = 1024 * 1024  # 1MB chunks
    
    # AI Model configuration
    QA_MODEL_NAME: str = "deepset/roberta-base-squad2"
    HF_CACHE_DIR: Optional[str] = None
    FORCE_CPU: bool = False
    
    # Email configuration (optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_TLS: bool = True
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None
    EMAIL_FROM_NAME: str = "SWHA Backend"
    
    # Logging configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None
    
    # CORS configuration
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Redis configuration (optional)
    REDIS_URL: Optional[str] = None
    
    # External services (optional) - S3 Configuration
    AWS_ACCESS_KEY_ID: str = Field(default="", env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(default="", env="AWS_SECRET_ACCESS_KEY") 
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    S3_BUCKET_NAME: str = Field(default="swha-audio-bucket", env="S3_BUCKET_NAME")
    S3_PRESIGNED_URL_EXPIRY: int = Field(default=3600, env="S3_PRESIGNED_URL_EXPIRY")  # 1 hour default
    USE_S3_STORAGE: bool = Field(default=False, env="USE_S3_STORAGE")
    
    # Legacy AWS bucket name (for backwards compatibility)
    AWS_BUCKET_NAME: Optional[str] = None
    
    # Google Cloud Storage (optional)
    GCS_PROJECT_ID: Optional[str] = None
    GCS_BUCKET_NAME: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    ANALYTICS_ID: Optional[str] = None
    
    # Development settings
    AUTO_MIGRATE: bool = True
    ENABLE_DOCS: bool = True
    DEV_MODE: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list."""
        if self.CORS_ORIGINS:
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return ["*"]
    
    @property 
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.DEBUG and self.DEV_MODE
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.DEBUG

    @property
    def s3_enabled(self) -> bool:
        """Check if S3 is properly configured and enabled."""
        return (
            self.USE_S3_STORAGE and 
            self.AWS_ACCESS_KEY_ID and 
            self.AWS_SECRET_ACCESS_KEY and 
            self.S3_BUCKET_NAME
        )

# Create upload directories
def create_upload_dirs():
    """Create necessary upload directories."""
    settings = Settings()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(f"{settings.UPLOAD_DIR}/videos", exist_ok=True)
    os.makedirs(f"{settings.UPLOAD_DIR}/images", exist_ok=True)
    os.makedirs(f"{settings.UPLOAD_DIR}/thumbnails", exist_ok=True)

settings = Settings()
create_upload_dirs() 