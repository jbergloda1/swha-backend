# SWHA Backend API

A comprehensive **Software with Human-AI (SWHA)** backend built with FastAPI, featuring advanced AI capabilities including question answering, text-to-speech, lip synchronization, video streaming, and cloud storage integration.

## 🌟 Key Features

- 🤖 **AI Question Answering** - RoBERTa-based extractive QA system with GPU acceleration
- 🎵 **Text-to-Speech** - High-quality voice synthesis using Kokoro library
- 🎬 **Lip Synchronization** - Advanced lip sync capabilities using Sync.so technology
- 🎥 **Video Streaming** - Upload, process, and stream videos with range support
- ☁️ **Cloud Storage** - AWS S3 integration with presigned URLs for secure file access
- 🔐 **Authentication** - JWT-based user authentication and authorization
- 🗄️ **Database Management** - PostgreSQL with SQLAlchemy ORM and Alembic migrations
- 📁 **File Upload** - Support for video, audio, and image uploads
- 🔍 **Search & Analytics** - Video search functionality and view tracking
- 🎯 **CORS Support** - Cross-origin resource sharing for web applications
- 🐳 **Containerization** - Full Docker deployment with Nginx reverse proxy
- 📊 **Monitoring** - Health checks, logging, and performance monitoring

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)

```bash
# Clone and navigate to the project
cd swha-backend

# Quick deployment with Docker
chmod +x quick-deploy.sh
./quick-deploy.sh
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python -m venv human-ai-venv
source human-ai-venv/bin/activate  # On Windows: human-ai-venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp env.template .env
# Edit .env with your configuration

# 4. Setup database
# Create PostgreSQL database and run migrations
alembic upgrade head

# 5. Start the application
python main.py
```

## 🏗️ Architecture & Tech Stack

### Core Technologies
- **FastAPI** - Modern, fast web framework for building APIs
- **PostgreSQL** - Advanced open-source relational database
- **SQLAlchemy** - Python SQL toolkit and ORM
- **Alembic** - Database migration tool
- **Redis** - In-memory data structure store for caching
- **JWT** - JSON Web Tokens for authentication

### AI & Machine Learning
- **Transformers** - Hugging Face transformers library
- **PyTorch** - Deep learning framework
- **RoBERTa** - Question answering model (deepset/roberta-base-squad2)
- **Kokoro** - High-quality text-to-speech synthesis
- **Sync.so** - Advanced lip synchronization technology
- **Whisper** - High-performance speech-to-text from OpenAI

### Media Processing
- **OpenCV** - Computer vision and video processing
- **FFmpeg** - Video metadata extraction and processing
- **Pillow** - Image processing library
- **SoundFile** - Audio file I/O

### DevOps & Deployment
- **Docker** - Containerization platform
- **Docker Compose** - Multi-container application management
- **Nginx** - Web server and reverse proxy
- **AWS S3** - Cloud storage integration
- **Uvicorn** - ASGI web server

## 📁 Project Structure

```
swha-backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   ├── users.py         # User management
│   │   │   ├── videos.py        # Video CRUD and streaming
│   │   │   ├── upload.py        # File upload endpoints
│   │   │   ├── qa.py            # Question Answering API
│   │   │   ├── tts.py           # Text-to-Speech API
│   │   │   ├── lipsync.py       # Lip Synchronization API
│   │   │   └── stt.py           # Speech-to-Text API
│   │   └── dependencies.py      # Route dependencies
│   ├── core/
│   │   ├── config.py            # Configuration settings
│   │   └── security.py          # Security utilities
│   ├── database/
│   │   └── database.py          # Database connection
│   ├── models/                  # SQLAlchemy models
│   ├── schemas/                 # Pydantic schemas
│   ├── services/                # Business logic services
│   └── static/                  # Static files (uploads, audio, videos)
├── alembic/                     # Database migrations
├── nginx/                       # Nginx configuration
├── examples/                    # Usage examples
├── main.py                      # Application entry point
├── docker-compose.yml           # Docker services configuration
├── Dockerfile                   # Application container
├── requirements.txt             # Python dependencies
├── deploy.sh                    # Deployment script
├── quick-deploy.sh              # Quick deployment script
├── install-docker.sh            # Docker installation script
├── .env.template               # Environment variables template
├── DEPLOYMENT.md               # Detailed deployment guide
├── TTS_README.md               # Text-to-Speech documentation
├── LIPSYNC_README.md           # Lip Sync documentation
└── S3_INTEGRATION.md           # S3 integration guide
```

## 🔧 Configuration

### Environment Variables

Copy the template and configure:
```bash
cp env.template .env
```

Key configuration options:

