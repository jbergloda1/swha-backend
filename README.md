# SWHA Backend API

A comprehensive FastAPI backend with video streaming, user authentication, database management, and AI-powered question answering.

## Features

- 🚀 **FastAPI** - Modern, fast web framework for building APIs
- 🔐 **Authentication** - JWT-based user authentication and authorization
- 🎥 **Video Streaming** - Upload, process, and stream videos with range support
- 🗄️ **Database** - PostgreSQL with SQLAlchemy ORM
- 📁 **File Upload** - Support for video and image uploads
- 🔍 **Search** - Video search functionality
- 📊 **Analytics** - Video view tracking
- 🎯 **CORS** - Cross-origin resource sharing support
- 🤖 **AI Question Answering** - RoBERTa-based extractive QA system

## Tech Stack

- **FastAPI** - API framework
- **PostgreSQL** - Database
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations
- **JWT** - Authentication
- **OpenCV** - Video processing
- **FFmpeg** - Video metadata extraction
- **Uvicorn** - ASGI server
- **Transformers** - Hugging Face transformers for AI
- **PyTorch** - Deep learning framework
- **RoBERTa** - Question answering model

## Project Structure

```
swha-backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py          # Authentication routes
│   │   │   ├── users.py         # User management
│   │   │   ├── videos.py        # Video CRUD and streaming
│   │   │   ├── upload.py        # File upload endpoints
│   │   │   └── qa.py            # Question Answering API
│   │   └── dependencies.py     # Route dependencies
│   ├── core/
│   │   ├── config.py           # Configuration settings
│   │   └── security.py         # Security utilities
│   ├── database/
│   │   └── database.py         # Database connection
│   ├── models/
│   │   ├── user.py             # User model
│   │   ├── video.py            # Video model
│   │   └── qa.py               # QA History model
│   ├── schemas/
│   │   ├── user.py             # User Pydantic schemas
│   │   ├── video.py            # Video Pydantic schemas
│   │   └── qa.py               # QA Pydantic schemas
│   ├── services/
│   │   ├── video_service.py    # Video processing service
│   │   └── qa_service.py       # Question Answering service
│   └── static/                 # Static files (uploads)
├── alembic/                    # Database migrations
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── alembic.ini                # Alembic configuration
└── .env.example               # Environment variables example
```

## Setup Instructions

### 1. Clone and Navigate

```bash
cd swha-backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: The installation may take some time due to PyTorch and Transformers libraries. For GPU support, install CUDA-compatible PyTorch version.

### 4. Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` file with your configuration:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/swha_db

# Security
SECRET_KEY=your-super-secret-key-here
```

### 5. Database Setup

Create PostgreSQL database:

```sql
CREATE DATABASE swha_db;
```

Initialize Alembic and create tables:

```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### 6. Run the Application

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**Note**: First startup may take longer as the RoBERTa model (around 500MB) needs to be downloaded from Hugging Face.

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login with form data
- `POST /api/v1/auth/login-json` - Login with JSON

### Users

- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update current user profile
- `GET /api/v1/users/` - Get all users (admin only)
- `GET /api/v1/users/{user_id}` - Get user by ID
- `DELETE /api/v1/users/{user_id}` - Delete user (admin only)

### Videos

- `GET /api/v1/videos/` - Get paginated video list
- `GET /api/v1/videos/{video_id}` - Get video details
- `PUT /api/v1/videos/{video_id}` - Update video
- `DELETE /api/v1/videos/{video_id}` - Delete video
- `GET /api/v1/videos/{video_id}/stream` - Stream video

### Upload

- `POST /api/v1/upload/video` - Upload single video
- `POST /api/v1/upload/videos` - Upload multiple videos
- `POST /api/v1/upload/image` - Upload image

### Question Answering (AI)

- `POST /api/v1/qa/answer` - Answer single question
- `POST /api/v1/qa/answer-batch` - Answer multiple questions
- `POST /api/v1/qa/answer-detailed` - Get detailed answer with probabilities
- `GET /api/v1/qa/stats` - Get QA usage statistics
- `GET /api/v1/qa/history` - Get QA history
- `GET /api/v1/qa/model-info` - Get model information
- `POST /api/v1/qa/demo` - Public demo endpoint (no auth)

### Health

- `GET /` - API status
- `GET /health` - Health check

## Usage Examples

### Register User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepassword",
    "full_name": "John Doe"
  }'
```

### Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login-json" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "securepassword"
  }'
```

### Question Answering

```bash
# Demo endpoint (no authentication required)
curl -X POST "http://localhost:8000/api/v1/qa/demo" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the capital of France?",
    "context": "France is a country in Western Europe. Its capital and largest city is Paris, which is located in the north-central part of the country."
  }'
```

```bash
# Authenticated endpoint
curl -X POST "http://localhost:8000/api/v1/qa/answer" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "question": "What is machine learning?",
    "context": "Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention."
  }'
```

### Upload Video

```bash
curl -X POST "http://localhost:8000/api/v1/upload/video" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@video.mp4" \
  -F "title=My Video" \
  -F "description=Video description" \
  -F "is_public=true"
```

### Stream Video

```bash
curl "http://localhost:8000/api/v1/videos/1/stream" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  --output video.mp4
```

## AI Question Answering

The API includes a powerful question answering system using the **deepset/roberta-base-squad2** model from Hugging Face. This model can:

- **Extract answers** from provided context passages
- **Handle unanswerable questions** (returns appropriate response when answer isn't in context)
- **Provide confidence scores** for answers
- **Track answer positions** in the original text
- **Support batch processing** of multiple questions
- **Automatically use GPU** if available for faster inference

### Model Features

- **Model**: RoBERTa-base fine-tuned on SQuAD 2.0
- **Type**: Extractive Question Answering
- **Languages**: English
- **Max Context Length**: 512 tokens
- **Capabilities**: Answerable and unanswerable questions

### Example Response

```json
{
  "question": "What is the capital of France?",
  "context": "France is a country in Western Europe. Its capital and largest city is Paris...",
  "answer": "Paris",
  "confidence": 0.9876,
  "start_position": 65,
  "end_position": 70,
  "is_answerable": true,
  "processing_time_ms": 45
}
```

## Development

### Database Migrations

Create new migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:

```bash
alembic upgrade head
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
```

## Production Deployment

1. Set `DEBUG=False` in environment
2. Use strong `SECRET_KEY`
3. Configure PostgreSQL with proper credentials
4. Set up reverse proxy (nginx)
5. Use HTTPS
6. Configure CORS origins properly
7. Set up file storage (AWS S3, etc.)
8. **GPU Setup**: For better QA performance, use GPU-enabled servers
9. **Model Caching**: Consider using model caching for faster startup

### GPU Support

For GPU acceleration:

1. Install CUDA-compatible PyTorch:
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

2. Verify GPU availability:
   ```bash
   curl "http://localhost:8000/api/v1/qa/model-info"
   ```

## API Documentation

When running the server, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Performance Notes

- **First Request**: May take 2-3 seconds as the model loads into memory
- **Subsequent Requests**: Typically 100-500ms depending on context length
- **GPU Acceleration**: 3-5x faster inference with GPU
- **Memory Usage**: ~1.5GB RAM for the model
- **Concurrent Requests**: Supported with proper threading

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

## License

MIT License 