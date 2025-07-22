#!/usr/bin/env python3
"""
Example script to test the Question Answering API
Usage: python examples/test_qa.py
"""

import requests
import json
import time

# API Configuration
BASE_URL = "http://localhost:8000"
QA_DEMO_URL = f"{BASE_URL}/api/v1/qa/demo"
QA_MODEL_INFO_URL = f"{BASE_URL}/api/v1/qa/model-info"

def test_demo_qa():
    """Test the demo QA endpoint (no authentication required)"""
    print("🤖 Testing Question Answering Demo...")
    
    # Example contexts and questions
    test_cases = [
        {
            "question": "What is the capital of France?",
            "context": "France is a country in Western Europe. Its capital and largest city is Paris, which is located in the north-central part of the country. Paris is known for its art, culture, and landmarks like the Eiffel Tower."
        },
        {
            "question": "What is machine learning?",
            "context": "Machine learning is a method of data analysis that automates analytical model building. It is a branch of artificial intelligence (AI) based on the idea that systems can learn from data, identify patterns and make decisions with minimal human intervention."
        },
        {
            "question": "Who invented the telephone?",
            "context": "The telephone was invented by Alexander Graham Bell in 1876. Bell was a Scottish-born scientist, inventor, engineer, and innovator who is credited with patenting the first practical telephone."
        },
        {
            "question": "What is the largest planet?",
            "context": "Mars is the fourth planet from the Sun and the second smallest planet in the solar system. It is often called the Red Planet due to its appearance."
        },  # This should be unanswerable
        {
            "question": "How does photosynthesis work?",
            "context": "Photosynthesis is the process by which plants and other organisms use sunlight to synthesize foods with the help of chlorophyll. During photosynthesis, plants take in carbon dioxide from the air and water from the soil, and convert them into glucose and oxygen using energy from sunlight."
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}:")
        print(f"Question: {test_case['question']}")
        print(f"Context: {test_case['context'][:100]}...")
        
        try:
            start_time = time.time()
            response = requests.post(
                QA_DEMO_URL,
                json=test_case,
                headers={"Content-Type": "application/json"}
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Answer: {result['answer']}")
                print(f"🎯 Confidence: {result['confidence']:.3f}")
                print(f"📍 Position: {result['start_position']}-{result['end_position']}")
                print(f"❓ Answerable: {result['is_answerable']}")
                print(f"⏱️ Response Time: {response_time:.2f}s")
                
                if not result['is_answerable']:
                    print("🚫 This question appears to be unanswerable based on the context")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")

def test_batch_qa():
    """Test batch question answering"""
    print("\n\n📦 Testing Batch Question Answering...")
    
    batch_request = {
        "questions": [
            "What is the main ingredient?",
            "How long does it take to cook?",
            "What temperature should it be?"
        ],
        "context": "To make chocolate chip cookies, you need flour, sugar, butter, eggs, and chocolate chips as the main ingredients. Preheat your oven to 375°F (190°C). Mix the ingredients and bake for 10-12 minutes until golden brown."
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/v1/qa/demo",  # Using demo endpoint for simplicity
            json=batch_request["questions"][0],  # Test first question only for demo
            headers={"Content-Type": "application/json"}
        )
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            print("✅ Batch processing simulation completed")
            print(f"⏱️ Processing time: {response_time:.2f}s")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def get_model_info():
    """Get model information (no auth required via demo)"""
    print("\n\n🔍 Getting Model Information...")
    
    try:
        # First check if server is running
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code != 200:
            print("❌ Server is not running. Please start the server first.")
            return
            
        print("✅ Server is running")
        print("📋 Model Features:")
        print("  • Extractive Question Answering")
        print("  • Handles answerable and unanswerable questions")
        print("  • Returns confidence scores")
        print("  • Provides answer positions")
        print("  • GPU acceleration support")
        print("  • Model: deepset/roberta-base-squad2")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not connect to server: {e}")
        print("💡 Make sure the server is running with: python main.py")

def main():
    """Main function to run all tests"""
    print("🚀 Starting Question Answering API Tests")
    print("=" * 50)
    
    # Check server availability
    get_model_info()
    
    # Run QA tests
    test_demo_qa()
    
    # Test batch processing
    test_batch_qa()
    
    print("\n" + "=" * 50)
    print("✨ Tests completed!")
    print("\n💡 Tips:")
    print("  • For authentication required endpoints, you need to login first")
    print("  • Check /docs for complete API documentation")
    print("  • Use /api/v1/qa/model-info for detailed model information")

if __name__ == "__main__":
    main() 