```env
# Server Configuration
HOST=127.0.0.1
PORT=8000
DEBUG=False

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/swha_db

# Security
SECRET_KEY=your-super-secret-key-32-chars-minimum
ACCESS_TOKEN_EXPIRE_MINUTES=60

# AWS S3 (Optional)
USE_S3_STORAGE=true
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
S3_BUCKET_NAME=swha-audio-bucket

# AI Models
QA_MODEL_NAME=deepset/roberta-base-squad2
FORCE_CPU=false  # Set to true to disable GPU

# Speech-to-Text
STT_MODEL_NAME=base # Options: tiny, base, small, medium, large

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## 📚 API Documentation

### Base URL: `http://localhost:8000/api/v1`

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login (form data)
- `POST /auth/login-json` - Login (JSON)

### AI Question Answering
- `POST /qa/answer` - Answer single question
- `POST /qa/answer-batch` - Answer multiple questions
- `POST /qa/answer-detailed` - Get detailed answer with probabilities
- `POST /qa/demo` - Public demo (no auth required)
- `GET /qa/stats` - Usage statistics
- `GET /qa/history` - QA history
- `GET /qa/model-info` - Model information

### Text-to-Speech
- `POST /tts/generate` - Generate speech (full options)
- `POST /tts/generate-simple` - Generate speech (simple)
- `GET /tts/voices` - Available voices
- `GET /tts/languages` - Supported languages
- `DELETE /tts/cleanup/{user_id}` - Clean up user audio files

### Speech-to-Text (New)
- `POST /stt/transcribe` - Transcribe audio file to text. Accepts either a direct file upload or a URL.

### Lip Synchronization
- `POST /lipsync/create` - Create lipsync job
- `POST /lipsync/create-from-tts` - Create from TTS output
- `GET /lipsync/status/{job_id}` - Check job status
- `GET /lipsync/result/{job_id}` - Get result
- `DELETE /lipsync/cleanup/{user_id}` - Clean up user files

### Video Management
- `GET /videos/` - List videos (paginated)
- `GET /videos/{video_id}` - Get video details
- `GET /videos/{video_id}/stream` - Stream video
- `PUT /videos/{video_id}` - Update video
- `DELETE /videos/{video_id}` - Delete video

### File Upload
- `POST /upload/video` - Upload video
- `POST /upload/videos` - Upload multiple videos
- `POST /upload/image` - Upload image

### User Management
- `GET /users/me` - Current user profile
- `PUT /users/me` - Update profile
- `GET /users/` - All users (admin)
- `GET /users/{user_id}` - User by ID
- `DELETE /users/{user_id}` - Delete user (admin)

## 🎯 Usage Examples

### AI Question Answering

```bash
# Demo endpoint (no authentication)
curl -X POST "http://localhost:8000/api/v1/qa/demo" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is machine learning?",
    "context": "Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention."
  }'
```

### Text-to-Speech

```bash
# Generate speech
curl -X POST "http://localhost:8000/api/v1/tts/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world! This is a test of the TTS system.",
    "voice": "af_heart",
    "language_code": "a",
    "speed": 1.0
  }'
```

### Speech-to-Text

```bash
# Option 1: Transcribe an audio file via direct upload
curl -X POST "http://localhost:8000/api/v1/stt/transcribe" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/your/audio.mp3"

# Option 2: Transcribe an audio file via URL
curl -X POST "http://localhost:8000/api/v1/stt/transcribe" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "audio_url=https://example.com/audio.wav"
```

### Lip Synchronization

```bash
# Create lipsync from TTS
curl -X POST "http://localhost:8000/api/v1/lipsync/create-from-tts" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://example.com/video.mp4",
    "tts_audio_url": "https://example.com/audio.wav",
    "api_key": "your_sync_api_key"
  }'
```

### Video Upload & Streaming

```bash
# Upload video
curl -X POST "http://localhost:8000/api/v1/upload/video" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@video.mp4" \
  -F "title=My Video" \
  -F "description=Test video" \
  -F "is_public=true"

# Stream video with range support
curl -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Range: bytes=0-1048576" \
  "http://localhost:8000/api/v1/videos/1/stream"
```

## 🚀 Deployment

### Docker Deployment (Production)

The project includes comprehensive deployment automation:

```bash
# Quick deployment
./quick-deploy.sh

# Or use the full deployment script
./deploy.sh up

# Check status
./deploy.sh status

# View logs
./deploy.sh logs

# Update application
./deploy.sh update
```

### Manual Deployment

For detailed deployment instructions, see:
- [`DEPLOYMENT.md`](DEPLOYMENT.md) - Complete Docker deployment guide
- [`TTS_README.md`](TTS_README.md) - Text-to-Speech setup
- [`LIPSYNC_README.md`](LIPSYNC_README.md) - Lip Sync configuration
- [`S3_INTEGRATION.md`](S3_INTEGRATION.md) - AWS S3 setup

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure PostgreSQL with secure credentials
- [ ] Set up SSL/HTTPS with nginx
- [ ] Configure CORS origins for your domains
- [ ] Set up S3 bucket for file storage
- [ ] Configure monitoring and logging
- [ ] Set up backup strategy
- [ ] Enable GPU acceleration for AI models (optional)

