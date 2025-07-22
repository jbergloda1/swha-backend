# 🎵☁️ S3 Integration for TTS Audio Storage

## Overview

This integration adds AWS S3 support for storing TTS-generated audio files with presigned URL generation. Audio files can be stored either locally (default fallback) or in S3 with automatic presigned URL generation for secure, time-limited access.

## 🚀 Features

- ✅ **S3 Upload**: Automatic upload of generated audio files to AWS S3
- ✅ **Presigned URLs**: Generate secure, time-limited URLs for audio access
- ✅ **Local Fallback**: Falls back to local storage if S3 is unavailable
- ✅ **Flexible Expiry**: Configurable presigned URL expiration times
- ✅ **Metadata Support**: Store rich metadata with audio files
- ✅ **Cleanup Integration**: Clean up both local and S3 files
- ✅ **Lipsync Compatibility**: Seamless integration with lipsync workflows

## 📋 Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Enable S3 storage
USE_S3_STORAGE=true

# AWS Credentials
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key_here
AWS_REGION=us-east-1

# S3 Configuration
S3_BUCKET_NAME=swha-audio-bucket
S3_PRESIGNED_URL_EXPIRY=3600  # 1 hour
```

### AWS Setup

1. **Create S3 Bucket**:
   ```bash
   aws s3 mb s3://swha-audio-bucket --region us-east-1
   ```

2. **Create IAM User** with S3 permissions:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "s3:PutObject",
           "s3:GetObject",
           "s3:DeleteObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::swha-audio-bucket",
           "arn:aws:s3:::swha-audio-bucket/*"
         ]
       }
     ]
   }
   ```

3. **Generate Access Keys** for the IAM user

## 🎯 API Usage

### Generate TTS with S3 Storage

```python
import requests

headers = {"Authorization": "Bearer YOUR_TOKEN"}

# Full API request
response = requests.post("/api/v1/tts/generate", json={
    "text": "Hello world!",
    "voice": "af_heart",
    "language_code": "a",
    "use_s3": True,
    "presigned_url_expiry": 7200  # 2 hours
}, headers=headers)

result = response.json()
print(f"Storage type: {result['storage_type']}")  # "s3" or "local"
print(f"Audio files: {result['audio_files']}")    # List of presigned URLs
```

### Simple API Request

```python
# Simple request with defaults
response = requests.post("/api/v1/tts/generate-simple", params={
    "text": "Hello world!",
    "use_s3": True
}, headers=headers)
```

### Check S3 Configuration

```python
response = requests.get("/api/v1/tts/s3-info", headers=headers)
s3_info = response.json()
print(f"S3 enabled: {s3_info['s3_enabled']}")
```

## 📊 Response Format

### TTS Response with S3

```json
{
  "message": "Speech generated successfully",
  "audio_files": [
    "https://swha-audio-bucket.s3.amazonaws.com/audio/users/123/1703123456_123/segment_000.wav?AWSAccessKeyId=..."
  ],
  "audio_segments": [
    {
      "index": 0,
      "graphemes": "Hello world!",
      "phonemes": "həˈloʊ wɜrld",
      "filename": "segment_000.wav",
      "local_url": "/static/audio/1703123456_123/segment_000.wav",
      "presigned_url": "https://swha-audio-bucket.s3.amazonaws.com/...",
      "s3_key": "audio/users/123/1703123456_123/segment_000.wav",
      "expires_at": 1703127056.789
    }
  ],
  "total_segments": 1,
  "language_code": "a",
  "voice": "af_heart",
  "processing_time": 1.23,
  "storage_type": "s3",
  "session_id": "1703123456_123",
  "expires_at": 1703127056.789
}
```

## 🔄 Workflow Integration

### TTS + Lipsync with S3

```python
# Step 1: Generate TTS with S3
tts_response = requests.post("/api/v1/tts/generate-simple", params={
    "text": "Hello world!",
    "use_s3": True
}, headers=headers)

presigned_url = tts_response.json()["first_audio_url"]

# Step 2: Use presigned URL in lipsync
lipsync_response = requests.post("/api/v1/lipsync/create-from-tts", params={
    "video_url": "https://example.com/video.mp4",
    "tts_audio_url": presigned_url,  # Uses S3 presigned URL
    "api_key": "sk-your_sync_key"
}, headers=headers)
```

## 🗂️ File Organization

S3 files are organized with the following structure:

```
s3://swha-audio-bucket/
├── audio/
│   ├── users/
│   │   ├── 123/                    # User ID
│   │   │   ├── 1703123456_123/     # Session ID
│   │   │   │   ├── segment_000.wav
│   │   │   │   ├── segment_001.wav
│   │   │   │   └── ...
│   │   └── 456/
│   │       └── ...
│   └── anonymous/                  # For non-authenticated requests
│       ├── 1703123456_anonymous/
│       └── ...
```

