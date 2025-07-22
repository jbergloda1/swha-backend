"""
Example usage of Text-to-Speech API
"""
import requests
import json

# API Configuration
BASE_URL = "http://localhost:8000/api/v1"
# Replace with your actual access token
ACCESS_TOKEN = "your_access_token_here"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def test_tts_generate_simple():
    """Test simple TTS generation"""
    print("🎵 Testing simple TTS generation...")
    
    url = f"{BASE_URL}/tts/generate-simple"
    params = {
        "text": "Hello world! This is a test of the text-to-speech system.",
        "voice": "af_heart",
        "language_code": "a"  # American English
    }
    
    response = requests.post(url, params=params, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ TTS generation successful!")
        print(f"📁 Generated {result['total_segments']} audio segments")
        print(f"🔊 First audio URL: {result['first_audio_url']}")
        print(f"⏱️ Processing time: {result['processing_time']:.2f}s")
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def test_tts_generate_full():
    """Test full TTS generation with all parameters"""
    print("\n🎵 Testing full TTS generation...")
    
    url = f"{BASE_URL}/tts/generate"
    
    data = {
        "text": "This is a more complex text.\nIt has multiple lines.\nEach line will be a separate audio segment.",
        "voice": "af_bella",
        "language_code": "a",  # American English
        "speed": 1.2,
        "split_pattern": r"\n+"
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Full TTS generation successful!")
        print(f"📁 Generated {result['total_segments']} audio segments")
        print(f"🎭 Voice: {result['voice']}")
        print(f"🌍 Language: {result['language_code']}")
        print(f"⏱️ Processing time: {result['processing_time']:.2f}s")
        print("🔊 Audio files:")
        for i, audio_url in enumerate(result['audio_files']):
            print(f"  {i+1}. {audio_url}")
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def test_get_voices():
    """Test getting available voices"""
    print("\n🎭 Testing get available voices...")
    
    url = f"{BASE_URL}/tts/voices"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Voices retrieved successfully!")
        print(f"🎭 Available voices ({result['total_count']}):")
        for voice in result['voices']:
            print(f"  - {voice}")
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def test_get_languages():
    """Test getting supported languages"""
    print("\n🌍 Testing get supported languages...")
    
    url = f"{BASE_URL}/tts/languages"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Languages retrieved successfully!")
        print(f"🌍 Supported languages ({result['total_count']}):")
        for code, desc in result['languages'].items():
            print(f"  - {code}: {desc}")
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def test_multilingual():
    """Test TTS with different languages"""
    print("\n🌍 Testing multilingual TTS...")
    
    test_texts = [
        {"text": "Hello, how are you today?", "lang": "a", "desc": "American English"},
        {"text": "Bonjour, comment allez-vous?", "lang": "f", "desc": "French"},
        {"text": "Hola, ¿cómo estás hoy?", "lang": "e", "desc": "Spanish"},
    ]
    
    for test in test_texts:
        print(f"\n🗣️ Testing {test['desc']}...")
        
        url = f"{BASE_URL}/tts/generate-simple"
        params = {
            "text": test['text'],
            "voice": "af_heart",
            "language_code": test['lang']
        }
        
        response = requests.post(url, params=params, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {test['desc']} TTS successful!")
            print(f"🔊 Audio URL: {result['first_audio_url']}")
        else:
            print(f"❌ {test['desc']} failed: {response.status_code}")

if __name__ == "__main__":
    print("🎵 Text-to-Speech API Test Suite")
    print("=" * 50)
    
    # Make sure to replace ACCESS_TOKEN with your actual token
    if ACCESS_TOKEN == "your_access_token_here":
        print("⚠️ Please replace ACCESS_TOKEN with your actual access token!")
        print("You can get a token by logging in through /api/v1/auth/login")
        exit(1)
    
    # Run tests
    test_get_voices()
    test_get_languages()
    test_tts_generate_simple()
    test_tts_generate_full()
    test_multilingual()
    
    print("\n✅ All tests completed!")
    print("📝 Note: Audio files are saved in app/static/audio/ and accessible via /static/audio/ URLs") 