"""
Complete TTS + Lipsync Workflow Example
This demonstrates the full pipeline: Text -> Speech -> Lip Sync Video
"""
import requests
import json
import time

# API Configuration
BASE_URL = "http://localhost:8000/api/v1"
ACCESS_TOKEN = "your_access_token_here"
SYNC_API_KEY = "sk-your_sync_api_key_here"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def complete_workflow_example():
    """Complete example of Text-to-Speech + Lipsync workflow"""
    print("🚀 Starting Complete TTS + Lipsync Workflow")
    print("=" * 60)
    
    # Configuration
    text_to_speak = """
    Hello there! Welcome to our advanced Text-to-Speech and Lip Sync demonstration.
    This technology can convert any text into natural speech and then synchronize it with video.
    The possibilities are endless for content creation, education, and entertainment.
    """
    
    video_url = "https://drive.google.com/file/d/1oJ8xrJJIAYcOSRG8hWAOal6HhKl-RapY/view?usp=drive_link"
    voice = "af_heart"
    language_code = "a"  # American English
    
    print(f"📝 Text: {text_to_speak[:100]}...")
    print(f"🎭 Voice: {voice}")
    print(f"🌍 Language: {language_code}")
    print(f"📺 Video URL: {video_url}")
    
    # Step 1: Generate TTS Audio
    print("\n🎵 STEP 1: Generating Text-to-Speech Audio...")
    print("-" * 40)
    
    tts_url = f"{BASE_URL}/tts/generate"
    tts_data = {
        "text": text_to_speak,
        "voice": voice,
        "language_code": language_code,
        "speed": 1.0,
        "split_pattern": r"\.\s+"  # Split on sentences
    }
    
    print("Sending TTS request...")
    tts_response = requests.post(tts_url, json=tts_data, headers=headers)
    
    if tts_response.status_code != 200:
        print(f"❌ TTS failed: {tts_response.status_code}")
        print(tts_response.text)
        return None
    
    tts_result = tts_response.json()
    print(f"✅ TTS completed successfully!")
    print(f"📁 Generated {tts_result['total_segments']} audio segments")
    print(f"⏱️ Processing time: {tts_result['processing_time']:.2f}s")
    print(f"🔊 Audio files:")
    for i, audio_file in enumerate(tts_result['audio_files']):
        print(f"  {i+1}. {audio_file}")
    
    # Use the first audio segment for lipsync
    first_audio_url = tts_result['audio_files'][0]
    print(f"\n🎯 Using audio file: {first_audio_url}")
    
    # Step 2: Create Lipsync Job
    print("\n🎬 STEP 2: Creating Lipsync Job...")
    print("-" * 40)
    
    lipsync_url = f"{BASE_URL}/lipsync/create-from-tts"
    lipsync_params = {
        "video_url": video_url,
        "tts_audio_url": first_audio_url,
        "api_key": SYNC_API_KEY,
        "model": "lipsync-2",
        "sync_mode": "cut_off"
    }
    
    print("Sending lipsync request...")
    lipsync_response = requests.post(lipsync_url, params=lipsync_params, headers=headers)
    
    if lipsync_response.status_code != 200:
        print(f"❌ Lipsync job creation failed: {lipsync_response.status_code}")
        print(lipsync_response.text)
        return None
    
    lipsync_result = lipsync_response.json()
    job_id = lipsync_result["job_id"]
    
    print(f"✅ Lipsync job created successfully!")
    print(f"🆔 Job ID: {job_id}")
    print(f"📊 Status: {lipsync_result['status']}")
    print(f"🤖 Model: {lipsync_result['model']}")
    print(f"🔄 Sync Mode: {lipsync_result['sync_mode']}")
    
    # Step 3: Monitor Job Progress
    print("\n📊 STEP 3: Monitoring Job Progress...")
    print("-" * 40)
    
    max_attempts = 30  # Maximum polling attempts
    poll_interval = 10  # seconds
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"🔍 Checking status (attempt {attempt}/{max_attempts})...")
        
        status_url = f"{BASE_URL}/lipsync/status/{job_id}"
        status_response = requests.get(status_url, params={"api_key": SYNC_API_KEY}, headers=headers)
        
        if status_response.status_code != 200:
            print(f"❌ Status check failed: {status_response.status_code}")
            break
        
        status_result = status_response.json()
        job_status = status_result["status"]
        
        print(f"📊 Status: {job_status}")
        
        if status_result.get("progress"):
            print(f"🔄 Progress: {status_result['progress']}%")
        
        if job_status == "COMPLETED":
            print(f"🎉 Job completed successfully!")
            if status_result.get("output_url"):
                print(f"🎥 Output video URL: {status_result['output_url']}")
            break
        elif job_status == "FAILED":
            print(f"❌ Job failed!")
            if status_result.get("error_message"):
                print(f"🔍 Error: {status_result['error_message']}")
            break
        elif job_status in ["PENDING", "PROCESSING"]:
            print(f"⏳ Job still processing... waiting {poll_interval}s")
            time.sleep(poll_interval)
        else:
            print(f"❓ Unknown status: {job_status}")
            break
    
    if attempt >= max_attempts:
        print(f"⏰ Timeout: Job didn't complete within {max_attempts * poll_interval} seconds")
    
    # Step 4: Summary
    print("\n📋 WORKFLOW SUMMARY")
    print("=" * 40)
    print(f"📝 Original text length: {len(text_to_speak)} characters")
    print(f"🎵 TTS segments generated: {tts_result['total_segments']}")
    print(f"⏱️ TTS processing time: {tts_result['processing_time']:.2f}s")
    print(f"🆔 Lipsync job ID: {job_id}")
    print(f"📊 Final status: {status_result.get('status', 'Unknown')}")
    
    if status_result.get("output_url"):
        print(f"✅ Success! Output video: {status_result['output_url']}")
    
    return {
        "tts_result": tts_result,
        "lipsync_job_id": job_id,
        "final_status": status_result
    }

