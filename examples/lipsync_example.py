"""
Example usage of Lipsync API
"""
import requests
import json
import time

# API Configuration
BASE_URL = "http://localhost:8000/api/v1"
# Replace with your actual access token
ACCESS_TOKEN = "your_access_token_here"
# Replace with your Sync.so API key
SYNC_API_KEY = "sk-te2wduQ_RSab12A3cSy3LQ.cRZ13R0e1tq-5GAskr7RwuJ0A8Z6IVIG"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def test_create_lipsync_job():
    """Test creating a lipsync job"""
    print("🎬 Testing lipsync job creation...")
    
    url = f"{BASE_URL}/lipsync/create"
    
    data = {
        "video_url": "https://drive.google.com/file/d/1oJ8xrJJIAYcOSRG8hWAOal6HhKl-RapY/view?usp=drive_link",
        "audio_url": "http://localhost:8000/static/audio/1234567890_123/segment_000.wav",  # From TTS
        "api_key": SYNC_API_KEY,
        "model": "lipsync-2",
        "sync_mode": "cut_off",
        "output_filename": "my_lipsync_video"
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Lipsync job created successfully!")
        print(f"🆔 Job ID: {result['job_id']}")
        print(f"📺 Video URL: {result['video_url']}")
        print(f"🔊 Audio URL: {result['audio_url']}")
        print(f"🤖 Model: {result['model']}")
        print(f"🔄 Sync Mode: {result['sync_mode']}")
        print(f"📅 Submitted: {result['submitted_at']}")
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def test_create_from_tts():
    """Test creating lipsync job from TTS audio"""
    print("\n🎵➡️🎬 Testing lipsync from TTS audio...")
    
    url = f"{BASE_URL}/lipsync/create-from-tts"
    
    params = {
        "video_url": "https://drive.google.com/file/d/1oJ8xrJJIAYcOSRG8hWAOal6HhKl-RapY/view?usp=drive_link",
        "tts_audio_url": "/static/audio/1234567890_123/segment_000.wav",  # Relative URL from TTS
        "api_key": SYNC_API_KEY,
        "model": "lipsync-2",
        "sync_mode": "cut_off"
    }
    
    response = requests.post(url, params=params, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Lipsync from TTS created successfully!")
        print(f"🆔 Job ID: {result['job_id']}")
        print(f"📺 Video URL: {result['video_url']}")
        print(f"🔊 Audio URL: {result['audio_url']}")
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def test_get_job_status(job_id: str):
    """Test getting job status"""
    print(f"\n📊 Testing job status for {job_id}...")
    
    url = f"{BASE_URL}/lipsync/status/{job_id}"
    params = {"api_key": SYNC_API_KEY}
    
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Job status retrieved successfully!")
        print(f"🆔 Job ID: {result['job_id']}")
        print(f"📊 Status: {result['status']}")
        if result.get('output_url'):
            print(f"🎥 Output URL: {result['output_url']}")
        if result.get('progress'):
            print(f"🔄 Progress: {result['progress']}")
        if result.get('error_message'):
            print(f"❌ Error: {result['error_message']}")
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def test_wait_for_completion(job_id: str):
    """Test waiting for job completion"""
    print(f"\n⏳ Testing wait for completion for {job_id}...")
    
    url = f"{BASE_URL}/lipsync/wait/{job_id}"
    params = {
        "api_key": SYNC_API_KEY,
        "timeout": 300,  # 5 minutes
        "poll_interval": 10  # 10 seconds
    }
    
    response = requests.post(url, params=params, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Job completed!")
        print(f"📊 Final Status: {result['status']}")
        if result.get('output_url'):
            print(f"🎥 Output URL: {result['output_url']}")
        if result.get('error_message'):
            print(f"❌ Error: {result['error_message']}")
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def test_get_models():
    """Test getting supported models"""
    print("\n🤖 Testing get supported models...")
    
    url = f"{BASE_URL}/lipsync/models"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Models retrieved successfully!")
        print(f"🤖 Available models ({result['total_count']}):")
        for model in result['models']:
            description = result['descriptions'].get(model, "No description")
            print(f"  - {model}: {description}")
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def test_get_sync_modes():
    """Test getting sync modes"""
    print("\n🔄 Testing get sync modes...")
    
    url = f"{BASE_URL}/lipsync/sync-modes"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Sync modes retrieved successfully!")
        print(f"🔄 Available sync modes ({result['total_count']}):")
        for mode in result['sync_modes']:
            description = result['descriptions'].get(mode, "No description")
            print(f"  - {mode}: {description}")
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def test_get_my_jobs():
    """Test getting user's jobs"""
    print("\n📋 Testing get my jobs...")
    
    url = f"{BASE_URL}/lipsync/jobs/my"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Jobs retrieved successfully!")
        print(f"📋 Total jobs: {result['total_count']}")
        for job in result['jobs']:
            print(f"  🆔 {job['job_id']}: {job['status']} - {job['model']}")
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def test_full_workflow():
    """Test full TTS + Lipsync workflow"""
    print("\n🔄 Testing full TTS + Lipsync workflow...")
    
    # Step 1: Generate TTS
    print("Step 1: Generate TTS audio...")
    tts_url = f"{BASE_URL}/tts/generate-simple"
    tts_params = {
        "text": "Hello! This is a test of the text-to-speech and lipsync integration.",
        "voice": "af_heart",
        "language_code": "a"
    }
    
    tts_response = requests.post(tts_url, params=tts_params, headers=headers)
    
    if tts_response.status_code != 200:
        print("❌ TTS generation failed")
        return None
    
    tts_result = tts_response.json()
    audio_url = tts_result["first_audio_url"]
    print(f"✅ TTS generated: {audio_url}")
    
    # Step 2: Create lipsync job
    print("Step 2: Create lipsync job...")
    lipsync_result = test_create_from_tts()
    
    if not lipsync_result:
        print("❌ Lipsync job creation failed")
        return None
    
    job_id = lipsync_result["job_id"]
    
    # Step 3: Poll for completion (optional - just check status once)
    print("Step 3: Check job status...")
    status_result = test_get_job_status(job_id)
    
    print("🎉 Full workflow test completed!")
    return {
        "tts_result": tts_result,
        "lipsync_result": lipsync_result,
        "status_result": status_result
    }

if __name__ == "__main__":
    print("🎬 Lipsync API Test Suite")
    print("=" * 50)
    
    # Check prerequisites
    if ACCESS_TOKEN == "your_access_token_here":
        print("⚠️ Please replace ACCESS_TOKEN with your actual access token!")
        print("You can get a token by logging in through /api/v1/auth/login")
        exit(1)
    
    if SYNC_API_KEY == "sk-te2wduQ_RSab12A3cSy3LQ.cRZ13R0e1tq-5GAskr7RwuJ0A8Z6IVIG":
        print("⚠️ Please replace SYNC_API_KEY with your actual Sync.so API key!")
        print("You can get one from https://sync.so")
        exit(1)
    
    # Run tests
    test_get_models()
    test_get_sync_modes()
    test_get_my_jobs()
    
    # Test job creation
    job_result = test_create_lipsync_job()
    if job_result:
        job_id = job_result["job_id"]
        
        # Check status immediately
        test_get_job_status(job_id)
        
        # Wait for completion (commented out to avoid long running test)
        # test_wait_for_completion(job_id)
    
    # Test TTS integration
    test_create_from_tts()
    
    # Test full workflow
    # test_full_workflow()
    
    print("\n✅ All tests completed!")
    print("📝 Note: Check job status periodically or use wait endpoint for completion") 