# 🎵 Text-to-Speech API Documentation

## Overview

The Text-to-Speech (TTS) API provides powerful voice synthesis capabilities using the Kokoro library. Convert text to natural-sounding speech in multiple languages and voices.

## 🚀 Quick Start

### 1. Install Dependencies

First, install system dependencies:
```bash
./install_dependencies.sh
```

Then install Python dependencies:
```bash
pip install -r requirements.txt
```

### 2. Start the Server

```bash
python main.py
```

### 3. Test the API

```bash
python examples/tts_example.py
```

## 📋 API Endpoints

### Base URL: `/api/v1/tts`

All endpoints require authentication. Include your Bearer token in the Authorization header.

### 1. Generate Speech (Simple)

**POST** `/generate-simple`

Quick endpoint for basic TTS generation.

**Parameters:**
- `text` (string, required): Text to convert to speech
- `voice` (string, optional): Voice type (default: "af_heart")
- `language_code` (string, optional): Language code (default: "a")

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/tts/generate-simple" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "text=Hello world!&voice=af_heart&language_code=a"
```

### 2. Generate Speech (Full)

**POST** `/generate`

Full-featured endpoint with all TTS options.

**Request Body:**
```json
{
  "text": "Hello world!\nThis is line two.",
  "voice": "af_heart",
  "language_code": "a",
  "speed": 1.0,
  "split_pattern": "\\n+"
}
```

**Response:**
```json
{
  "message": "Speech generated successfully",
  "audio_files": [
    "/static/audio/1234567890_123/segment_000.wav",
    "/static/audio/1234567890_123/segment_001.wav"
  ],
  "total_segments": 2,
  "language_code": "a",
  "voice": "af_heart",
  "processing_time": 1.23
}
```

### 3. Get Available Voices

**GET** `/voices`

Returns list of available voice types.

**Response:**
```json
{
  "voices": [
    "af_heart",
    "af_bella",
    "af_sarah",
    "af_nicole",
    "am_adam",
    "am_michael"
  ],
  "total_count": 6
}
```

### 4. Get Supported Languages

**GET** `/languages`

Returns supported language codes and descriptions.

**Response:**
```json
{
  "languages": {
    "a": "American English 🇺🇸",
    "b": "British English 🇬🇧",
    "e": "Spanish 🇪🇸",
    "f": "French 🇫🇷",
    "h": "Hindi 🇮🇳",
    "i": "Italian 🇮🇹",
    "j": "Japanese 🇯🇵",
    "p": "Brazilian Portuguese 🇧🇷",
    "z": "Mandarin Chinese 🇨🇳"
  },
  "total_count": 9
}
```

### 5. Cleanup Audio Files

**POST** `/cleanup`

Remove audio files older than specified days.

**Parameters:**
- `days_old` (integer, optional): Days threshold (default: 7)

## 🌍 Language Codes

| Code | Language | Flag |
|------|----------|------|
| `a` | American English | 🇺🇸 |
| `b` | British English | 🇬🇧 |
| `e` | Spanish | 🇪🇸 |
| `f` | French | 🇫🇷 |
| `h` | Hindi | 🇮🇳 |
| `i` | Italian | 🇮🇹 |
| `j` | Japanese* | 🇯🇵 |
| `p` | Brazilian Portuguese | 🇧🇷 |
| `z` | Mandarin Chinese* | 🇨🇳 |

*Japanese and Chinese require additional packages: `pip install misaki[ja]` or `pip install misaki[zh]`

## 🎭 Voice Types

- `af_heart` - Female, warm tone (default)
- `af_bella` - Female, elegant
- `af_sarah` - Female, professional
- `af_nicole` - Female, friendly
- `am_adam` - Male, confident
- `am_michael` - Male, professional

## 🔧 Configuration Options

### Speed Control
Control speech speed with the `speed` parameter:
- `0.5` - Very slow
- `1.0` - Normal speed (default)
- `1.5` - Fast
- `2.0` - Very fast

### Text Splitting
Use `split_pattern` to control how text is segmented:
- `\\n+` - Split on line breaks (default)
- `\\. ` - Split on sentences
- `\\. |\\! |\\? ` - Split on sentence endings
- Custom regex patterns

## 📁 File Management

Generated audio files are stored in `/app/static/audio/` with the following structure:
```
app/static/audio/
├── {timestamp}_{user_id}/
│   ├── segment_000.wav
│   ├── segment_001.wav
│   └── ...
└── .gitkeep
```

Files are accessible via URLs like: `/static/audio/{session_id}/{filename}`

## 🔒 Authentication

All endpoints require authentication. Include your Bearer token:

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

Common error responses:

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Error generating speech: [specific error message]"
}
```

## 📝 Example Integration

### Python
```python
import requests

headers = {"Authorization": "Bearer YOUR_TOKEN"}

# Simple generation
response = requests.post(
    "http://localhost:8000/api/v1/tts/generate-simple",
    params={
        "text": "Hello, this is a test!",
        "voice": "af_heart",
        "language_code": "a"
    },
    headers=headers
)

result = response.json()
audio_url = result["first_audio_url"]
print(f"Audio available at: {audio_url}")
```

### JavaScript
```javascript
const headers = {
    'Authorization': 'Bearer YOUR_TOKEN',
    'Content-Type': 'application/json'
};

const response = await fetch('/api/v1/tts/generate', {
    method: 'POST',
    headers: headers,
    body: JSON.stringify({
        text: "Hello world!",
        voice: "af_heart",
        language_code: "a"
    })
});

const result = await response.json();
console.log('Audio files:', result.audio_files);
```

## 🔧 Troubleshooting

### Common Issues

1. **espeak-ng not found**
   ```bash
   sudo apt-get install espeak-ng
   ```

2. **Audio files not accessible**
   - Check that `/app/static/audio/` directory exists
   - Verify static file serving is configured correctly

3. **Language not supported**
   - Check language code against supported list
   - Install additional language packages if needed

4. **Memory issues**
   - Monitor RAM usage during generation
   - Consider cleanup of old files
   - Use shorter text segments

### Performance Tips

- Cache TTS pipelines for frequently used languages
- Use appropriate `split_pattern` for your text
- Cleanup old audio files regularly
- Monitor disk space usage

## 🤝 Contributing

To add new voices or languages:

1. Update `TTSService.get_available_voices()`
2. Update `TTSService.get_supported_languages()`
3. Add corresponding language codes to schema
4. Test with example texts

## 📄 License

This TTS integration uses the Kokoro library. Check Kokoro's license for usage terms. 