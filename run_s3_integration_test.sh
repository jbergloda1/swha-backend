#!/bin/bash

echo "🎵☁️ S3 Integration Test Suite"
echo "========================================"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "💡 Please create .env file from env.template and configure S3 settings"
    echo "   cp env.template .env"
    echo "   # Then edit .env with your S3 configuration"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "⚠️  No virtual environment found"
    echo "💡 Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
else
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        source .venv/bin/activate
    fi
fi

echo "✅ Virtual environment activated"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -q -r requirements.txt

# Check if S3 is configured in .env
echo "🔍 Checking S3 configuration..."
if grep -q "USE_S3_STORAGE=true" .env; then
    echo "✅ S3 storage is enabled in .env"
else
    echo "⚠️  S3 storage is not enabled in .env"
    echo "💡 To test with S3, set USE_S3_STORAGE=true in .env"
fi

# Run S3 service test
echo ""
echo "🧪 Running S3 Service Test..."
python test_s3_fix.py
s3_test_result=$?

if [ $s3_test_result -eq 0 ]; then
    echo "✅ S3 service test passed!"
else
    echo "❌ S3 service test failed"
    echo "💡 Check your S3 configuration and AWS credentials"
fi

# Run TTS S3 example test
echo ""
echo "🎵 Testing TTS with S3 integration..."
echo "💡 This would require authentication token"
echo "   To test manually: python examples/tts_s3_example.py"

# Summary
echo ""
echo "📋 Test Summary:"
echo "================================"
if [ $s3_test_result -eq 0 ]; then
    echo "✅ S3 Service: PASSED"
    echo "🎉 S3 integration is working correctly!"
    echo ""
    echo "🚀 Next steps:"
    echo "   1. Start the server: uvicorn main:app --reload"
    echo "   2. Test TTS API: python examples/tts_s3_example.py"
    echo "   3. Check /docs for API documentation"
else
    echo "❌ S3 Service: FAILED"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   1. Check your .env file S3 configuration"
    echo "   2. Verify AWS credentials are correct"
    echo "   3. Ensure S3 bucket exists and is accessible"
    echo "   4. Check AWS permissions for your IAM user"
fi

echo ""
echo "📝 For detailed S3 setup instructions, see:"
echo "   📄 S3_INTEGRATION.md"
echo "   📄 env.template" 