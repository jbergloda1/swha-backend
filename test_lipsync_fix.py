#!/usr/bin/env python3
"""
Test script to verify lipsync status conversion fixes
"""
import sys
import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000/api/v1"
ACCESS_TOKEN = "your_access_token_here"  # Replace with actual token
SYNC_API_KEY = "sk-your_sync_api_key_here"  # Replace with actual key
TEST_JOB_ID = "test_job_id"  # Replace with actual job ID

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def test_datetime_conversion():
    """Test datetime to timestamp conversion locally"""
    print("🧪 Testing datetime conversion logic...")
    
    from app.services.lipsync_service import LipsyncService
    service = LipsyncService()
    
    # Test cases
    test_cases = [
        (None, None),
        (datetime.now(), "should_be_timestamp"),
        (1703123456.789, 1703123456.789),
        ("not_datetime", None),
    ]
    
    for input_val, expected_type in test_cases:
        result = service._convert_datetime_to_timestamp(input_val)
        print(f"  Input: {input_val} (type: {type(input_val)})")
        print(f"  Output: {result} (type: {type(result)})")
        
        if input_val is None:
            assert result is None, "None input should return None"
        elif isinstance(input_val, datetime):
            assert isinstance(result, float), "Datetime should return float timestamp"
        elif isinstance(input_val, (int, float)):
            assert isinstance(result, float), "Number should return float"
        print("  ✅ Passed\n")

def test_status_conversion():
    """Test status enum conversion"""
    print("🧪 Testing status enum conversion...")
    
    from app.api.routes.lipsync import _safe_status_conversion
    from app.schemas.lipsync import LipsyncStatus
    
    test_cases = [
        ("PENDING", LipsyncStatus.PENDING),
        ("PROCESSING", LipsyncStatus.PROCESSING),
        ("COMPLETED", LipsyncStatus.COMPLETED),
        ("FAILED", LipsyncStatus.FAILED),
        ("pending", LipsyncStatus.PENDING),
        ("completed", LipsyncStatus.COMPLETED),
        ("TIMEOUT", LipsyncStatus.FAILED),
        ("unknown_status", LipsyncStatus.PENDING),
    ]
    
    for input_status, expected in test_cases:
        result = _safe_status_conversion(input_status)
        print(f"  Input: '{input_status}' -> Output: {result}")
        assert result == expected, f"Expected {expected}, got {result}"
        print("  ✅ Passed")
    print()

def test_debug_endpoint(job_id: str):
    """Test the debug endpoint"""
    print(f"🧪 Testing debug endpoint with job ID: {job_id}")
    
    if ACCESS_TOKEN == "your_access_token_here":
        print("⚠️ Skipping API test - please set ACCESS_TOKEN")
        return
    
    if SYNC_API_KEY == "sk-your_sync_api_key_here":
        print("⚠️ Skipping API test - please set SYNC_API_KEY")
        return
    
    url = f"{BASE_URL}/lipsync/debug/status/{job_id}"
    params = {"api_key": SYNC_API_KEY}
    
    try:
        response = requests.get(url, params=params, headers=headers)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("  ✅ Debug endpoint working!")
            print(f"  Data types: {result.get('data_types', {})}")
            
            # Check if timestamps are properly converted
            raw_result = result.get('raw_result', {})
            created_at = raw_result.get('created_at')
            completed_at = raw_result.get('completed_at')
            
            if created_at is not None:
                print(f"  created_at: {created_at} (should be float)")
                assert isinstance(created_at, (int, float)) or created_at is None
            
            if completed_at is not None:
                print(f"  completed_at: {completed_at} (should be float)")
                assert isinstance(completed_at, (int, float)) or completed_at is None
                
        else:
            print(f"  ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"  ❌ Exception: {e}")

def test_regular_status_endpoint(job_id: str):
    """Test the regular status endpoint"""
    print(f"🧪 Testing regular status endpoint with job ID: {job_id}")
    
    if ACCESS_TOKEN == "your_access_token_here":
        print("⚠️ Skipping API test - please set ACCESS_TOKEN")
        return
    
    if SYNC_API_KEY == "sk-your_sync_api_key_here":
        print("⚠️ Skipping API test - please set SYNC_API_KEY")
        return
    
    url = f"{BASE_URL}/lipsync/status/{job_id}"
    params = {"api_key": SYNC_API_KEY}
    
    try:
        response = requests.get(url, params=params, headers=headers)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("  ✅ Regular endpoint working!")
            print(f"  Job status: {result.get('status')}")
            print(f"  Output URL: {result.get('output_url')}")
        else:
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"  ❌ Exception: {e}")

if __name__ == "__main__":
    print("🔧 Lipsync Status Fix Test Suite")
    print("=" * 50)
    
    # Test 1: Local conversion logic
    try:
        test_datetime_conversion()
        test_status_conversion()
        print("✅ Local tests passed!")
    except Exception as e:
        print(f"❌ Local test failed: {e}")
        sys.exit(1)
    
    # Test 2: API endpoints (if tokens are provided)
    if len(sys.argv) > 1:
        test_job_id = sys.argv[1]
        print(f"\n🌐 Testing API endpoints with job ID: {test_job_id}")
        test_debug_endpoint(test_job_id)
        test_regular_status_endpoint(test_job_id)
    else:
        print("\n💡 To test API endpoints, provide a job ID as argument:")
        print("   python test_lipsync_fix.py <job_id>")
    
    print("\n✅ Test suite completed!")
    print("\nNext steps:")
    print("1. Replace ACCESS_TOKEN and SYNC_API_KEY with real values")
    print("2. Run with a real job ID to test API endpoints")
    print("3. Check server logs for debug information") 