"""
Example usage of TTS API with S3 presigned URLs
"""
import requests
import json
import time
from datetime import datetime

# API Configuration
BASE_URL = "http://localhost:8000/api/v1"
# Replace with your actual access token
ACCESS_TOKEN = "your_access_token_here"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def test_s3_info():
    """Test S3 configuration endpoint"""
    print("🔍 Testing S3 configuration...")
    
    url = f"{BASE_URL}/tts/s3-info"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ S3 info retrieved successfully!")
        print(f"📊 S3 Enabled: {result['s3_enabled']}")
        print(f"🪣 Bucket: {result.get('bucket_name', 'Not configured')}")
        print(f"🌍 Region: {result.get('region', 'Not configured')}")
        print(f"⏱️ Default Expiry: {result['default_expiry']} seconds")
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def test_tts_with_s3():
    """Test TTS generation with S3 storage"""
    print("\n🎵 Testing TTS with S3 storage...")
    
    url = f"{BASE_URL}/tts/generate"
    
    data = {
        "text": "Hello! This is a test of TTS with S3 presigned URLs. The audio will be stored in AWS S3 and accessible via presigned URLs.",
        "voice": "af_heart",
        "language_code": "a",
        "speed": 1.0,
        "split_pattern": r"\.\s+",
        "use_s3": True,
        "presigned_url_expiry": 7200  # 2 hours
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ TTS with S3 generation successful!")
        print(f"📁 Generated {result['total_segments']} audio segments")
        print(f"🏪 Storage Type: {result['storage_type']}")
        print(f"🆔 Session ID: {result['session_id']}")
        print(f"⏱️ Processing time: {result['processing_time']:.2f}s")
        
        if result.get('expires_at'):
            expires_datetime = datetime.fromtimestamp(result['expires_at'])
            print(f"⏰ URLs expire at: {expires_datetime}")
        
        print("\n🔊 Generated Audio Files:")
        for i, audio_url in enumerate(result['audio_files']):
            url_type = "🔗 Presigned S3" if "amazonaws.com" in audio_url else "📁 Local"
            print(f"  {i+1}. {url_type}: {audio_url[:80]}...")
        
        print("\n📋 Audio Segments Detail:")
        for segment in result['audio_segments']:
            print(f"  Segment {segment['index']}:")
            print(f"    Text: {segment['graphemes'][:50]}...")
            if segment.get('presigned_url'):
                print(f"    S3 URL: {segment['presigned_url'][:80]}...")
                print(f"    S3 Key: {segment.get('s3_key', 'N/A')}")
            if segment.get('local_url'):
                print(f"    Local URL: {segment['local_url']}")
        
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def test_tts_local_fallback():
    """Test TTS generation with local storage (S3 disabled)"""
    print("\n📁 Testing TTS with local storage fallback...")
    
    url = f"{BASE_URL}/tts/generate-simple"
    
    params = {
        "text": "This is a test with local storage fallback when S3 is disabled.",
        "voice": "af_bella",
        "language_code": "a",
        "use_s3": False  # Force local storage
    }
    
    response = requests.post(url, params=params, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ TTS with local storage successful!")
        print(f"🏪 Storage Type: {result['storage_type']}")
        print(f"📁 First Audio URL: {result['first_audio_url']}")
        print(f"⏱️ Processing time: {result['processing_time']:.2f}s")
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def test_lipsync_with_presigned_url(presigned_url: str):
    """Test lipsync creation using presigned URL from TTS"""
    print(f"\n🎬 Testing lipsync with presigned URL...")
    
    # This would require actual Sync.so API key and video URL
    # Just showing the request structure
    
    url = f"{BASE_URL}/lipsync/create-from-tts"
    
    params = {
        "video_url": "https://example.com/test-video.mp4",  # Replace with actual video
        "tts_audio_url": presigned_url,
        "api_key": "sk-your_sync_api_key_here",  # Replace with actual key
        "model": "lipsync-2",
        "sync_mode": "cut_off"
    }
    
    print(f"📝 Would create lipsync job with:")
    print(f"  🎥 Video: {params['video_url']}")
    print(f"  🔊 Audio: {presigned_url[:80]}...")
    print(f"  🤖 Model: {params['model']}")
    
    # Uncomment to actually test (requires valid API key and video URL)
    # response = requests.post(url, params=params, headers=headers)
    # if response.status_code == 200:
    #     result = response.json()
    #     print("✅ Lipsync job created with presigned URL!")
    #     return result
    # else:
    #     print(f"❌ Error: {response.status_code}")
    #     return None
    
    print("💡 Uncomment the request code to actually test lipsync")

def test_cleanup_with_s3():
    """Test cleanup functionality for both local and S3 files"""
    print("\n🧹 Testing cleanup with S3...")
    
    url = f"{BASE_URL}/tts/cleanup"
    
    params = {
        "days_old": 1,  # Clean files older than 1 day for testing
        "cleanup_s3": True
    }
    
    response = requests.post(url, params=params, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Cleanup completed!")
        print(f"📁 Local files cleaned: {result['local_files_cleaned']}")
        print(f"☁️ S3 files cleaned: {result['s3_files_cleaned']}")
        if result.get('s3_cleanup_error'):
            print(f"⚠️ S3 cleanup error: {result['s3_cleanup_error']}")
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def test_url_accessibility(url: str):
    """Test if a presigned URL is accessible"""
    print(f"\n🔗 Testing URL accessibility...")
    print(f"URL: {url[:80]}...")
    
    try:
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            print("✅ URL is accessible!")
            print(f"📊 Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
            print(f"📏 Content-Length: {response.headers.get('Content-Length', 'Unknown')} bytes")
            return True
        else:
            print(f"❌ URL not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing URL: {str(e)}")
        return False

if __name__ == "__main__":
    print("🎵☁️ TTS + S3 Integration Test Suite")
    print("=" * 60)
    
    # Check prerequisites
    if ACCESS_TOKEN == "your_access_token_here":
        print("⚠️ Please replace ACCESS_TOKEN with your actual access token!")
        print("You can get a token by logging in through /api/v1/auth/login")
        exit(1)
    
    # Test 1: Check S3 configuration
    s3_info = test_s3_info()
    
    # Test 2: TTS with S3 (if enabled)
    if s3_info and s3_info.get('s3_enabled'):
        print("\n✅ S3 is enabled, testing S3 storage...")
        tts_result = test_tts_with_s3()
        
        if tts_result and tts_result['audio_files']:
            # Test URL accessibility
            first_url = tts_result['audio_files'][0]
            test_url_accessibility(first_url)
            
            # Test lipsync integration
            test_lipsync_with_presigned_url(first_url)
    else:
        print("\n⚠️ S3 is not enabled, testing local storage fallback...")
        test_tts_local_fallback()
    
    # Test 3: Local storage fallback
    test_tts_local_fallback()
    
    # Test 4: Cleanup
    test_cleanup_with_s3()
    
    print("\n✅ All tests completed!")
    print("\n📝 Notes:")
    print("- Presigned URLs have expiration times")
    print("- S3 storage requires proper AWS configuration")
    print("- Local storage is used as fallback when S3 is unavailable")
    print("- Check server logs for detailed S3 operation information") 