## 🔧 AI Model Information

### Question Answering Model
- **Model**: RoBERTa-base fine-tuned on SQuAD 2.0
- **Size**: ~500MB
- **Languages**: English
- **Max Context**: 512 tokens
- **Features**: Extractive QA, handles unanswerable questions
- **GPU Support**: Automatic detection and usage

### Text-to-Speech
- **Engine**: Kokoro TTS
- **Quality**: High-quality voice synthesis
- **Languages**: Multiple language support
- **Voices**: Various voice types available
- **Features**: Speed control, multi-line processing

### Speech-to-Text
- **Engine**: OpenAI Whisper
- **Models**: tiny, base, small, medium, large
- **Features**: High accuracy, multi-language support
- **GPU Support**: Automatic detection and usage

### Lip Synchronization
- **Technology**: Sync.so API
- **Models**: lipsync-2 (default), multiple available
- **Sync Modes**: cut_off, loop, extend
- **Input**: Video + audio files
- **Output**: Synchronized video

## 📊 Performance & Monitoring

### API Performance
- **First Request**: 2-3 seconds (model loading)
- **Subsequent Requests**: 100-500ms
- **GPU Acceleration**: 3-5x faster inference
- **Memory Usage**: ~1.5GB for AI models
- **Concurrent Support**: Multi-threaded processing

### Health Monitoring
```bash
# Application health
curl http://localhost:8000/health

# Service status (Docker)
./deploy.sh status

# Resource monitoring
docker stats
```

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Development

### Local Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Code formatting
black .

# Database migrations
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

For detailed setup and usage instructions, refer to:
- [Deployment Guide](DEPLOYMENT.md)
- [TTS Documentation](TTS_README.md)
- [TTS Troubleshooting Guide](TTS_TROUBLESHOOTING.md) - **Essential for Docker permission issues**
- [Lipsync Documentation](LIPSYNC_README.md)
- [S3 Integration Guide](S3_INTEGRATION.md)

For issues and questions, please create an issue in the repository. 

# 🎤 Real-time Speech-to-Text WebSocket API

## Overview
This backend provides a real-time speech-to-text (STT) API using FastAPI, Whisper, and WebSocket streaming. It supports continuous audio streaming from the frontend and returns live transcription results.

---

## 🚀 Quickstart for Frontend Integration

### 1. **Authentication**
- Obtain a JWT access token via the `/api/v1/auth/login` endpoint.
- Pass the token as a query parameter when connecting to the WebSocket:
  ```
  ws://<BACKEND_HOST>/api/v1/stt/ws/transcribe?token=<ACCESS_TOKEN>
  ```

### 2. **WebSocket Message Protocol**
- **Text message** `"start_recording"`: Start a new session
- **Binary message** (ArrayBuffer/Blob): Audio chunk (WebM/Opus or WAV)
- **Text message** `"stop_recording"`: End session and get final result

#### **Server Responses**
- `{ "type": "connected", ... }`: Connection ready
- `{ "type": "recording_started" }`: Session started
- `{ "type": "chunk_received", ... }`: Audio chunk acknowledged
- `{ "type": "partial_transcription", "text": ... }`: Real-time result
- `{ "type": "session_complete", "full_text": ... }`: Final result

### 3. **Frontend Example (JavaScript)**
```js
const token = 'YOUR_JWT_TOKEN';
const ws = new WebSocket(`ws://localhost:8000/api/v1/stt/ws/transcribe?token=${token}`);

ws.onopen = () => {
  ws.send('start_recording');
  // Start sending audio chunks from MediaRecorder...
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'partial_transcription') {
    console.log('Live:', data.text);
  } else if (data.type === 'session_complete') {
    console.log('Final:', data.full_text);
  }
};

// To send audio chunk:
// ws.send(audioBuffer);
// To stop:
// ws.send('stop_recording');
```

### 4. **Audio Capture (Browser)**
```js
const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
recorder.ondataavailable = (e) => {
  if (e.data.size > 0) e.data.arrayBuffer().then(buf => ws.send(buf));
};
recorder.start(100); // 100ms chunks
```

---

## 🛡️ Notes & Best Practices
- **Use native browser WebSocket API** (not `websocket-client`)
- **Send audio as binary (ArrayBuffer/Blob)**
- **Chunk size**: 1-4KB, every 100-500ms for best latency
- **Sample rate**: 16kHz mono recommended
- **Token expires**: Always use a fresh JWT
- **Monitor `chunk_received` and `partial_transcription` for feedback**

---

## 🧑‍💻 Backend Tech Stack
- FastAPI + Uvicorn
- Whisper (OpenAI)
- WebSocket streaming
- JWT authentication

---

## 📞 Support
- If you encounter issues:
  1. Check token validity
  2. Verify WebSocket URL and query params
  3. Ensure audio is sent as binary
  4. Check browser console and backend logs

---

**Status:** ✅ Ready for real-time frontend integration 