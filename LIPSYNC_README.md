# 🎬 Lipsync API Documentation

## Overview

The Lipsync API provides powerful lip synchronization capabilities using Sync.so technology. Synchronize audio with video to create realistic lip-synced content. Perfect for combining with TTS API for complete text-to-video workflows.

## 🚀 Quick Start

### 1. Prerequisites

- Sync.so API key (get from [sync.so](https://sync.so))
- Video file accessible via URL
- Audio file (can be from TTS API or uploaded)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the Server

```bash
python main.py
```

### 4. Test the API

```bash
python examples/lipsync_example.py
```

## 📋 API Endpoints

### Base URL: `/api/v1/lipsync`

All endpoints require authentication. Include your Bearer token in the Authorization header.

### 1. Create Lipsync Job

**POST** `/create`

Create a new lipsync generation job with full options.

**Request Body:**
```json
{
  "video_url": "https://example.com/video.mp4",
  "audio_url": "https://example.com/audio.wav",
  "api_key": "sk-your_sync_api_key_here",
  "model": "lipsync-2",
  "sync_mode": "cut_off",
  "output_filename": "my_synced_video"
}
```

**Response:**
```json
{
  "message": "Lipsync job created successfully",
  "job_id": "job_12345",
  "status": "PENDING",
  "video_url": "https://example.com/video.mp4",
  "audio_url": "https://example.com/audio.wav",
  "model": "lipsync-2",
  "sync_mode": "cut_off",
  "submitted_at": 1703123456.789
}
```

### 2. Create Lipsync from TTS

**POST** `/create-from-tts`

Convenience endpoint for TTS + Lipsync workflow.

**Parameters:**
- `video_url` (string, required): URL to source video
- `tts_audio_url` (string, required): Audio URL from TTS API
- `api_key` (string, required): Your Sync.so API key
- `model` (string, optional): Lipsync model (default: lipsync-2)
- `sync_mode` (string, optional): Sync mode (default: cut_off)

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/lipsync/create-from-tts" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "video_url=https://example.com/video.mp4&tts_audio_url=/static/audio/123/segment_000.wav&api_key=sk-your_key"
```

### 3. Get Job Status

**GET** `/status/{job_id}`

Check the status of a lipsync job.

**Parameters:**
- `api_key` (string, required): Your Sync.so API key

**Response:**
```json
{
  "job_id": "job_12345",
  "status": "COMPLETED",
  "output_url": "https://sync.so/output/video.mp4",
  "progress": 100.0,
  "created_at": 1703123456.789,
  "completed_at": 1703123556.789
}
```

### 4. Wait for Completion

**POST** `/wait/{job_id}`

Wait for a job to complete with automatic polling.

**Parameters:**
- `api_key` (string, required): Your Sync.so API key
- `timeout` (integer, optional): Max wait time in seconds (default: 300)
- `poll_interval` (integer, optional): Polling interval in seconds (default: 10)

### 5. Get My Jobs

**GET** `/jobs/my`

Get all lipsync jobs for the current user.

**Response:**
```json
{
  "jobs": [
    {
      "job_id": "job_12345",
      "status": "COMPLETED",
      "video_url": "https://example.com/video.mp4",
      "audio_url": "https://example.com/audio.wav",
      "model": "lipsync-2",
      "sync_mode": "cut_off",
      "output_url": "https://sync.so/output/video.mp4",
      "submitted_at": 1703123456.789,
      "completed_at": 1703123556.789,
      "user_id": 123
    }
  ],
  "total_count": 1
}
```

### 6. Get Supported Models

**GET** `/models`

Get list of available lipsync models.

**Response:**
```json
{
  "models": ["lipsync-1", "lipsync-2"],
  "total_count": 2,
  "descriptions": {
    "lipsync-1": "Basic lipsync model",
    "lipsync-2": "Advanced lipsync model with better quality"
  }
}
```

### 7. Get Sync Modes

**GET** `/sync-modes`

Get list of supported synchronization modes.

**Response:**
```json
{
  "sync_modes": ["cut_off", "loop", "fade"],
  "total_count": 3,
  "descriptions": {
    "cut_off": "Cut off audio/video at the end of the shorter one",
    "loop": "Loop the shorter content to match the longer one",
    "fade": "Fade out the longer content to match the shorter one"
  }
}
```

### 8. Cleanup Old Jobs

**POST** `/cleanup`

Remove old completed jobs from memory.

**Parameters:**
- `hours_old` (integer, optional): Hours threshold (default: 24)

## 🤖 Models & Options

### Lipsync Models

| Model | Quality | Speed | Description |
|-------|---------|-------|-------------|
| `lipsync-1` | Good | Fast | Basic model for quick results |
| `lipsync-2` | Excellent | Moderate | Advanced model with better quality |

### Sync Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `cut_off` | Cut at shorter duration | When you want exact timing |
| `loop` | Loop shorter content | For background music scenarios |
| `fade` | Fade out longer content | For smooth endings |

## 🔄 Workflow Examples

### 1. Basic Lipsync

```python
import requests

headers = {"Authorization": "Bearer YOUR_TOKEN"}

# Create job
response = requests.post("/api/v1/lipsync/create", json={
    "video_url": "https://example.com/video.mp4",
    "audio_url": "https://example.com/audio.wav",
    "api_key": "sk-your_key",
    "model": "lipsync-2"
}, headers=headers)

job_id = response.json()["job_id"]

# Check status
status = requests.get(f"/api/v1/lipsync/status/{job_id}", 
                     params={"api_key": "sk-your_key"}, 
                     headers=headers)
```

### 2. TTS + Lipsync Workflow

```python
# Step 1: Generate TTS
tts_response = requests.post("/api/v1/tts/generate-simple", params={
    "text": "Hello world!",
    "voice": "af_heart"
}, headers=headers)

audio_url = tts_response.json()["first_audio_url"]

# Step 2: Create lipsync
lipsync_response = requests.post("/api/v1/lipsync/create-from-tts", params={
    "video_url": "https://example.com/video.mp4",
    "tts_audio_url": audio_url,
    "api_key": "sk-your_key"
}, headers=headers)

job_id = lipsync_response.json()["job_id"]

# Step 3: Wait for completion
result = requests.post(f"/api/v1/lipsync/wait/{job_id}", params={
    "api_key": "sk-your_key",
    "timeout": 300
}, headers=headers)

output_video = result.json()["output_url"]
```

### 3. Batch Processing

```python
videos = ["video1.mp4", "video2.mp4", "video3.mp4"]
texts = ["Hello!", "How are you?", "Goodbye!"]

job_ids = []

for video_url, text in zip(videos, texts):
    # Generate TTS
    tts_resp = requests.post("/api/v1/tts/generate-simple", 
                           params={"text": text}, headers=headers)
    audio_url = tts_resp.json()["first_audio_url"]
    
    # Create lipsync
    lipsync_resp = requests.post("/api/v1/lipsync/create-from-tts", params={
        "video_url": video_url,
        "tts_audio_url": audio_url,
        "api_key": "sk-your_key"
    }, headers=headers)
    
    job_ids.append(lipsync_resp.json()["job_id"])

# Check all jobs
for job_id in job_ids:
    status = requests.get(f"/api/v1/lipsync/status/{job_id}", 
                         params={"api_key": "sk-your_key"}, headers=headers)
    print(f"Job {job_id}: {status.json()['status']}")
```

## 📊 Job Status States

| Status | Description |
|--------|-------------|
| `PENDING` | Job submitted, waiting to start |
| `PROCESSING` | Job is being processed |
| `COMPLETED` | Job finished successfully |
| `FAILED` | Job failed with error |

## 🔒 Authentication

All endpoints require authentication:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" ...
```

Get a token by logging in:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

## 🐛 Error Handling

### Common Errors

**401 Unauthorized**
```json
{
  "detail": "Not authenticated"
}
```

**400 Bad Request**
```json
{
  "detail": "Invalid video URL or audio URL"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Sync.so API error: [specific error message]"
}
```

### Troubleshooting

1. **Invalid API Key**
   - Check your Sync.so API key
   - Ensure it has sufficient credits

2. **Video/Audio URL Issues**
   - URLs must be publicly accessible
   - Check file format compatibility
   - Ensure URLs are not expired

3. **Job Stuck in Processing**
   - Large files take longer to process
   - Check Sync.so service status
   - Use timeout parameters appropriately

4. **Datetime Validation Errors**
   - If you see errors like "Input should be a valid number", this is related to datetime conversion
   - The API automatically converts datetime objects to timestamps
   - Use the debug endpoint to check data types: `GET /lipsync/debug/status/{job_id}`

5. **Status Enum Errors**
   - The API handles unknown status values gracefully
   - Unknown statuses default to "PENDING"
   - Check logs for status conversion warnings

### Debugging Endpoints

#### Debug Job Status
```bash
GET /api/v1/lipsync/debug/status/{job_id}?api_key=sk-your_key
```

This endpoint returns raw data without schema validation, useful for debugging data type issues:

```json
{
  "message": "Raw status data for debugging",
  "job_id": "job_12345",
  "raw_result": {
    "job_id": "job_12345",
    "status": "COMPLETED",
    "created_at": 1703123456.789,
    "completed_at": 1703123556.789
  },
  "data_types": {
    "created_at": "<class 'float'>",
    "completed_at": "<class 'float'>",
    "status": "<class 'str'>"
  }
}
```

## 💡 Best Practices

### Performance Tips

1. **Use appropriate models**: lipsync-2 for quality, lipsync-1 for speed
2. **Optimize file sizes**: Smaller files process faster
3. **Batch processing**: Submit multiple jobs simultaneously
4. **Monitor usage**: Track API credits and usage patterns

### File Requirements

- **Video formats**: MP4, MOV, AVI, WebM
- **Audio formats**: WAV, MP3, M4A, AAC
- **Max file size**: Check Sync.so limits
- **Resolution**: Higher quality = longer processing time

### URL Requirements

- URLs must be publicly accessible
- HTTPS recommended
- Avoid password-protected or temporary URLs
- CDN URLs work well

## 🔧 Configuration

### Environment Variables

```bash
# Optional: Set default Sync.so API URL
SYNC_API_URL=https://api.sync.so

# Optional: Set default timeouts
LIPSYNC_DEFAULT_TIMEOUT=300
LIPSYNC_POLL_INTERVAL=10
```

### Service Configuration

The LipsyncService can be configured in `app/services/lipsync_service.py`:

```python
class LipsyncService:
    def __init__(self):
        self.base_url = "https://api.sync.so"  # Sync.so API URL
        self.active_jobs = {}  # In-memory job tracking
```

## 📈 Integration Examples

### React Frontend

```javascript
const createLipsync = async (videoUrl, audioUrl, apiKey) => {
  const response = await fetch('/api/v1/lipsync/create', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      video_url: videoUrl,
      audio_url: audioUrl,
      api_key: apiKey,
      model: 'lipsync-2'
    })
  });
  
  return response.json();
};
```

### Node.js Backend

```javascript
const axios = require('axios');

const createLipsyncJob = async (videoUrl, audioUrl, syncApiKey) => {
  try {
    const response = await axios.post('/api/v1/lipsync/create', {
      video_url: videoUrl,
      audio_url: audioUrl,
      api_key: syncApiKey,
      model: 'lipsync-2'
    }, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    return response.data;
  } catch (error) {
    console.error('Lipsync job failed:', error.response.data);
    throw error;
  }
};
```

## 📄 License

This Lipsync integration uses the Sync.so API. Check Sync.so's terms of service and pricing for usage terms. 