#!/usr/bin/env python3
"""
Quick test script to verify S3 upload fix
"""
import os
import sys
import tempfile
import time
import numpy as np
import soundfile as sf

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings
from app.services.s3_service import get_s3_service

def create_test_audio_file():
    """Create a test audio file for upload testing."""
    # Generate 1 second of sine wave audio
    sample_rate = 24000
    duration = 1.0
    frequency = 440  # A note
    
    # Generate audio samples
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio = np.sin(2 * np.pi * frequency * t)
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        sf.write(f.name, audio, sample_rate)
        return f.name

def test_s3_service():
    """Test S3 service functionality."""
    print("🧪 Testing S3 Service Fix")
    print("=" * 50)
    
    # Check S3 configuration
    print(f"✅ S3 Enabled: {settings.s3_enabled}")
    print(f"🪣 Bucket: {settings.S3_BUCKET_NAME}")
    print(f"🌍 Region: {settings.AWS_REGION}")
    print(f"🔑 Has Access Key: {bool(settings.AWS_ACCESS_KEY_ID)}")
    print(f"🗝️ Has Secret Key: {bool(settings.AWS_SECRET_ACCESS_KEY)}")
    
    if not settings.s3_enabled:
        print("❌ S3 is not enabled or configured")
        print("💡 To enable S3:")
        print("   1. Set USE_S3_STORAGE=true in .env")
        print("   2. Configure AWS credentials in .env")
        return False
    
    # Get S3 service
    s3_service = get_s3_service()
    if not s3_service:
        print("❌ Failed to get S3 service")
        return False
    
    print("✅ S3 service initialized")
    
    # Test bucket access
    print("\n🔍 Testing bucket access...")
    if not s3_service.check_bucket_exists():
        print("❌ S3 bucket is not accessible")
        return False
    
    print("✅ S3 bucket is accessible")
    
    # Test file upload
    print("\n📤 Testing file upload...")
    test_file = create_test_audio_file()
    
    try:
        # Create test S3 key
        timestamp = int(time.time() * 1000)
        s3_key = f"test-uploads/test_audio_{timestamp}.wav"
        
        # Test metadata
        metadata = {
            "test": "true",
            "timestamp": str(timestamp),
            "source": "s3_test_script"
        }
        
        # Upload file
        upload_success = s3_service.upload_audio_file(
            file_path=test_file,
            s3_key=s3_key,
            metadata=metadata
        )
        
        if not upload_success:
            print("❌ File upload failed")
            return False
        
        print("✅ File uploaded successfully")
        
        # Test presigned URL generation
        print("\n🔗 Testing presigned URL generation...")
        presigned_url = s3_service.generate_presigned_url(s3_key, expiry_seconds=300)
        
        if not presigned_url:
            print("❌ Presigned URL generation failed")
            return False
        
        print("✅ Presigned URL generated successfully")
        print(f"🔗 URL: {presigned_url[:80]}...")
        
        # Test file info
        print("\n📊 Testing file info retrieval...")
        file_info = s3_service.get_file_info(s3_key)
        
        if not file_info:
            print("❌ File info retrieval failed")
        else:
            print("✅ File info retrieved successfully")
            print(f"📏 Size: {file_info.get('size')} bytes")
            print(f"📅 Content Type: {file_info.get('content_type')}")
            print(f"🏷️ Metadata: {file_info.get('metadata', {})}")
        
        # Cleanup test file from S3
        print("\n🧹 Cleaning up test file...")
        delete_success = s3_service.delete_audio_file(s3_key)
        
        if delete_success:
            print("✅ Test file deleted from S3")
        else:
            print("⚠️ Failed to delete test file")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        return False
    
    finally:
        # Cleanup local test file
        try:
            os.unlink(test_file)
            print("✅ Local test file cleaned up")
        except Exception as e:
            print(f"⚠️ Failed to cleanup local test file: {e}")

def test_upload_and_presigned_url():
    """Test the combined upload and presigned URL method."""
    print("\n🔄 Testing combined upload and presigned URL...")
    
    s3_service = get_s3_service()
    if not s3_service:
        return False
    
    test_file = create_test_audio_file()
    
    try:
        timestamp = int(time.time() * 1000)
        s3_key = f"test-combined/test_audio_{timestamp}.wav"
        
        metadata = {
            "test_type": "combined",
            "timestamp": str(timestamp)
        }
        
        # Test combined method
        presigned_url = s3_service.upload_and_get_presigned_url(
            file_path=test_file,
            s3_key=s3_key,
            metadata=metadata,
            expiry_seconds=600
        )
        
        if not presigned_url:
            print("❌ Combined upload and presigned URL failed")
            return False
        
        print("✅ Combined upload and presigned URL successful")
        print(f"🔗 URL: {presigned_url[:80]}...")
        
        # Cleanup
        s3_service.delete_audio_file(s3_key)
        return True
        
    except Exception as e:
        print(f"❌ Error in combined test: {str(e)}")
        return False
    
    finally:
        try:
            os.unlink(test_file)
        except:
            pass

if __name__ == "__main__":
    print("🎵☁️ S3 Integration Fix Test")
    print("=" * 60)
    
    try:
        # Test basic S3 service
        basic_test_passed = test_s3_service()
        
        if basic_test_passed:
            # Test combined method
            combined_test_passed = test_upload_and_presigned_url()
            
            if combined_test_passed:
                print("\n🎉 All S3 tests passed!")
                print("✅ The S3 upload fix is working correctly")
            else:
                print("\n⚠️ Basic tests passed but combined test failed")
        else:
            print("\n❌ Basic S3 tests failed")
            print("💡 Check your S3 configuration and AWS credentials")
    
    except Exception as e:
        print(f"\n💥 Test script error: {str(e)}")
        sys.exit(1)
    
    print("\n📝 Note: If tests failed due to missing credentials,")
    print("set up your .env file with proper S3 configuration.") 