## 🧹 Cleanup & Management

### Automatic Cleanup

```python
# Cleanup both local and S3 files
response = requests.post("/api/v1/tts/cleanup", params={
    "days_old": 7,
    "cleanup_s3": True
}, headers=headers)

result = response.json()
print(f"Local files cleaned: {result['local_files_cleaned']}")
print(f"S3 files cleaned: {result['s3_files_cleaned']}")
```

### Manual S3 Operations

```python
from app.services.s3_service import get_s3_service

s3_service = get_s3_service()

# List files
files = s3_service.list_audio_files(prefix="audio/users/123/")

# Delete specific file
s3_service.delete_audio_file("audio/users/123/session/segment_000.wav")

# Get file info
info = s3_service.get_file_info("audio/users/123/session/segment_000.wav")
```

## 🔒 Security & Best Practices

### Presigned URL Security

- URLs are time-limited (default 1 hour)
- S3 bucket should not allow public access
- Use HTTPS-only bucket policies
- Monitor access logs

### IAM Best Practices

- Use least-privilege IAM policies
- Rotate access keys regularly
- Use IAM roles in production when possible
- Enable CloudTrail for auditing

### Example Bucket Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyInsecureConnections",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::swha-audio-bucket",
        "arn:aws:s3:::swha-audio-bucket/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

## 🐛 Troubleshooting

### Common Issues

1. **S3 Upload Failures**
   ```bash
   # Check AWS credentials
   aws sts get-caller-identity
   
   # Test bucket access
   aws s3 ls s3://swha-audio-bucket/
   ```

2. **boto3 upload_file() ContentType Error**
   - **Error**: `upload_file() got an unexpected keyword argument 'ContentType'`
   - **Fix**: Use `ExtraArgs` parameter instead of passing ContentType directly
   - **Solution**: This has been fixed in the latest version of S3Service

3. **Presigned URL Errors**
   - Check URL expiration time
   - Verify bucket permissions
   - Ensure CORS configuration if accessing from browser

4. **Local Fallback Triggered**
   - Check S3 configuration in logs
   - Verify AWS credentials
   - Check bucket existence and permissions

### Debug Endpoints

```python
# Check S3 configuration
GET /api/v1/tts/s3-info

# Test with debug logging
import logging
logging.getLogger("app.services.s3_service").setLevel(logging.DEBUG)
```

### Quick S3 Test

```bash
# Run S3 integration test
cd swha-backend
python test_s3_fix.py
```

This test script will:
- ✅ Check S3 configuration
- ✅ Test bucket accessibility
- ✅ Test file upload with metadata
- ✅ Test presigned URL generation
- ✅ Test file info retrieval
- ✅ Test cleanup functionality

## 📈 Performance Considerations

### Optimization Tips

1. **Parallel Uploads**: Multiple segments uploaded concurrently
2. **Local Cleanup**: Remove local files after successful S3 upload
3. **Presigned URL Caching**: Cache URLs until expiration
4. **Regional Buckets**: Use S3 bucket in same region as application

### Monitoring

- Monitor S3 upload success/failure rates
- Track presigned URL usage
- Monitor S3 storage costs
- Set up CloudWatch alarms for errors

## 🧪 Testing

### Run Tests

```bash
# Test S3 integration
python examples/tts_s3_example.py

# Test with specific configuration
USE_S3_STORAGE=true python examples/tts_s3_example.py
```

### Test Checklist

- [ ] S3 bucket accessibility
- [ ] File upload functionality
- [ ] Presigned URL generation
- [ ] URL accessibility and expiration
- [ ] Local fallback when S3 unavailable
- [ ] Cleanup functionality
- [ ] Lipsync integration with presigned URLs

## 🔧 Configuration Reference

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `USE_S3_STORAGE` | `false` | Enable S3 storage |
| `AWS_ACCESS_KEY_ID` | - | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | - | AWS secret key |
| `AWS_REGION` | `us-east-1` | AWS region |
| `S3_BUCKET_NAME` | `swha-audio-bucket` | S3 bucket name |
| `S3_PRESIGNED_URL_EXPIRY` | `3600` | URL expiry (seconds) |

## 📄 Dependencies

- `boto3`: AWS SDK for Python
- `botocore`: Core AWS library
- Existing TTS and FastAPI dependencies

## 🚀 Future Enhancements

- [ ] Multi-region S3 support
- [ ] S3 Transfer Acceleration
- [ ] CloudFront CDN integration
- [ ] Database persistence for file metadata
- [ ] Batch presigned URL generation
- [ ] S3 lifecycle policies for automatic cleanup 