def batch_workflow_example():
    """Example of processing multiple texts in batch"""
    print("\n🔄 BATCH WORKFLOW EXAMPLE")
    print("=" * 40)
    
    # Multiple texts to process
    texts_and_videos = [
        {
            "text": "Welcome to our company! We're excited to have you here.",
            "video": "https://example.com/welcome_video.mp4",
            "voice": "af_heart"
        },
        {
            "text": "Thank you for your purchase. Your order is being processed.",
            "video": "https://example.com/thank_you_video.mp4", 
            "voice": "af_bella"
        },
        {
            "text": "Don't forget to subscribe and hit the bell icon for notifications!",
            "video": "https://example.com/subscribe_video.mp4",
            "voice": "am_adam"
        }
    ]
    
    job_ids = []
    
    for i, item in enumerate(texts_and_videos, 1):
        print(f"\n📝 Processing item {i}/{len(texts_and_videos)}")
        print(f"Text: {item['text'][:50]}...")
        print(f"Voice: {item['voice']}")
        
        # Generate TTS
        tts_response = requests.post(f"{BASE_URL}/tts/generate-simple", params={
            "text": item["text"],
            "voice": item["voice"],
            "language_code": "a"
        }, headers=headers)
        
        if tts_response.status_code != 200:
            print(f"❌ TTS failed for item {i}")
            continue
        
        tts_result = tts_response.json()
        audio_url = tts_result["first_audio_url"]
        print(f"✅ TTS generated: {audio_url}")
        
        # Create lipsync job
        lipsync_response = requests.post(f"{BASE_URL}/lipsync/create-from-tts", params={
            "video_url": item["video"],
            "tts_audio_url": audio_url,
            "api_key": SYNC_API_KEY,
            "model": "lipsync-2"
        }, headers=headers)
        
        if lipsync_response.status_code != 200:
            print(f"❌ Lipsync failed for item {i}")
            continue
        
        lipsync_result = lipsync_response.json()
        job_id = lipsync_result["job_id"]
        job_ids.append(job_id)
        print(f"✅ Lipsync job created: {job_id}")
    
    print(f"\n📊 Batch Summary: {len(job_ids)} jobs created")
    print("Job IDs:", job_ids)
    
    # Check status of all jobs
    print("\n🔍 Checking status of all jobs...")
    for job_id in job_ids:
        status_response = requests.get(f"{BASE_URL}/lipsync/status/{job_id}", 
                                     params={"api_key": SYNC_API_KEY}, headers=headers)
        if status_response.status_code == 200:
            status = status_response.json()["status"]
            print(f"Job {job_id}: {status}")

def test_api_info():
    """Test getting API information"""
    print("\n🔍 API INFORMATION")
    print("=" * 30)
    
    # Get TTS voices
    print("🎭 Available TTS voices:")
    voices_response = requests.get(f"{BASE_URL}/tts/voices", headers=headers)
    if voices_response.status_code == 200:
        voices = voices_response.json()["voices"]
        for voice in voices:
            print(f"  - {voice}")
    
    # Get TTS languages
    print("\n🌍 Available TTS languages:")
    langs_response = requests.get(f"{BASE_URL}/tts/languages", headers=headers)
    if langs_response.status_code == 200:
        languages = langs_response.json()["languages"]
        for code, desc in languages.items():
            print(f"  - {code}: {desc}")
    
    # Get lipsync models
    print("\n🤖 Available lipsync models:")
    models_response = requests.get(f"{BASE_URL}/lipsync/models", headers=headers)
    if models_response.status_code == 200:
        models = models_response.json()
        for model in models["models"]:
            desc = models["descriptions"].get(model, "")
            print(f"  - {model}: {desc}")
    
    # Get sync modes
    print("\n🔄 Available sync modes:")
    sync_modes_response = requests.get(f"{BASE_URL}/lipsync/sync-modes", headers=headers)
    if sync_modes_response.status_code == 200:
        sync_modes = sync_modes_response.json()
        for mode in sync_modes["sync_modes"]:
            desc = sync_modes["descriptions"].get(mode, "")
            print(f"  - {mode}: {desc}")

if __name__ == "__main__":
    print("🎬🎵 TTS + Lipsync Complete Workflow Test")
    print("=" * 60)
    
    # Check prerequisites
    if ACCESS_TOKEN == "your_access_token_here":
        print("⚠️ Please replace ACCESS_TOKEN with your actual access token!")
        exit(1)
    
    if SYNC_API_KEY == "sk-your_sync_api_key_here":
        print("⚠️ Please replace SYNC_API_KEY with your actual Sync.so API key!")
        exit(1)
    
    # Test API information first
    test_api_info()
    
    # Ask user what to run
    print("\n🤔 What would you like to test?")
    print("1. Complete single workflow (Text -> TTS -> Lipsync)")
    print("2. Batch processing example")
    print("3. Both")
    
    try:
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice in ["1", "3"]:
            print("\n" + "="*60)
            result = complete_workflow_example()
            
        if choice in ["2", "3"]:
            print("\n" + "="*60)
            batch_workflow_example()
            
        if choice not in ["1", "2", "3"]:
            print("Invalid choice. Running complete workflow by default.")
            complete_workflow_example()
            
    except KeyboardInterrupt:
        print("\n\n👋 Workflow interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    print("\n✅ Workflow test completed!")
    print("📝 Check the API docs at /docs for more information") 