# 🔧 TTS Troubleshooting Guide

## Common Issues and Solutions

### 1. Permission Denied Error during Docker Build

**Error:**
```
OSError: [Errno 13] Permission denied: '/nonexistent'
ERROR: Could not install packages due to an OSError
```

**Solution:**
This occurs when spaCy models cannot be downloaded due to permission issues in Docker container.

#### Option A: Rebuild with Fixed Dockerfile
```bash
# Stop existing containers
docker-compose down

# Rebuild with no cache
docker-compose build --no-cache

# Start services
docker-compose up -d
```

#### Option B: Manual Model Download
```bash
# Access the running container
docker-compose exec app bash

# Install spaCy models manually
python -m spacy download en_core_web_sm
python -m spacy download en_core_web_md

# Restart the service
docker-compose restart app
```

### 2. TTS Pipeline Initialization Fails

**Error:**
```
Exception in ASGI application
File "/app/app/services/tts_service.py", line 34, in _get_pipeline
SystemExit: 1
```

**Solution:**

#### Check Model Availability
```bash
# Check if models are available
docker-compose exec app python -c "
import spacy
try:
    nlp = spacy.load('en_core_web_sm')
    print('✅ en_core_web_sm is available')
except:
    print('❌ en_core_web_sm is missing')

try:
    nlp = spacy.load('en_core_web_md')
    print('✅ en_core_web_md is available')
except:
    print('❌ en_core_web_md is missing')
"
```

#### Manual Model Initialization
```bash
# Run the initialization script manually
docker-compose exec app python init_models.py
```

### 3. Cache Directory Issues

**Error:**
```
PermissionError: [Errno 13] Permission denied: '/home/app/.cache/spacy'
```

**Solution:**
```bash
# Fix cache directory permissions
docker-compose exec --user root app bash -c "
mkdir -p /home/app/.cache/spacy
chown -R app:app /home/app/.cache
chmod -R 755 /home/app/.cache
"

# Restart service
docker-compose restart app
```

### 4. Memory Issues During Model Loading

**Error:**
```
RuntimeError: CUDA out of memory
MemoryError: Unable to allocate memory
```

**Solution:**
```bash
# Check container memory usage
docker stats

# Increase Docker memory limit (Docker Desktop)
# Settings -> Resources -> Memory -> Increase to 4GB+

# Or disable GPU and use CPU only
# Add to .env file:
FORCE_CPU=true
```

### 5. Network Issues During Model Download

**Error:**
```
requests.exceptions.ConnectionError
HTTPSConnectionPool: Max retries exceeded
```

**Solution:**
```bash
# Check internet connectivity in container
docker-compose exec app ping google.com

# Try downloading models manually with specific timeout
docker-compose exec app python -c "
import subprocess
import sys

models = ['en_core_web_sm', 'en_core_web_md']
for model in models:
    try:
        result = subprocess.run([sys.executable, '-m', 'spacy', 'download', model], 
                              timeout=300, capture_output=True, text=True)
        print(f'{model}: {result.returncode}')
        if result.stderr:
            print(f'Error: {result.stderr}')
    except subprocess.TimeoutExpired:
        print(f'{model}: Download timeout')
"
```

## 🔍 Diagnostic Commands

### Check TTS Service Status
```bash
# Test TTS endpoint
curl -X POST "http://localhost:8000/api/v1/tts/generate-simple" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "text=Hello world&voice=af_heart&language_code=a"
```

### Check Available Models
```bash
# List installed spaCy models
docker-compose exec app python -c "
import spacy
import spacy.util
import os

print('Installed spaCy models:')
for model in spacy.util.get_installed_models():
    print(f'  ✅ {model}')

print(f'spaCy data path: {spacy.util.get_data_path()}')
print(f'SPACY_DATA env: {os.environ.get(\"SPACY_DATA\", \"Not set\")}')
"
```

### Check Kokoro Installation
```bash
# Test Kokoro import
docker-compose exec app python -c "
try:
    from kokoro import KPipeline
    print('✅ Kokoro library imported successfully')
    
    # Test pipeline creation (this might fail if models aren't ready)
    try:
        pipeline = KPipeline(lang_code='a')
        print('✅ Kokoro pipeline created successfully')
    except Exception as e:
        print(f'❌ Kokoro pipeline creation failed: {e}')
        
except ImportError as e:
    print(f'❌ Kokoro library not found: {e}')
"
```

## 🚀 Quick Fixes

### Complete Reset
```bash
# Nuclear option: rebuild everything
docker-compose down -v
docker system prune -a
docker-compose build --no-cache
docker-compose up -d
```

### Development Mode (Local Testing)
```bash
# Test locally without Docker
python -m venv tts-test-env
source tts-test-env/bin/activate
pip install kokoro>=0.9.4 spacy
python -m spacy download en_core_web_sm
python -m spacy download en_core_web_md

# Test TTS
python -c "
from kokoro import KPipeline
pipeline = KPipeline(lang_code='a')
print('✅ Local TTS test successful')
"
```

### Alternative spaCy Model Download
```bash
# If automatic download fails, try manual download
docker-compose exec app bash -c "
pip install -U spacy[lookups]
python -m spacy download en_core_web_sm --direct
python -m spacy download en_core_web_md --direct
"
```

## 📞 Support

If issues persist:

1. **Check logs**: `docker-compose logs app`
2. **Check container resources**: `docker stats`
3. **Try manual initialization**: `docker-compose exec app python init_models.py`
4. **Report the issue** with:
   - Docker logs
   - System specifications
   - Error messages
   - Steps to reproduce

## 🔄 Workaround for Development

If TTS is not critical for your development:

```python
# Temporary disable TTS in development
# Add to .env:
DISABLE_TTS=true

# Or modify tts_service.py to return mock responses
```

## ✅ Prevention

To avoid these issues in the future:

1. **Use the provided `init_models.py` script**
2. **Ensure sufficient Docker memory allocation (4GB+)**
3. **Check internet connectivity during Docker build**
4. **Monitor cache directory permissions**
5. **Keep dependencies updated**

```bash
# Regular maintenance
docker-compose exec app pip list --outdated
docker system prune -f
``` 