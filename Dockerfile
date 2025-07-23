FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TRANSFORMERS_CACHE=/app/.cache/huggingface \
    HF_HOME=/app/.cache/huggingface \
    SPACY_DATA=/app/.cache/spacy

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    ffmpeg \
    libsndfile1 \
    espeak-ng \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN addgroup --system app && adduser --system --group app

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy initialization script
COPY init_models.py .

# Run model initialization script
# This downloads all required models and sets up cache directories
RUN python init_models.py

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p app/static/uploads app/static/audio app/static/videos \
    && mkdir -p /app/.cache/huggingface \
    && mkdir -p /app/.cache/spacy \
    && mkdir -p /home/app/.cache/spacy \
    && chown -R app:app /app \
    && chown -R app:app /home/app \
    && chmod -R 755 /app/.cache

# Switch to app user
USER app

# Set environment variables for app user
ENV HOME=/home/app \
    SPACY_DATA=/home/app/.cache/spacy

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 