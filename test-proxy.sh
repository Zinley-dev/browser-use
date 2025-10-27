#!/bin/bash

echo "========================================"
echo "🧪 Browser-Use with SnowX API Proxy Test"
echo "========================================"
echo ""

# Check if backend is running
echo "🔍 Checking if backend is running..."
if curl -s -f http://localhost:3000/api/browser-use/o3/v1/chat/completions \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"messages":[{"role":"user","content":"test"}],"max_completion_tokens":10}' > /dev/null 2>&1; then
    echo "✅ Backend is running on http://localhost:3000"
else
    echo "❌ Backend is NOT running!"
    echo ""
    echo "Please start the backend first:"
    echo "  cd /Users/khoinguyen/Desktop/snowx-api-v2"
    echo "  npm run dev"
    echo ""
    exit 1
fi

echo ""
echo "========================================"
echo "🚀 Running browser automation test..."
echo "========================================"
echo ""

# Kill any existing Chrome processes
echo "🧹 Cleaning up existing Chrome processes..."
killall -9 "Google Chrome" 2>/dev/null || true
sleep 2

# Run the test
cd /Users/khoinguyen/Desktop/browser-use
python3 test-proxy-simple.py

EXIT_CODE=$?

echo ""
echo "========================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Test completed successfully"
    echo "✅ Browser-use works with SnowX API proxy!"
else
    echo "❌ Test failed with exit code $EXIT_CODE"
fi
echo "========================================"
echo ""

exit $EXIT_CODE
